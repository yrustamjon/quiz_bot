from rest_framework.permissions import BasePermission

def is_admin(user):
    return bool(user.is_authenticated and user.is_active and user.is_superuser and user.role == 'SUPER_ADMIN')

class PanelAccess(BasePermission):
    message = 'Kirish huquqi yo‘q yoki parolni almashtirish zarur.'
    def has_permission(self, request, view):
        u = request.user
        return bool(u.is_authenticated and u.is_active and not u.must_change_password and (is_admin(u) or u.role == 'TEACHER'))

class AdminAccess(PanelAccess):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and is_admin(request.user)

def owned(qs, user, field='owner'):
    return qs if is_admin(user) else qs.filter(**{field: user})
