from datetime import timedelta

import pytest
from apps.accounts.services import temporary_password
from django.utils import timezone
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def test_onboarding(admin):
    c = APIClient()
    c.force_login(admin)
    response = c.post(
        "/api/teachers/",
        {
            "username": "newteacher",
            "full_name": "Yangi Ustoz",
            "email": "new@example.com",
            "specialty": "Math",
        },
        format="json",
    )
    assert response.status_code == 201
    password = response.data["temporary_password"]
    assert "temporary_password" not in c.get("/api/teachers/").data["results"][0]
    c.logout()
    assert (
        c.post(
            "/api/auth/login/", {"username": "newteacher", "password": password}
        ).status_code
        == 200
    )
    assert c.get("/api/teachers/").status_code == 403
    assert (
        c.post(
            "/api/auth/change-password/",
            {
                "old_password": password,
                "new_password": "A-secure-replacement-234",
                "confirm_password": "A-secure-replacement-234",
            },
        ).status_code
        == 200
    )
    c.logout()
    assert (
        c.post(
            "/api/auth/login/", {"username": "newteacher", "password": password}
        ).status_code
        == 400
    )


def test_csrf_enforced(admin):
    c = APIClient(enforce_csrf_checks=True)
    assert (
        c.post(
            "/api/auth/login/", {"username": "admin", "password": "Strong-Password-987"}
        ).status_code
        == 403
    )
    token = c.get("/api/auth/csrf/").data["csrfToken"]
    assert (
        c.post(
            "/api/auth/login/",
            {"username": "admin", "password": "Strong-Password-987"},
            HTTP_X_CSRFTOKEN=token,
        ).status_code
        == 200
    )


def test_expired_temp_and_rate_limit(teacher, admin):
    password = temporary_password(teacher, admin)
    teacher.temporary_password_expires_at = timezone.now() - timedelta(seconds=1)
    teacher.save()
    c = APIClient()
    assert (
        c.post(
            "/api/auth/login/", {"username": "teacher", "password": password}
        ).status_code
        == 400
    )
    for _ in range(10):
        c.post("/api/auth/login/", {"username": "teacher", "password": "bad"})
    assert (
        c.post(
            "/api/auth/login/", {"username": "teacher", "password": "bad"}
        ).status_code
        == 429
    )


def test_roles(client, teacher):
    assert client.get("/api/teachers/").status_code == 403
    teacher.is_active = False
    teacher.save()
    assert client.get("/api/students/").status_code == 403


def test_profile_cannot_escalate_role(client, teacher):
    response = client.patch(
        "/api/profile/",
        {"full_name": "Updated Name", "role": "SUPER_ADMIN", "is_superuser": True},
        format="json",
    )
    assert response.status_code == 200
    teacher.refresh_from_db()
    assert teacher.role == "TEACHER" and not teacher.is_superuser
