import io

import pytest
from apps.attempts.models import Attempt
from apps.quizzes.models import Quiz
from apps.reports.services import export_results, safe_cell
from openpyxl import load_workbook

pytestmark = pytest.mark.django_db


def test_scoped_exports_and_rankings(client, other):
    quiz = Quiz.objects.create(owner=other, title="Private", subject="Fan")
    assert client.post("/api/reports/export/", {"quiz": quiz.pk}).status_code == 404
    assert client.get("/api/results/?quiz=" + str(quiz.pk)).data["count"] == 0
    assert client.get("/api/rankings/").data["count"] == 0


def test_real_xlsx_and_injection():
    assert safe_cell('=HYPERLINK("evil")').startswith("'")
    assert safe_cell(" +SUM(1)").startswith("'")
    data = export_results(Attempt.objects.none())
    w = load_workbook(io.BytesIO(data))
    assert w.active["A1"].value == "O‘quvchi"


def test_job_download_owner(client, teacher, other):
    from apps.reports.models import ReportExport
    from apps.reports.tasks import generate_export

    job = ReportExport.objects.create(owner=other)
    assert client.get(f"/api/reports/exports/{job.pk}/").status_code == 404
    assert client.get(f"/api/reports/exports/{job.pk}/download/").status_code == 404
    job.owner = teacher
    job.save()
    generate_export(str(job.pk))
    job.refresh_from_db()
    assert job.status == "ready"
    assert client.get(f"/api/reports/exports/{job.pk}/download/").status_code == 200
    generate_export(str(job.pk))
    job.refresh_from_db()
    job.file.delete()


def test_student_summary_and_details_stay_scoped(client, teacher, other):
    from datetime import timedelta

    from apps.accounts.models import StudentProfile
    from django.utils import timezone

    s = StudentProfile.objects.create(telegram_id=9182, full_name="Shared Student")
    for owner, score in [(teacher, 50), (other, 100)]:
        quiz = Quiz.objects.create(
            owner=owner, title="Private " + owner.username, subject="Fan"
        )
        Attempt.objects.create(
            quiz=quiz,
            student=s,
            number=1,
            status="completed",
            navigation="sequential",
            started_at=timezone.now(),
            deadline=timezone.now() + timedelta(minutes=10),
            percentage=score,
        )
    data = client.get(f"/api/students/{s.pk}/").data
    assert data["participation_count"] == 1 and float(data["average_percentage"]) == 50
    assert (
        len(data["attempts"]) == 1
        and data["attempts"][0]["quiz_title"] == "Private teacher"
    )


@pytest.mark.parametrize("kind", ["leaderboard", "students", "teachers"])
def test_report_types_and_scope(client, kind):
    response = client.post("/api/reports/export/", {"report_type": kind}, format="json")
    if kind == "teachers":
        assert response.status_code == 403
    else:
        assert response.status_code == 200
        assert load_workbook(io.BytesIO(response.content)).active.max_row == 1
    assert client.get("/api/reports/summary/?type=" + kind).status_code == (
        403 if kind == "teachers" else 200
    )


def test_dashboard_cache_scope_and_redis_failure(client, teacher, other):
    from unittest.mock import patch

    from redis.exceptions import RedisError
    from rest_framework.test import APIClient

    Quiz.objects.create(owner=teacher, title="Mine", subject="Fan")
    Quiz.objects.create(owner=other, title="Other 1", subject="Fan")
    Quiz.objects.create(owner=other, title="Other 2", subject="Fan")
    assert client.get("/api/dashboard/summary/").data["quizzes"] == 1
    other_client = APIClient()
    other_client.force_login(other)
    assert other_client.get("/api/dashboard/summary/").data["quizzes"] == 2
    with patch("apps.reports.views.cache.get", side_effect=RedisError("unavailable")):
        assert client.get("/api/dashboard/summary/").data["quizzes"] == 1


def test_rankings_best_attempt_average_and_deterministic_ties(teacher):
    from datetime import timedelta
    from decimal import Decimal

    from apps.accounts.models import StudentProfile
    from apps.reports.services import ranking
    from django.utils import timezone

    students = [
        StudentProfile.objects.create(telegram_id=9000 + i, full_name=f"Rank {i}")
        for i in range(3)
    ]
    quizzes = [
        Quiz.objects.create(
            owner=teacher, title=f"Rank quiz {i}", subject="Fan", status="published"
        )
        for i in range(2)
    ]
    now = timezone.now()

    def add(student, quiz, score, seconds, number=1, status="completed"):
        return Attempt.objects.create(
            student=student,
            quiz=quiz,
            number=number,
            status=status,
            navigation="free",
            started_at=now,
            deadline=now + timedelta(minutes=30),
            finished_at=now + timedelta(seconds=seconds),
            percentage=score,
            elapsed_seconds=seconds,
        )

    add(students[0], quizzes[0], 80, 20)
    add(students[0], quizzes[0], 100, 15, number=2)
    add(students[0], quizzes[1], 60, 15)
    add(students[1], quizzes[0], 80, 10)
    add(students[1], quizzes[1], 80, 20)
    add(students[2], quizzes[0], 80, 20)
    add(students[2], quizzes[1], 80, 20)
    add(students[2], quizzes[0], 100, 1, number=2, status="in_progress")
    rows = ranking(Attempt.objects.all())
    assert [x["student_id"] for x in rows] == [s.pk for s in students]
    assert [x["percentage"] for x in rows] == [Decimal(80)] * 3
    assert [x["quizzes"] for x in rows] == [2, 2, 2]
    assert [x["rank"] for x in rows] == [1, 2, 3]
    per_quiz = ranking(Attempt.objects.filter(quiz=quizzes[0]))
    assert per_quiz[0]["percentage"] == 100
    quizzes[1].result_release_mode = "manual"
    quizzes[1].save()
    visible = ranking(Attempt.objects.all(), student_visibility=True)
    assert all(row["quizzes"] == 1 for row in visible)


@pytest.mark.parametrize("kind", ["results", "students", "leaderboard"])
def test_real_scoped_workbook_escapes_formula_payloads(client, teacher, kind):
    from datetime import timedelta

    from apps.accounts.models import StudentProfile
    from django.utils import timezone

    teacher.full_name = "+SUM(1,2)"
    teacher.save()
    student = StudentProfile.objects.create(
        telegram_id=72836, full_name='=HYPERLINK("https://example.test","x")'
    )
    quiz = Quiz.objects.create(
        owner=teacher, title="@SUM(1,2)", subject="Fan", status="published"
    )
    now = timezone.now()
    Attempt.objects.create(
        quiz=quiz,
        student=student,
        number=1,
        status="completed",
        navigation="sequential",
        started_at=now,
        deadline=now + timedelta(minutes=10),
        finished_at=now + timedelta(minutes=1),
        earned=1,
        maximum=2,
        percentage=50,
    )
    response = client.post(
        f"/api/reports/export/?quiz={quiz.pk}", {"report_type": kind}, format="json"
    )
    assert response.status_code == 200
    workbook = load_workbook(io.BytesIO(response.content))
    sheet = workbook.active
    assert sheet.max_row == 2
    row = list(sheet[2])
    assert all(cell.data_type != "f" for cell in row)
    student_cell = next(
        cell
        for cell in row
        if isinstance(cell.value, str) and "HYPERLINK" in cell.value
    )
    assert student_cell.value.startswith("'=")
    if kind == "results":
        assert row[1].value == "'@SUM(1,2)"
        assert row[2].value == "'+SUM(1,2)"
