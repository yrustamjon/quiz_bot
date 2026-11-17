import hashlib
from collections.abc import Mapping

from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.db.models import Avg, Count, Max, Q
from django.middleware.csrf import get_token
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Group, StudentProfile, User
from .permissions import AdminAccess, owned
from .serializers import GroupSerializer, StudentSerializer, UserSerializer
from .services import rate_limit, temporary_expired, temporary_password


@method_decorator(csrf_protect, name="dispatch")
class AuthView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, operation):
        if operation == "csrf":
            return Response({"csrfToken": get_token(request)})
        if operation == "me" and request.user.is_authenticated:
            if temporary_expired(request.user):
                logout(request)
                return Response(
                    {
                        "detail": "Vaqtinchalik parol muddati tugagan. Administrator bilan bog‘laning."
                    },
                    status=403,
                )
            return Response(UserSerializer(request.user).data)
        return Response({"detail": "Hisobga kiring."}, status=403)

    def post(self, request, operation):
        if not isinstance(request.data, Mapping):
            raise ValidationError("So‘rov maydonlari noto‘g‘ri.")

        def text(field, limit=4096):
            value = request.data.get(field, "")
            if not isinstance(value, str) or len(value) > limit:
                raise ValidationError({field: "Matn qiymati noto‘g‘ri yoki juda uzun."})
            return value

        if operation == "login":
            identity = text("username", 254)
            password = text("password")
            ip = request.META.get("REMOTE_ADDR", "")
            rate_limit("login-ip:" + ip, 30)
            rate_limit(
                "login-user:" + hashlib.sha256(identity.lower().encode()).hexdigest(),
                10,
            )
            candidate = User.objects.filter(
                Q(username__iexact=identity) | Q(email__iexact=identity)
            ).first()
            user = authenticate(
                request,
                username=candidate.username if candidate else identity,
                password=password,
            )
            if (
                not user
                or user.role == "STUDENT"
                or (user.role == "SUPER_ADMIN" and not user.is_superuser)
                or (
                    user.must_change_password
                    and (
                        not user.temporary_password_expires_at
                        or user.temporary_password_expires_at <= timezone.now()
                    )
                )
            ):
                return Response({"detail": "Login yoki parol noto‘g‘ri."}, status=400)
            login(request, user)
            return Response(UserSerializer(user).data)
        if not request.user.is_authenticated:
            return Response(status=403)
        if operation == "logout":
            logout(request)
            return Response(status=204)
        if operation == "change-password":
            u = request.user
            if temporary_expired(u):
                logout(request)
                return Response(
                    {
                        "detail": "Vaqtinchalik parol muddati tugagan. Administrator bilan bog‘laning."
                    },
                    status=403,
                )
            rate_limit("password-change:" + str(u.pk), 10)
            if not u.check_password(text("old_password")):
                raise ValidationError({"old_password": "Parol noto‘g‘ri."})
            password = text("new_password")
            if password != text("confirm_password"):
                raise ValidationError({"confirm_password": "Parollar mos emas."})
            if u.check_password(password):
                raise ValidationError(
                    {"new_password": "Yangi parol oldingisidan farq qilsin."}
                )
            validate_password(password, u)
            u.set_password(password)
            u.must_change_password = False
            u.temporary_password_expires_at = None
            u.save()
            update_session_auth_hash(request, u)
            return Response(UserSerializer(u).data)
        return Response(status=404)


class TeacherViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [AdminAccess]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        qs = User.objects.filter(role="TEACHER").filter(
            Q(full_name__icontains=self.request.query_params.get("search", ""))
            | Q(username__icontains=self.request.query_params.get("search", ""))
        )
        state = self.request.query_params.get("is_active")
        if state in ["true", "false"]:
            qs = qs.filter(is_active=state == "true")
        elif state:
            raise ValidationError("Hisob holati noto‘g‘ri.")
        return qs.annotate(quiz_count=Count("quizzes")).order_by("-id")

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        for field in ["full_name", "email", "specialty"]:
            if not request.data.get(field):
                raise ValidationError({field: "Majburiy maydonni to‘ldiring."})
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        u = serializer.save(role="TEACHER")
        password = temporary_password(u, request.user)
        return Response({**serializer.data, "temporary_password": password}, status=201)

    @action(detail=True, methods=["post"], url_path="reset-password")
    def reset_password(self, request, pk=None):
        return Response(
            {"temporary_password": temporary_password(self.get_object(), request.user)}
        )

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        return self.set_active(True)

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        return self.set_active(False)

    def set_active(self, active):
        u = self.get_object()
        u.is_active = active
        u.save(update_fields=["is_active"])
        return Response(self.get_serializer(u).data)


class StudentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StudentSerializer

    def get_queryset(self):
        from apps.attempts.models import Attempt
        from apps.quizzes.models import Quiz

        from .permissions import is_admin

        scope = (
            Q()
            if is_admin(self.request.user)
            else Q(attempts__quiz__owner=self.request.user)
        )
        qs = StudentProfile.objects.all()
        if not is_admin(self.request.user):
            qs = qs.filter(
                pk__in=Attempt.objects.filter(quiz__owner=self.request.user).values(
                    "student_id"
                )
            )
        if self.request.query_params.get("quiz"):
            quiz_id = self.request.query_params["quiz"]
            if not quiz_id.isdigit():
                raise ValidationError("Test filtri noto‘g‘ri.")
            allowed_quizzes = owned(Quiz.objects.all(), self.request.user)
            if not allowed_quizzes.filter(pk=quiz_id).exists():
                from rest_framework.exceptions import NotFound

                raise NotFound()
            qs = qs.filter(attempts__quiz_id=quiz_id)
        return (
            qs.filter(full_name__icontains=self.request.query_params.get("search", ""))
            .annotate(
                participation_count=Count("attempts", filter=scope),
                average_percentage=Avg(
                    "attempts__percentage",
                    filter=scope & ~Q(attempts__status="in_progress"),
                ),
                last_activity=Max("attempts__started_at", filter=scope),
            )
            .order_by("-id")
        )

    def retrieve(self, request, *args, **kwargs):
        from apps.attempts.models import Attempt
        from apps.reports.serializers import ResultSerializer

        student = self.get_object()
        attempts = owned(
            Attempt.objects.filter(student=student).select_related("student", "quiz"),
            request.user,
            "quiz__owner",
        ).order_by("-started_at")
        return Response(
            {
                **self.get_serializer(student).data,
                "attempts": ResultSerializer(attempts[:25], many=True).data,
            }
        )

    @action(detail=True, methods=["post"], permission_classes=[AdminAccess])
    def activate(self, request, pk=None):
        return self.set_active(True)

    @action(detail=True, methods=["post"], permission_classes=[AdminAccess])
    def deactivate(self, request, pk=None):
        return self.set_active(False)

    def set_active(self, active):
        student = self.get_object()
        student.is_active = active
        student.save(update_fields=["is_active"])
        return Response(self.get_serializer(student).data)


class GroupViewSet(viewsets.ModelViewSet):
    permission_classes = [AdminAccess]
    queryset = Group.objects.all().order_by("name")
    serializer_class = GroupSerializer


class ProfileView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        allowed = {
            k: request.data[k]
            for k in ["full_name", "email", "specialty"]
            if k in request.data
        }
        serializer = UserSerializer(request.user, data=allowed, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
