import logging
import secrets

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.questions.models import QuizQuestion

from .models import Quiz, QuizAccessCode


@transaction.atomic
def regenerate_code(quiz):
    code = secrets.token_hex(5).upper()
    QuizAccessCode.objects.update_or_create(
        quiz=quiz, defaults={"code": code, "active": True, "expires_at": quiz.closes_at}
    )
    return code


@transaction.atomic
def transition(quiz, target):
    quiz = Quiz.objects.select_for_update().get(pk=quiz.pk)
    allowed = {
        "draft": ["published", "archived"],
        "published": ["closed"],
        "closed": ["archived"],
        "archived": [],
    }
    if target not in allowed[quiz.status]:
        raise ValidationError("Test holatini bunday o‘zgartirib bo‘lmaydi.")
    if target == "published":
        quiz.full_clean()
        questions = [
            link.question for link in quiz.question_links.select_related("question")
        ]
        if len(questions) < quiz.question_count:
            raise ValidationError("Yetarli savol mavjud emas.")
        if quiz.closes_at and quiz.closes_at <= timezone.now():
            raise ValidationError("Yopilish vaqti o‘tgan.")
        if quiz.opens_at and quiz.closes_at and quiz.opens_at >= quiz.closes_at:
            raise ValidationError("Vaqt oralig‘i noto‘g‘ri.")
        for q in questions:
            if (
                not isinstance(q.options, list)
                or not q.text.strip()
                or len(q.options) != 4
                or not all(isinstance(x, str) and x.strip() for x in q.options)
                or q.correct_option not in range(4)
                or q.points <= 0
            ):
                raise ValidationError("Savolni tekshiring.")
        if quiz.access == "private":
            regenerate_code(quiz)
    logging.getLogger(__name__).info(
        "Quiz transition quiz=%s status=%s", quiz.pk, target
    )
    quiz.status = target
    quiz.save(update_fields=["status", "updated_at"])
    return quiz


@transaction.atomic
def duplicate(quiz, owner):
    links = list(quiz.question_links.select_related("question"))
    quiz.pk = None
    quiz.owner = owner
    quiz.status = "draft"
    quiz.title += " (nusxa)"
    quiz.results_released = False
    quiz.save()
    for link in links:
        question = link.question
        question.pk = None
        question.owner = owner
        question.save()
        QuizQuestion.objects.create(
            quiz=quiz, question=question, position=link.position
        )
    return quiz
