import hashlib
import json
import logging
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.db.models import Avg, Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from kombu.exceptions import OperationalError as BrokerError
from redis.exceptions import RedisError
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import StudentProfile, User
from apps.accounts.permissions import is_admin, owned
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
        attempts = Attempt.objects.filter(quiz__in=quizzes)
        if request.query_params.get("start") or request.query_params.get("end"):
            attempts = filter_results(attempts, request.query_params)
        else:
            attempts = attempts.filter(
                started_at__gte=timezone.localtime(timezone.now()).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                if days == 1
                else timezone.now() - timedelta(days=days)
            )
        key = (
            "dashboard:"
            + hashlib.sha256(
                json.dumps(
                    [
                        [
                            str(settings.DATABASES["default"].get(field, ""))
                            for field in ["HOST", "PORT", "NAME"]
                        ],
                        request.user.pk,
                        request.user.role,
                        is_admin(request.user),
                        dict(request.query_params),
                    ],
                    sort_keys=True,
                ).encode()
            ).hexdigest()
        )
        try:
            cached = cache.get(key)
        except (RedisError, OSError):
            cached = None
        if cached is not None:
            return Response(cached)
        final = attempts.exclude(status="in_progress")
        response = Response(
            {
                "teachers": User.objects.filter(role="TEACHER").count()
                if is_admin(request.user)
                else None,
                "active_teachers": User.objects.filter(
                    role="TEACHER", is_active=True
                ).count()
                if is_admin(request.user)
                else None,
                "students": StudentProfile.objects.count()
                if is_admin(request.user)
                else None,
                "attempts": attempts.count(),
                "most_active": list(
                    attempts.values("quiz_id", "quiz__title")
                    .annotate(count=Count("id"))
                    .order_by("-count", "quiz_id")[:5]
                ),
                "status_distribution": list(
                    quizzes.values("status").annotate(count=Count("id"))
                ),
                "recent_attempts": ResultSerializer(
                    attempts.select_related("student", "quiz").order_by("-started_at")[
                        :5
                    ],
                    many=True,
                ).data,
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
        try:
            cache.set(key, response.data, timeout=20)
        except (RedisError, OSError):
            logging.getLogger(__name__).warning(
                "Dashboard cache unavailable; SQL fallback used"
            )
        return response


from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from .serializers import ResultSerializer
from .services import export_report, filter_results, ranking, report_data


class ResultViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ResultSerializer

    def get_queryset(self):
        qs = owned(
            Attempt.objects.select_related("student", "quiz"),
            self.request.user,
            "quiz__owner",
        )
        if self.request.query_params.get("teacher") and not is_admin(self.request.user):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("O‘qituvchi filtri faqat administrator uchun.")
        return filter_results(qs, self.request.query_params).order_by("-started_at")

    def retrieve(self, request, *args, **kwargs):
        attempt = self.get_object()
        data = self.get_serializer(attempt).data
        data["questions"] = [
            {
                "position": q.position,
                "text": q.text,
                "options": q.options,
                "correct_option": q.correct_option,
                "selected": q.answer.option if hasattr(q, "answer") else None,
                "points": q.points,
            }
            for q in attempt.questions.select_related("answer")
        ]
        return Response(data)


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
        kind = request.data.get("report_type", "results")
        if kind not in ["results", "leaderboard", "students", "teachers"]:
            raise ValidationError("Hisobot turi noto‘g‘ri.")
        if kind == "teachers" and not is_admin(request.user):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Ruxsat yo‘q.")
        view = ResultViewSet()
        view.request = request
        qs = view.get_queryset()
        if request.data.get("quiz"):
            from django.shortcuts import get_object_or_404

            quiz = get_object_or_404(
                owned(Quiz.objects.all(), request.user), pk=request.data["quiz"]
            )
            qs = qs.filter(quiz=quiz)
        count = qs.count()
        if count > 100000:
            raise ValidationError(
                "Bir hisobot 100000 qatordan oshmasin. Filtrni aniqlashtiring."
            )
        if count > 5000 or request.data.get("background"):
            filters = {
                k: request.query_params[k]
                for k in [
                    "quiz",
                    "student",
                    "status",
                    "search",
                    "start",
                    "end",
                    "min_score",
                    "max_score",
                    "teacher",
                ]
                if request.query_params.get(k)
            }
            if request.data.get("quiz"):
                filters["quiz"] = request.data["quiz"]
            filters["report_type"] = kind
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
            export_report(qs, kind),
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
        return owned(ReportExport.objects.all(), self.request.user).order_by(
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


class SummaryReportView(APIView):
    def get(self, request):
        kind = request.query_params.get("type", "students")
        if kind not in ["students", "teachers", "leaderboard"]:
            raise ValidationError("Hisobot turi noto‘g‘ri.")
        if kind == "teachers" and not is_admin(request.user):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Ruxsat yo‘q.")
        view = ResultViewSet()
        view.request = request
        rows = report_data(view.get_queryset(), kind)
        paginator = PageNumberPagination()
        return paginator.get_paginated_response(
            paginator.paginate_queryset(rows, request)
        )
