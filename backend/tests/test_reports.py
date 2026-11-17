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
