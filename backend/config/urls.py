from apps.accounts.views import (
    AuthView,
    GroupViewSet,
    ProfileView,
    StudentViewSet,
    TeacherViewSet,
)
from apps.questions.import_views import ImportView
from apps.questions.views import QuestionViewSet
from apps.quizzes.views import QuizViewSet
from apps.reports.views import (
    DashboardView,
    ExportJobViewSet,
    ExportView,
    RankingView,
    ResultViewSet,
)
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("reports/exports", ExportJobViewSet, basename="export-job")
router.register("results", ResultViewSet, basename="result")
router.register("quizzes", QuizViewSet, basename="quiz")
router.register("questions", QuestionViewSet, basename="question")
router.register("teachers", TeacherViewSet, basename="teacher")
router.register("students", StudentViewSet, basename="student")
router.register("groups", GroupViewSet)
urlpatterns = [
    path("api/profile/", ProfileView.as_view()),
    path("api/rankings/", RankingView.as_view()),
    path("api/reports/export/", ExportView.as_view()),
    path("api/questions/import/<str:operation>/", ImportView.as_view()),
    path("api/dashboard/summary/", DashboardView.as_view()),
    path("admin/", admin.site.urls),
    path("api/auth/<str:operation>/", AuthView.as_view()),
    path("api/", include(router.urls)),
]
