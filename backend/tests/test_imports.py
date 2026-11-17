import io
import zipfile

import pytest
from apps.questions.importer import parse_upload, template
from apps.quizzes.models import Quiz
from django.core.files.uploadedfile import SimpleUploadedFile
from openpyxl import load_workbook
from openpyxl.drawing.image import Image as XLImage
from PIL import Image
from rest_framework.exceptions import ValidationError

pytestmark = pytest.mark.django_db


def workbook(edit=None):
    w = load_workbook(io.BytesIO(template()))
    if edit:
        edit(w)
    out = io.BytesIO()
    w.save(out)
    return out.getvalue()


def test_template_and_formula():
    rows, errors = parse_upload(template(), "q.xlsx")
    assert len(rows) == 1 and not errors
    rows, errors = parse_upload(
        workbook(lambda w: setattr(w["Questions"]["A2"], "value", "=1+1")), "q.xlsx"
    )
    assert errors and not rows


def test_zip_path_and_bomb():
    for path in ["../evil.png", "/evil.png", "images/../../evil.png"]:
        data = io.BytesIO()
        with zipfile.ZipFile(data, "w") as z:
            z.writestr(path, b"bad")
        with pytest.raises(ValidationError):
            parse_upload(data.getvalue(), "x.zip")
    with pytest.raises(ValidationError):
        parse_upload(b"x" * (10 * 1024 * 1024 + 1), "x.xlsx")


def test_embedded_and_zip_images():
    png = io.BytesIO()
    Image.new("RGB", (20, 20)).save(png, format="PNG")
    png.seek(0)
    raw = png.getvalue()
    data = workbook(lambda w: w["Questions"].add_image(XLImage(png), "H2"))
    rows, errors = parse_upload(data, "q.xlsx")
    assert not errors and rows[0]["image_base64"]
    data = workbook(lambda w: setattr(w["Questions"]["H2"], "value", "images/q.png"))
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        z.writestr("questions.xlsx", data)
        z.writestr("images/q.png", raw)
    rows, errors = parse_upload(out.getvalue(), "q.zip")
    assert not errors and rows[0]["image_base64"]


def test_confirm_idempotent_and_scoped(client, teacher, other):
    q = Quiz.objects.create(owner=teacher, title="Import", subject="Fan")
    r = client.post(
        "/api/questions/import/preview/",
        {"quiz": q.pk, "file": SimpleUploadedFile("q.xlsx", template())},
        format="multipart",
    )
    assert r.status_code == 200
    data = {"id": str(r.data["id"])}
    assert client.post("/api/questions/import/confirm/", data).status_code == 200
    assert client.post("/api/questions/import/confirm/", data).status_code == 200
    assert q.question_links.count() == 1
    q.owner = other
    q.save()
    assert (
        client.post(
            "/api/questions/import/preview/",
            {"quiz": q.pk, "file": SimpleUploadedFile("q.xlsx", template())},
            format="multipart",
        ).status_code
        == 404
    )
