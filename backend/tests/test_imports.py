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


@pytest.mark.parametrize("value", ["E", None, "=SUM(A1:A2)"])
def test_invalid_answer_cells(value):
    rows, errors = parse_upload(
        workbook(lambda w: setattr(w["Questions"]["F2"], "value", value)), "q.xlsx"
    )
    assert errors and not rows


def test_symlink_duplicate_and_nested_archives():
    import stat

    malicious = zipfile.ZipInfo("link.png")
    malicious.create_system = 3
    malicious.external_attr = (stat.S_IFLNK | 0o777) << 16
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as z:
        z.writestr(malicious, "/etc/passwd")
    with pytest.raises(ValidationError):
        parse_upload(data.getvalue(), "x.zip")
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as z:
        z.writestr("nested.zip", b"bad")
    with pytest.raises(ValidationError):
        parse_upload(data.getvalue(), "x.zip")


def test_http_request_size_limit(client):
    response = client.generic(
        "POST",
        "/api/questions/import/preview/",
        b"{}",
        content_type="application/json",
        CONTENT_LENGTH=str(13 * 1024 * 1024),
    )
    assert response.status_code == 413


def test_manual_raster_upload_and_remove(client):
    image = io.BytesIO()
    Image.new("RGB", (8, 8)).save(image, format="PNG")
    response = client.post(
        "/api/questions/",
        {
            "text": "Image question",
            "options": ["a", "b", "c", "d"],
            "correct_option": 0,
            "points": "1",
        },
        format="json",
    )
    assert response.status_code == 201
    pk = response.data["id"]
    response = client.patch(
        f"/api/questions/{pk}/",
        {
            "image": SimpleUploadedFile(
                "anything.png", image.getvalue(), content_type="image/png"
            )
        },
        format="multipart",
    )
    assert response.status_code == 200 and response.data["image_url"]
    assert client.get(f"/api/questions/{pk}/image/").status_code == 200
    assert (
        client.patch(
            f"/api/questions/{pk}/", {"remove_image": True}, format="json"
        ).status_code
        == 200
    )
    assert client.get(f"/api/questions/{pk}/image/").status_code == 404
    assert (
        client.patch(
            f"/api/questions/{pk}/",
            {
                "image": SimpleUploadedFile(
                    "evil.png", b"not a PNG", content_type="image/png"
                )
            },
            format="multipart",
        ).status_code
        == 400
    )


def test_numeric_options_and_utf16_relationship_entities():
    def set_options(w):
        for index, value in enumerate([1, 2, 3, 4], 2):
            w["Questions"].cell(2, index, value)

    rows, errors = parse_upload(workbook(set_options), "q.xlsx")
    assert not errors and rows[0]["options"] == ["1", "2", "3", "4"]
    data = io.BytesIO()
    with (
        zipfile.ZipFile(io.BytesIO(template())) as original,
        zipfile.ZipFile(data, "w") as z,
    ):
        for entry in original.infolist():
            z.writestr(entry, original.read(entry))
        z.writestr(
            "xl/test.rels",
            '<?xml version="1.0" encoding="UTF-16"?><!DOCTYPE root [<!ENTITY evil "data">]><root>&evil;</root>'.encode(
                "utf-16"
            ),
        )
    with pytest.raises(ValidationError):
        parse_upload(data.getvalue(), "q.xlsx")


def test_unsupported_embedded_image_has_row_error():
    png = io.BytesIO()
    Image.new("RGB", (10, 10)).save(png, format="PNG")
    png.seek(0)
    book = workbook(lambda w: w["Questions"].add_image(XLImage(png), "H2"))
    out = io.BytesIO()
    with (
        zipfile.ZipFile(io.BytesIO(book)) as original,
        zipfile.ZipFile(out, "w") as changed,
    ):
        for entry in original.infolist():
            content = original.read(entry)
            if entry.filename.endswith(".rels"):
                content = content.replace(b"image1.png", b"image1.emf")
            filename = entry.filename.replace("image1.png", "image1.emf")
            changed.writestr(filename, content)
    rows, errors = parse_upload(out.getvalue(), "q.xlsx")
    assert not rows and errors[0]["row"] == 2


def test_multipart_question_creation_validates_image_before_saving(client):
    import json

    from apps.questions.models import Question

    before = Question.objects.count()
    fields = {
        "text": "Atomic raster question",
        "options": json.dumps(["a", "b", "c", "d"]),
        "correct_option": "0",
        "points": "1.25",
    }
    bad = client.post(
        "/api/questions/",
        {
            **fields,
            "image": SimpleUploadedFile(
                "bad.png", b"not-image", content_type="image/png"
            ),
        },
        format="multipart",
    )
    assert bad.status_code == 400 and Question.objects.count() == before
    png = io.BytesIO()
    Image.new("RGB", (8, 8)).save(png, format="PNG")
    good = client.post(
        "/api/questions/",
        {
            **fields,
            "image": SimpleUploadedFile(
                "good.png", png.getvalue(), content_type="image/png"
            ),
        },
        format="multipart",
    )
    assert good.status_code == 201 and good.data["image_url"]
    assert good.data["options"] == ["a", "b", "c", "d"]
    assert Question.objects.count() == before + 1


def test_private_question_image_denies_other_teacher_and_anonymous(
    client, teacher, other
):
    from apps.questions.models import Question
    from django.core.files.base import ContentFile
    from rest_framework.test import APIClient

    question = Question.objects.create(
        owner=other,
        text="Private image",
        options=["a", "b", "c", "d"],
        correct_option=0,
    )
    png = io.BytesIO()
    Image.new("RGB", (8, 8)).save(png, format="PNG")
    question.image.save("private.png", ContentFile(png.getvalue()), save=True)
    assert client.get(f"/api/questions/{question.pk}/image/").status_code == 404
    assert APIClient().get(f"/api/questions/{question.pk}/image/").status_code == 403
