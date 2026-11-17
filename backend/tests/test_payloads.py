"""Malformed top-level JSON must be rejected without server exceptions."""

import json

import pytest
from apps.quizzes.models import Quiz
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_non_object_json_is_rejected_for_custom_mutations(admin):
    client = APIClient()
    client.force_login(admin)
    client.raise_request_exception = False
    quiz = Quiz.objects.create(owner=admin, title="Payload validation", subject="Fan")
    endpoints = [
        ("POST", "/api/teachers/"),
        ("POST", "/api/questions/import/preview/"),
        ("POST", "/api/reports/export/"),
        ("PUT", f"/api/quizzes/{quiz.pk}/questions/"),
    ]
    for payload in [[], None, "invalid", 42, True]:
        for method, path in endpoints:
            response = client.generic(
                method, path, data=json.dumps(payload), content_type="application/json"
            )
            assert response.status_code == 400, (
                method,
                path,
                type(payload).__name__,
                response.status_code,
            )
