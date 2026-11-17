from django.db import transaction
from django.db.models import Count
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.accounts.permissions import owned
from apps.questions.models import Question, QuizQuestion
from apps.questions.serializers import QuestionSerializer

from .models import Quiz
from .serializers import QuizSerializer
from .services import duplicate, regenerate_code, transition


class QuizViewSet(viewsets.ModelViewSet):
    serializer_class = QuizSerializer

    def get_queryset(self):
        qs = owned(
            Quiz.objects.select_related("owner", "access_code")
            .prefetch_related("question_links")
            .annotate(participants=Count("attempts__student", distinct=True)),
            self.request.user,
        )
        for field in ["status", "subject", "access"]:
            if self.request.query_params.get(field):
                qs = qs.filter(**{field: self.request.query_params[field]})
        return qs.filter(
            title__icontains=self.request.query_params.get("search", "")
        ).order_by(
            self.request.query_params.get("ordering")
            if self.request.query_params.get("ordering")
            in ["created_at", "-created_at", "title"]
            else "-created_at"
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @transaction.atomic
    def perform_update(self, serializer):
        serializer.instance = Quiz.objects.select_for_update().get(
            pk=serializer.instance.pk
        )
        if serializer.instance.status != "draft":
            raise ValidationError("Faol testni o‘zgartirish uchun nusxa yarating.")
        serializer.save()

    @transaction.atomic
    def perform_destroy(self, obj):
        obj = Quiz.objects.select_for_update().get(pk=obj.pk)
        if obj.status != "draft" or obj.attempts.exists():
            raise ValidationError("Faqat qatnashuvchisiz qoralamani o‘chirish mumkin.")
        obj.delete()

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        return Response(
            self.get_serializer(transition(self.get_object(), "published")).data
        )

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        return Response(
            self.get_serializer(transition(self.get_object(), "closed")).data
        )

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        return Response(
            self.get_serializer(transition(self.get_object(), "archived")).data
        )

    @action(detail=True, methods=["post"])
    def duplicate(self, request, pk=None):
        return Response(
            self.get_serializer(duplicate(self.get_object(), request.user)).data,
            status=201,
        )

    @action(detail=True, methods=["get"], url_path="access-code")
    def access_code(self, request, pk=None):
        quiz = self.get_object()
        if (
            quiz.access != "private"
            or not hasattr(quiz, "access_code")
            or not quiz.access_code.active
        ):
            raise ValidationError("Faol kirish kodi mavjud emas.")
        response = Response(
            {"code": quiz.access_code.code, "expires_at": quiz.access_code.expires_at}
        )
        response["Cache-Control"] = "private, no-store"
        return response

    @action(detail=True, methods=["post"], url_path="regenerate-code")
    def code(self, request, pk=None):
        return Response({"code": regenerate_code(self.get_object())})

    @action(detail=True, methods=["post"], url_path="release-results")
    @transaction.atomic
    def release(self, request, pk=None):
        q = Quiz.objects.select_for_update().get(pk=self.get_object().pk)
        if q.status == "draft":
            raise ValidationError("Qoralama natijalarini e’lon qilib bo‘lmaydi.")
        q.results_released = True
        q.save(update_fields=["results_released"])
        return Response({"released": True})

    @action(detail=True, methods=["get", "put"])
    @transaction.atomic
    def questions(self, request, pk=None):
        quiz = self.get_object()
        if request.method == "PUT":
            quiz = Quiz.objects.select_for_update().get(pk=quiz.pk)
            if quiz.status != "draft":
                raise ValidationError("Faqat qoralamani o‘zgartirish mumkin.")
            ids = request.data.get("question_ids", [])
            if (
                not isinstance(ids, list)
                or len(ids) > 500
                or any(type(x) != int for x in ids)
                or len(set(ids)) != len(ids)
            ):
                raise ValidationError("Savollar ro‘yxati noto‘g‘ri.")
            qs = Question.objects.filter(pk__in=ids, owner=quiz.owner)
            if qs.count() != len(ids):
                raise ValidationError("Savollarga ruxsat yo‘q.")
            with transaction.atomic():
                quiz.question_links.all().delete()
                QuizQuestion.objects.bulk_create(
                    [
                        QuizQuestion(quiz=quiz, question_id=q, position=i)
                        for i, q in enumerate(ids)
                    ]
                )
        return Response(
            QuestionSerializer(
                [x.question for x in quiz.question_links.select_related("question")],
                many=True,
            ).data
        )
