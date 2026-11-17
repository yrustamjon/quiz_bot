import logging
import random
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.accounts.services import rate_limit
from apps.quizzes.models import Quiz, QuizAccessCode

from .models import Attempt, AttemptAnswer, AttemptQuestion

rng = random.SystemRandom()


def access_quiz(student, quiz, code=None, throttle=True):
    if not student.is_active:
        raise PermissionDenied("Hisob faol emas.")
    now = timezone.now()
    if (
        quiz.status != "published"
        or (quiz.opens_at and now < quiz.opens_at)
        or (quiz.closes_at and now >= quiz.closes_at)
    ):
        raise ValidationError("Test hozir mavjud emas.")
    if quiz.access == "private":
        if throttle:
            rate_limit("code:" + str(student.pk), 10)
        if (
            not code
            or not QuizAccessCode.objects.filter(
                quiz=quiz, active=True, code=code
            ).exists()
        ):
            raise ValidationError("Kod noto‘g‘ri yoki muddati o‘tgan.")
        c = quiz.access_code
        if c.expires_at and c.expires_at <= now:
            raise ValidationError("Kod noto‘g‘ri yoki muddati o‘tgan.")


def start(student, quiz, code=None):
    # Failed access validation must not roll back its rate-limit accounting.
    if quiz.access == "private":
        rate_limit("code:" + str(student.pk), 10)
    return _start(student, quiz, code)


@transaction.atomic
def _start(student, quiz, code=None):
    quiz = Quiz.objects.select_for_update().get(pk=quiz.pk)
    access_quiz(student, quiz, code, throttle=False)
    active = (
        Attempt.objects.select_related("student", "quiz")
        .filter(student=student, quiz=quiz, status="in_progress")
        .first()
    )
    if active:
        reconcile_one(active)
        if active.status == "in_progress":
            return active
    count = Attempt.objects.filter(student=student, quiz=quiz).count()
    if count >= quiz.max_attempts:
        if active is not None:
            return active
        raise ValidationError("Urinishlar tugagan.")
    questions = [x.question for x in quiz.question_links.select_related("question")]
    if quiz.shuffle_questions:
        rng.shuffle(questions)
    questions = questions[: quiz.question_count]
    if len(questions) != quiz.question_count:
        raise ValidationError("Savollar yetarli emas.")
    now = timezone.now()
    deadline = now + timedelta(minutes=quiz.duration_minutes)
    if quiz.closes_at:
        deadline = min(deadline, quiz.closes_at)
    a = Attempt.objects.create(
        student=student,
        quiz=quiz,
        number=count + 1,
        navigation=quiz.navigation,
        started_at=now,
        deadline=deadline,
    )
    for i, q in enumerate(questions):
        mapping = list(range(4))
        if quiz.shuffle_options:
            rng.shuffle(mapping)
        AttemptQuestion.objects.create(
            attempt=a,
            position=i,
            text=q.text,
            options=[q.options[j] for j in mapping],
            correct_option=mapping.index(q.correct_option),
            points=q.points,
            image_name=q.image.name or "",
        )
    return a


def check_owner(a, telegram_id):
    if a.student.telegram_id != telegram_id or not a.student.is_active:
        raise PermissionDenied("Urinishga ruxsat yo‘q.")


def reconcile_one(a):
    if a.status == "in_progress" and timezone.now() >= a.deadline:
        _finalize(a, "timed_out")
    return a


def _finalize(a, status):
    if a.status != "in_progress":
        return a
    now = timezone.now()
    a.status = status
    a.finished_at = min(now, a.deadline)
    a.correct = a.incorrect = a.unanswered = 0
    a.earned = Decimal(0)
    a.maximum = Decimal(0)
    for q in a.questions.select_related("answer"):
        a.maximum += q.points
        if not hasattr(q, "answer"):
            a.unanswered += 1
        elif q.answer.option == q.correct_option:
            a.correct += 1
            a.earned += q.points
        else:
            a.incorrect += 1
    a.percentage = (
        (a.earned / a.maximum * 100).quantize(
            Decimal(".000001"), rounding=ROUND_HALF_UP
        )
        if a.maximum
        else Decimal(0)
    )
    a.elapsed_seconds = max(0, int((a.finished_at - a.started_at).total_seconds()))
    a.revision += 1
    a.save()
    logging.getLogger(__name__).info(
        "Attempt finalized attempt=%s status=%s", a.pk, a.status
    )
    return a


@transaction.atomic
def answer(attempt_id, telegram_id, position, option, revision):
    a = (
        Attempt.objects.select_for_update()
        .select_related("student", "quiz")
        .get(pk=attempt_id)
    )
    check_owner(a, telegram_id)
    reconcile_one(a)
    if a.status != "in_progress":
        return a, False
    if (
        type(option) != int
        or option not in range(4)
        or position != a.cursor
        or revision != a.revision
    ):
        raise ValidationError("Tugma eskirgan yoki javob noto‘g‘ri.")
    q = a.questions.get(position=position)
    if (
        a.navigation == "sequential"
        and AttemptAnswer.objects.filter(question=q).exists()
    ):
        raise ValidationError("Javob saqlangan.")
    AttemptAnswer.objects.update_or_create(question=q, defaults={"option": option})
    if a.navigation == "sequential":
        a.cursor += 1
    a.revision += 1
    a.save(update_fields=["cursor", "revision"])
    return a, True


@transaction.atomic
def navigate(attempt_id, telegram_id, position, revision):
    a = (
        Attempt.objects.select_for_update()
        .select_related("student", "quiz")
        .get(pk=attempt_id)
    )
    check_owner(a, telegram_id)
    reconcile_one(a)
    if a.status != "in_progress":
        return a
    if (
        a.navigation != "free"
        or revision != a.revision
        or type(position) != int
        or not 0 <= position < a.questions.count()
    ):
        raise ValidationError("O‘tishga ruxsat yo‘q.")
    a.cursor = position
    a.revision += 1
    a.save(update_fields=["cursor", "revision"])
    return a


@transaction.atomic
def preview_finish(attempt_id, telegram_id):
    a = (
        Attempt.objects.select_for_update()
        .select_related("student", "quiz")
        .get(pk=attempt_id)
    )
    check_owner(a, telegram_id)
    reconcile_one(a)
    from django.db.models import Count

    counts = a.questions.aggregate(total=Count("id"), answered=Count("answer"))
    return a, counts["total"], counts["answered"]


@transaction.atomic
def finish(attempt_id, telegram_id, confirmed=False):
    a = (
        Attempt.objects.select_for_update()
        .select_related("student", "quiz")
        .get(pk=attempt_id)
    )
    check_owner(a, telegram_id)
    reconcile_one(a)
    if not confirmed and a.status == "in_progress":
        raise ValidationError("Yakunlashni tasdiqlang.")
    return _finalize(a, "completed")


@transaction.atomic
def resume(telegram_id):
    a = (
        Attempt.objects.select_for_update()
        .select_related("student", "quiz")
        .filter(student__telegram_id=telegram_id, status="in_progress")
        .order_by("-started_at")
        .first()
    )
    if a:
        check_owner(a, telegram_id)
        reconcile_one(a)
    return a


def released(quiz):
    return (
        quiz.result_release_mode == "instant"
        or (quiz.result_release_mode == "manual" and quiz.results_released)
        or (
            quiz.result_release_mode == "after_close"
            and (
                quiz.status in ["closed", "archived"]
                or (quiz.closes_at and timezone.now() >= quiz.closes_at)
            )
        )
    )


def student_result(a, telegram_id):
    check_owner(a, telegram_id)
    if a.status == "in_progress" or not released(a.quiz):
        return {"released": False}
    data = {"released": True, "title": a.quiz.title, "unanswered": a.unanswered}
    for flag, fields in [
        ("show_score", ["earned", "maximum"]),
        ("show_percentage", ["percentage"]),
        ("show_correct_count", ["correct"]),
        ("show_incorrect_count", ["incorrect"]),
    ]:
        if getattr(a.quiz, flag):
            data.update({k: getattr(a, k) for k in fields})
    if a.quiz.show_ranking:
        from apps.reports.services import ranking

        board = ranking(Attempt.objects.filter(quiz=a.quiz), student_visibility=True)
        data["rank"] = next(
            (r["rank"] for r in board if r["student_id"] == a.student_id), None
        )
    if a.quiz.show_detailed_answers:
        data["questions"] = [
            {
                "text": q.text,
                "options": q.options,
                "correct": q.correct_option,
                "selected": q.answer.option if hasattr(q, "answer") else None,
            }
            for q in a.questions.select_related("answer")
        ]
    return data
