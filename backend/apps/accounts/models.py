from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower


class User(AbstractUser):
    class Role(models.TextChoices):
        SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
        TEACHER = "TEACHER", "O‘qituvchi"
        STUDENT = "STUDENT", "O‘quvchi"

    role = models.CharField(max_length=16, choices=Role.choices, default=Role.STUDENT)
    full_name = models.CharField(max_length=150, blank=True)
    specialty = models.CharField(max_length=150, blank=True)
    must_change_password = models.BooleanField(default=False)
    temporary_password_expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(Lower("username"), name="username_case_unique"),
            models.UniqueConstraint(
                Lower("email"), condition=~models.Q(email=""), name="email_case_unique"
            ),
        ]

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.Role.SUPER_ADMIN
            self.is_staff = True
        super().save(*args, **kwargs)


class StudentProfile(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    full_name = models.CharField(max_length=150)
    telegram_username = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    registered_at = models.DateTimeField(auto_now_add=True)


class Group(models.Model):
    name = models.CharField(max_length=150, unique=True)
    students = models.ManyToManyField(StudentProfile, blank=True, related_name="groups")


class AuditLog(models.Model):
    actor = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=100)
    object_id = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
