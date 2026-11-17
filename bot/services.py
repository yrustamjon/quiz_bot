from apps.accounts.models import StudentProfile
from apps.accounts.services import rate_limit
from apps.attempts.models import Attempt
from apps.attempts.services import student_result
from apps.quizzes.models import Quiz, QuizAccessCode
from apps.reports.services import ranking
from django.core.files.storage import default_storage
from django.db.models import Q
from django.utils import timezone


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
    c = (
        QuizAccessCode.objects.select_related("quiz")
        .filter(code=code.strip().upper(), active=True)
        .first()
    )
    if not c or (c.expires_at and c.expires_at <= timezone.now()):
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
    data = ranking(Attempt.objects.all(), student_visibility=True)
    rows = [
        {
            "rank": x["rank"],
            "name": x["name"].split()[0],
            "percentage": str(round(x["percentage"], 2)),
        }
        for x in data[:10]
    ]
    own = next(
        (
            x["rank"]
            for x in data
            if StudentProfile.objects.filter(
                pk=x["student_id"], telegram_id=tid
            ).exists()
        ),
        None,
    )
    return rows, own
