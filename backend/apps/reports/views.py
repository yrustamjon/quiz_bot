from datetime import timedelta

from django.db.models import Avg, Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from kombu.exceptions import OperationalError as BrokerError
from redis.exceptions import RedisError
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import owned
from apps.attempts.models import Attempt
from apps.quizzes.models import Quiz


class DashboardView(APIView):
    def get(self, request):
        try:
            days = int(request.query_params.get("days", "30"))
        except ValueError:
            raise ValidationError("Davr noto‘g‘ri.")
        if days not in [1, 7, 30, 90]:
            raise ValidationError("Davr noto‘g‘ri.")
        quizzes = owned(Quiz.objects.all(), request.user)
        attempts = Attempt.objects.filter(
            quiz__in=quizzes, started_at__gte=timezone.now() - timedelta(days=days)
        )
        final = attempts.exclude(status="in_progress")
        return Response(
            {
                "quizzes": quizzes.count(),
                "published": quizzes.filter(status="published").count(),
                "participants": attempts.values("student").distinct().count(),
                "completed": final.count(),
                "average": final.aggregate(value=Avg("percentage"))["value"] or 0,
                "activity": list(
                    attempts.annotate(date=TruncDate("started_at"))
                    .values("date")
                    .annotate(attempts=Count("id"))
                    .order_by("date")
                ),
                "recent_quizzes": list(
                    quizzes.order_by("-created_at").values(
                        "id", "title", "subject", "status"
                    )[:5]
                ),
            }
        )


from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from .serializers import ResultSerializer
from .services import export_results, ranking


class ResultViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ResultSerializer

    def get_queryset(self):
        qs = owned(
            Attempt.objects.select_related("student", "quiz"),
            self.request.user,
            "quiz__owner",
        )
        for field in ["quiz", "student", "status"]:
            value = self.request.query_params.get(field)
            if value:
                if field in ["quiz", "student"] and not value.isdigit():
                    raise ValidationError("Filtr noto‘g‘ri.")
                qs = qs.filter(**{field: value})
        return qs.filter(
            student__full_name__icontains=self.request.query_params.get("search", "")
        ).order_by("-started_at")


class RankingView(APIView):
    def get(self, request):
        qs = ResultViewSet()
        qs.request = request
        data = ranking(qs.get_queryset())
        paginator = PageNumberPagination()
        rows = paginator.paginate_queryset(data, request)
        return paginator.get_paginated_response(rows)


class ExportView(APIView):
    def post(self, request):
        view = ResultViewSet()
        view.request = request
        qs = view.get_queryset()
        if request.data.get("quiz"):
            from django.shortcuts import get_object_or_404

            quiz = get_object_or_404(
                owned(Quiz.objects.all(), request.user), pk=request.data["quiz"]
            )
            qs = qs.filter(quiz=quiz)
        if qs.count() > 5000 or request.data.get("background"):
            filters = {
                k: request.query_params[k]
                for k in ["quiz", "student", "status", "search"]
                if request.query_params.get(k)
            }
            if request.data.get("quiz"):
                filters["quiz"] = request.data["quiz"]
            job = ReportExport.objects.create(owner=request.user, filters=filters)
            try:
                generate_export.delay(str(job.pk))
            except (BrokerError, RedisError, OSError):
                job.status = "failed"
                job.error = "Navbat xizmati mavjud emas."
                job.save(update_fields=["status", "error"])
                return Response({"id": job.pk, "detail": job.error}, status=503)
            return Response({"id": job.pk, "status": job.status}, status=202)
        response = HttpResponse(
            export_results(qs),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = 'attachment; filename="quiz-results.xlsx"'
        response["Cache-Control"] = "private, no-store"
        return response


from django.http import FileResponse
from rest_framework import serializers
from rest_framework.decorators import action

from .models import ReportExport
from .tasks import generate_export


class ExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportExport
        fields = ["id", "status", "error", "created_at", "finished_at"]


class ExportJobViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ExportSerializer

    def get_queryset(self):
        return ReportExport.objects.filter(owner=self.request.user).order_by(
            "-created_at"
        )

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        job = self.get_object()
        if job.status != "ready" or not job.file:
            raise ValidationError("Hisobot tayyor emas.")
        response = FileResponse(
            job.file.open("rb"), as_attachment=True, filename="quiz-results.xlsx"
        )
        response["Cache-Control"] = "private, no-store"
        return response
