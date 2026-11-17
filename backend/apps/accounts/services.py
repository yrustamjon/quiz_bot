import secrets
from datetime import timedelta

from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import Throttled, ValidationError

from .models import AuditLog, StudentProfile


@transaction.atomic
def temporary_password(user, actor):
    password = secrets.token_urlsafe(18)
    user.set_password(password)
    user.must_change_password = True
    user.temporary_password_expires_at = timezone.now() + timedelta(hours=24)
    user.save()
    AuditLog.objects.create(
        actor=actor, action="teacher.temporary_password", object_id=str(user.pk)
    )
    return password


def rate_limit(key, limit=10, seconds=300):
    if cache.add(key, 1, seconds):
        return
    try:
        count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, seconds)
        count = 1
    if count > limit:
        raise Throttled(
            seconds, detail="Juda ko‘p urinish. Keyinroq qayta urinib ko‘ring."
        )


@transaction.atomic
def register_student(telegram_id, full_name, username=""):
    name = " ".join(full_name.split())
    if not 3 <= len(name) <= 150 or any(ord(c) < 32 for c in name):
        raise ValidationError("To‘liq ism 3–150 belgidan iborat bo‘lsin.")
    student, created = StudentProfile.objects.get_or_create(
        telegram_id=telegram_id,
        defaults={"full_name": name, "telegram_username": username or ""},
    )
    if not student.is_active:
        raise ValidationError("Hisob faol emas.")
    if not created:
        student.telegram_username = username or ""
        student.save(update_fields=["telegram_username"])
    return student
