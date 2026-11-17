"""Authorized staging and transactional confirmation, shared independently of HTTP."""

import base64
from datetime import timedelta

from django.core.files.base import ContentFile
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.accounts.permissions import owned
from apps.quizzes.models import Quiz

from .importer import MAX_UPLOAD, parse_upload
from .models import ImportSession, Question, QuizQuestion


def preview_import(owner, quiz_id, upload):
    quiz = get_object_or_404(owned(Quiz.objects.all(), owner), pk=quiz_id)
    if quiz.status != "draft":
        raise ValidationError("Faqat qoralamaga import qilish mumkin.")
    if not upload or upload.size > MAX_UPLOAD:
        raise ValidationError("Fayl yo‘q yoki hajmi 10 MB dan oshgan.")
    rows, errors = parse_upload(upload.read(MAX_UPLOAD + 1), upload.name)
    session = ImportSession.objects.create(
        owner=owner,
        quiz=quiz,
        rows=rows,
        errors=errors,
        expires_at=timezone.now() + timedelta(minutes=30),
    )
    return {
        "id": session.pk,
        "rows": rows,
        "errors": errors,
        "count": len(rows),
        "image_count": sum(bool(row.get("image_base64")) for row in rows),
        "invalid_rows": len({error["row"] for error in errors if error["row"] >= 2}),
        "total_rows": len(
            {row["source_row"] for row in rows}
            | {error["row"] for error in errors if error["row"] >= 2}
        ),
    }


@transaction.atomic
def confirm_import(owner, session_id):
    session = get_object_or_404(
        ImportSession.objects.select_for_update(), pk=session_id, owner=owner
    )
    if session.confirmed:
        return {"count": len(session.rows), "already_confirmed": True}
    quiz = get_object_or_404(
        owned(Quiz.objects.select_for_update(), owner),
        pk=session.quiz_id,
        status="draft",
    )
    if session.expires_at <= timezone.now() or session.errors:
        raise ValidationError("Import muddati tugagan yoki xatolar mavjud.")
    count = quiz.question_links.count()
    if count + len(session.rows) > 500:
        raise ValidationError("Testda 500 tadan ortiq savol bo‘lmasin.")
    for i, row in enumerate(session.rows):
        data = {
            k: v
            for k, v in row.items()
            if k in ["text", "options", "correct_option", "points"]
        }
        question = Question.objects.create(
            owner=quiz.owner, subject=quiz.subject, **data
        )
        if row.get("image_base64"):
            question.image.save(
                "image.png", ContentFile(base64.b64decode(row["image_base64"]))
            )
        QuizQuestion.objects.create(quiz=quiz, question=question, position=count + i)
    session.confirmed = True
    session.save(update_fields=["confirmed"])
    return {"count": len(session.rows)}
