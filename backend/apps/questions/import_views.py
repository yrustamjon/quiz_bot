import base64
from datetime import timedelta

from django.core.files.base import ContentFile
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import owned
from apps.quizzes.models import Quiz

from .importer import MAX_UPLOAD, parse_upload, template
from .models import ImportSession, Question, QuizQuestion


class ImportView(APIView):
    def get(self, request, operation):
        if operation != "template":
            return Response(status=404)
        r = HttpResponse(
            template(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        r["Content-Disposition"] = 'attachment; filename="quiz-questions-v1.xlsx"'
        return r

    def post(self, request, operation):
        if operation == "preview":
            quiz = get_object_or_404(
                owned(Quiz.objects.all(), request.user), pk=request.data.get("quiz")
            )
            if quiz.status != "draft":
                raise ValidationError("Faqat qoralamaga import qilish mumkin.")
            upload = request.FILES.get("file")
            if not upload or upload.size > MAX_UPLOAD:
                raise ValidationError("Fayl yo‘q yoki hajmi 10 MB dan oshgan.")
            rows, errors = parse_upload(upload.read(MAX_UPLOAD + 1), upload.name)
            session = ImportSession.objects.create(
                owner=request.user,
                quiz=quiz,
                rows=rows,
                errors=errors,
                expires_at=timezone.now() + timedelta(minutes=30),
            )
            return Response(
                {"id": session.pk, "rows": rows, "errors": errors, "count": len(rows)}
            )
        if operation == "confirm":
            with transaction.atomic():
                session = get_object_or_404(
                    ImportSession.objects.select_for_update(),
                    pk=request.data.get("id"),
                    owner=request.user,
                )
                if session.confirmed:
                    return Response(
                        {"count": len(session.rows), "already_confirmed": True}
                    )
                quiz = get_object_or_404(
                    owned(Quiz.objects.select_for_update(), request.user),
                    pk=session.quiz_id,
                    status="draft",
                )
                if session.expires_at <= timezone.now() or session.errors:
                    raise ValidationError("Import muddati tugagan yoki xatolar mavjud.")
                count = quiz.question_links.count()
                if count + len(session.rows) > 500:
                    raise ValidationError("Testda 500 tadan ortiq savol bo‘lmasin.")
                for i, row in enumerate(session.rows):
                    data = {k: v for k, v in row.items() if k != "image_base64"}
                    q = Question.objects.create(
                        owner=quiz.owner, subject=quiz.subject, **data
                    )
                    if row.get("image_base64"):
                        q.image.save(
                            "image.png",
                            ContentFile(base64.b64decode(row["image_base64"])),
                        )
                    QuizQuestion.objects.create(
                        quiz=quiz, question=q, position=count + i
                    )
                session.confirmed = True
                session.save(update_fields=["confirmed"])
            return Response({"count": len(session.rows)})
        return Response(status=404)
