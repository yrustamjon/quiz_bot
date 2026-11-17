import hashlib
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.middleware.csrf import get_token
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from .models import User, StudentProfile, Group
from .serializers import UserSerializer, StudentSerializer, GroupSerializer
from .permissions import AdminAccess, owned
from .services import temporary_password, rate_limit

@method_decorator(csrf_protect, name='dispatch')
class AuthView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, operation):
        if operation == 'csrf': return Response({'csrfToken': get_token(request)})
        if operation == 'me' and request.user.is_authenticated: return Response(UserSerializer(request.user).data)
        return Response({'detail': 'Hisobga kiring.'}, status=403)
    def post(self, request, operation):
        if operation == 'login':
            identity = str(request.data.get('username', ''))[:254]
            ip = request.META.get('REMOTE_ADDR', '')
            rate_limit('login-ip:' + ip, 30)
            rate_limit('login-user:' + hashlib.sha256(identity.lower().encode()).hexdigest(), 10)
            candidate = User.objects.filter(Q(username__iexact=identity) | Q(email__iexact=identity)).first()
            user = authenticate(request, username=candidate.username if candidate else identity, password=request.data.get('password', ''))
            if not user or user.role == 'STUDENT' or (user.role == 'SUPER_ADMIN' and not user.is_superuser) or (user.must_change_password and (not user.temporary_password_expires_at or user.temporary_password_expires_at <= timezone.now())):
                return Response({'detail': 'Login yoki parol noto‘g‘ri.'}, status=400)
            login(request, user)
            return Response(UserSerializer(user).data)
        if not request.user.is_authenticated: return Response(status=403)
        if operation == 'logout':
            logout(request)
            return Response(status=204)
        if operation == 'change-password':
            u = request.user
            if not u.check_password(request.data.get('old_password', '')): raise ValidationError({'old_password': 'Parol noto‘g‘ri.'})
            password = request.data.get('new_password', '')
            if password != request.data.get('confirm_password'): raise ValidationError({'confirm_password': 'Parollar mos emas.'})
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
    http_method_names = ['get', 'post', 'patch', 'head', 'options']
    def get_queryset(self):
        return User.objects.filter(role='TEACHER').filter(Q(full_name__icontains=self.request.query_params.get('search', '')) | Q(username__icontains=self.request.query_params.get('search', ''))).order_by('-id')
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        u = serializer.save(role='TEACHER')
        password = temporary_password(u, request.user)
        return Response({**serializer.data, 'temporary_password': password}, status=201)
    @action(detail=True, methods=['post'], url_path='reset-password')
    def reset_password(self, request, pk=None):
        return Response({'temporary_password': temporary_password(self.get_object(), request.user)})
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None): return self.set_active(True)
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None): return self.set_active(False)
    def set_active(self, active):
        u = self.get_object(); u.is_active = active; u.save(update_fields=['is_active'])
        return Response(self.get_serializer(u).data)

class StudentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StudentSerializer
    def get_queryset(self):
        from .permissions import is_admin
        qs = StudentProfile.objects.all()
        if not is_admin(self.request.user): qs = qs.filter(attempts__quiz__owner=self.request.user)
        return qs.filter(full_name__icontains=self.request.query_params.get('search', '')).distinct().order_by('-id')

class GroupViewSet(viewsets.ModelViewSet):
    permission_classes = [AdminAccess]
    queryset = Group.objects.all().order_by('name')
    serializer_class = GroupSerializer
