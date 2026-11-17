import re

from apps.accounts.models import StudentProfile
from apps.accounts.services import rate_limit
from apps.attempts.models import Attempt
from apps.attempts.scoring import percent_display
from apps.attempts.services import access_quiz, released, student_result
from apps.quizzes.models import Quiz, QuizAccessCode
from apps.reports.services import ranking
from django.core.files.storage import default_storage
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError


def student(tid):
    return StudentProfile.objects.filter(telegram_id=tid, is_active=True).first()


def public_quizzes(page=0):
    now = timezone.now()
    return list(
        Quiz.objects.filter(status="published", access="public")
        .filter(Q(opens_at__isnull=True) | Q(opens_at__lte=now))
        .filter(Q(closes_at__isnull=True) | Q(closes_at__gt=now))
        .order_by("id")[page * 8 : page * 8 + 9]
    )


def by_code(tid, code):
    rate_limit("lookup-code:" + str(tid), 10)
    normalized = code.strip().upper()
    if not re.fullmatch(r"[A-F0-9]{10}", normalized):
        return None
    c = (
        QuizAccessCode.objects.select_related("quiz")
        .filter(code=code.strip().upper(), active=True)
        .first()
    )
    if not c or (c.expires_at and c.expires_at <= timezone.now()):
        return None
    identity = student(tid)
    if not identity:
        return None
    try:
        access_quiz(identity, c.quiz, normalized, throttle=False)
    except (ValidationError, PermissionDenied):
        return None
    attempts = Attempt.objects.filter(student=identity, quiz=c.quiz)
    if (
        attempts.count() >= c.quiz.max_attempts
        and not attempts.filter(
            status="in_progress", deadline__gt=timezone.now()
        ).exists()
    ):
        return None
    return c.quiz


def get_question(a):
    return a.questions.filter(position=a.cursor).first()


def image_data(name):
    if not name:
        return None
    try:
        with default_storage.open(name, "rb") as f:
            return f.read()
    except OSError:
        return None


def own_results(tid):
    return [
        student_result(a, tid)
        for a in Attempt.objects.filter(student__telegram_id=tid)
        .exclude(status="in_progress")
        .select_related("quiz", "student")
        .order_by("-finished_at")[:10]
    ]


def student_ranking(tid):
    data = ranking(
        Attempt.objects.filter(quiz__access="public", quiz__show_percentage=True),
        student_visibility=True,
    )
    rows = [
        {
            "rank": x["rank"],
            "name": x["name"].split()[0],
            "percentage": percent_display(x["percentage"]),
        }
        for x in data[:10]
    ]
    identity = (
        StudentProfile.objects.filter(telegram_id=tid)
        .values_list("id", flat=True)
        .first()
    )
    own = next((x["rank"] for x in data if x["student_id"] == identity), None)
    return rows, own


def quiz_ranking(tid, quiz_id):
    quiz = Quiz.objects.filter(pk=quiz_id).first()
    if (
        not quiz
        or not quiz.show_ranking
        or not released(quiz)
        or not Attempt.objects.filter(quiz=quiz, student__telegram_id=tid)
        .exclude(status="in_progress")
        .exists()
    ):
        return None
    board = ranking(Attempt.objects.filter(quiz=quiz))
    sid = (
        StudentProfile.objects.filter(telegram_id=tid)
        .values_list("id", flat=True)
        .first()
    )
    own = next((r["rank"] for r in board if r["student_id"] == sid), None)
    rows = [
        {
            "rank": r["rank"],
            "name": r["name"].split()[0],
            "percentage": percent_display(r["percentage"])
            if quiz.show_percentage
            else None,
        }
        for r in board[:10]
    ]
    return rows, own
