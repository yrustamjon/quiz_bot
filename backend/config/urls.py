from django.urls import path, include
from apps.reports.views import DashboardView
from django.contrib import admin
from rest_framework.routers import DefaultRouter
from apps.accounts.views import AuthView, TeacherViewSet, StudentViewSet, GroupViewSet
from apps.quizzes.views import QuizViewSet
from apps.questions.views import QuestionViewSet
router = DefaultRouter()
router.register('quizzes',QuizViewSet,basename='quiz')
router.register('questions',QuestionViewSet,basename='question')
router.register('teachers', TeacherViewSet, basename='teacher')
router.register('students', StudentViewSet, basename='student')
router.register('groups', GroupViewSet)
urlpatterns = [path('api/dashboard/summary/',DashboardView.as_view()),path('admin/', admin.site.urls), path('api/auth/<str:operation>/', AuthView.as_view()), path('api/', include(router.urls))]
