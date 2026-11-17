from datetime import timedelta

import pytest
from apps.accounts.models import User
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


def test_student_and_anonymous_cannot_use_panel():
    from rest_framework.test import APIClient

    student = User.objects.create_user(username="student-web", role="STUDENT")
    c = APIClient()
    for path in [
        "/api/quizzes/",
        "/api/questions/",
        "/api/results/",
        "/api/reports/exports/",
        "/api/dashboard/summary/",
    ]:
        assert c.get(path).status_code == 403
    c.force_login(student)
    for path in ["/api/quizzes/", "/api/teachers/", "/api/groups/", "/api/profile/"]:
        assert c.get(path).status_code == 403


def test_api_validation_is_uzbek(client):
    response = client.post(
        "/api/quizzes/",
        {"title": "", "subject": "", "duration_minutes": 0},
        format="json",
    )
    assert response.status_code == 400 and response.data["title"] == [
        "Bu maydon bo‘sh bo‘lmasin."
    ]


def test_expired_temporary_session_cannot_change_password(teacher, admin):
    from rest_framework.test import APIClient

    password = temporary_password(teacher, admin)
    c = APIClient()
    c.force_login(teacher)
    teacher.temporary_password_expires_at = timezone.now() - timedelta(seconds=1)
    teacher.save()
    response = c.post(
        "/api/auth/change-password/",
        {
            "old_password": password,
            "new_password": "Strong-new-secret-@#-9833",
            "confirm_password": "Strong-new-secret-@#-9833",
        },
    )
    assert response.status_code == 403
    assert c.get("/api/auth/me/").status_code == 403


def test_student_status_is_admin_only(client, admin):
    from apps.accounts.models import StudentProfile
    from rest_framework.test import APIClient

    student = StudentProfile.objects.create(
        telegram_id=4933, full_name="Active Student"
    )
    assert client.post(f"/api/students/{student.pk}/deactivate/").status_code == 403
    c = APIClient()
    c.force_login(admin)
    assert c.post(f"/api/students/{student.pk}/deactivate/").status_code == 200
    student.refresh_from_db()
    assert not student.is_active
    assert c.post(f"/api/students/{student.pk}/activate/").status_code == 200


@pytest.mark.parametrize(
    "payload",
    [["invalid"], {"username": []}, {"password": []}, {"password": "x" * 4097}],
)
def test_malformed_auth_credentials_are_rejected(payload):
    from rest_framework.test import APIClient

    response = APIClient().post("/api/auth/login/", payload, format="json")
    assert response.status_code == 400


def test_password_change_cannot_reuse_temporary_password(teacher, admin):
    from rest_framework.test import APIClient

    password = temporary_password(teacher, admin)
    c = APIClient()
    c.force_login(teacher)
    response = c.post(
        "/api/auth/change-password/",
        {
            "old_password": password,
            "new_password": password,
            "confirm_password": password,
        },
        format="json",
    )
    assert response.status_code == 400
    teacher.refresh_from_db()
    assert teacher.must_change_password and teacher.check_password(password)
