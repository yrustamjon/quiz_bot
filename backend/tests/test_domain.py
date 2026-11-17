from datetime import timedelta

import pytest
from apps.accounts.models import StudentProfile
from apps.attempts.models import Attempt
from apps.attempts.services import (
    answer,
    finish,
    navigate,
    resume,
    start,
    student_result,
)
from apps.questions.models import Question, QuizQuestion
from apps.quizzes.models import Quiz
from apps.quizzes.services import regenerate_code, transition
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

pytestmark = pytest.mark.django_db


@pytest.fixture
def quiz(teacher):
    q = Quiz.objects.create(
        owner=teacher, title="Algebra", subject="Matematika", question_count=2
    )
    for i in range(2):
        x = Question.objects.create(
            owner=teacher,
            text=f"Savol {i}",
            options=["a", "b", "c", "d"],
            correct_option=0,
        )
        QuizQuestion.objects.create(quiz=q, question=x, position=i)
    return q


@pytest.fixture
def student():
    return StudentProfile.objects.create(telegram_id=123, full_name="Ali Vali")


def test_object_security(client, other, quiz):
    quiz.owner = other
    quiz.save()
    assert client.get(f"/api/quizzes/{quiz.pk}/").status_code == 404
    assert client.post(f"/api/quizzes/{quiz.pk}/publish/").status_code == 404
    assert (
        client.put(
            f"/api/quizzes/{quiz.pk}/questions/", {"question_ids": []}, format="json"
        ).status_code
        == 404
    )
    question = quiz.question_links.first().question
    question.owner = other
    question.save()
    assert (
        client.patch(f"/api/questions/{question.pk}/", {"text": "hacked"}).status_code
        == 404
    )


def test_full_sequential(quiz, student):
    transition(quiz, "published")
    quiz.refresh_from_db()
    a = start(student, quiz)
    assert start(student, quiz).pk == a.pk
    a, ok = answer(a.pk, 123, 0, 0, 0)
    assert ok
    with pytest.raises(ValidationError):
        answer(a.pk, 123, 0, 1, 0)
    with pytest.raises(PermissionDenied):
        answer(a.pk, 999, 1, 0, a.revision)
    assert resume(123).cursor == 1
    with pytest.raises(ValidationError):
        finish(a.pk, 123)
    a = finish(a.pk, 123, True)
    assert a.correct == 1 and a.unanswered == 1 and a.percentage == 50
    assert finish(a.pk, 123, True).earned == a.earned
    assert "questions" not in student_result(a, 123)


def test_deadline(quiz, student):
    transition(quiz, "published")
    quiz.refresh_from_db()
    a = start(student, quiz)
    Attempt.objects.filter(pk=a.pk).update(
        deadline=timezone.now() - timedelta(seconds=1)
    )
    a, ok = answer(a.pk, 123, 0, 0, 0)
    assert not ok and a.status == "timed_out" and a.unanswered == 2


def test_free_and_result_release(quiz, student):
    quiz.navigation = "free"
    quiz.result_release_mode = "manual"
    quiz.save()
    transition(quiz, "published")
    quiz.refresh_from_db()
    a = start(student, quiz)
    a, _ = answer(a.pk, 123, 0, 1, 0)
    a, _ = answer(a.pk, 123, 0, 0, a.revision)
    a = navigate(a.pk, 123, 1, a.revision)
    a, _ = answer(a.pk, 123, 1, 0, a.revision)
    a = finish(a.pk, 123, True)
    assert a.correct == 2 and not student_result(a, 123)["released"]


def test_private_code(quiz, student):
    quiz.access = "private"
    quiz.save()
    transition(quiz, "published")
    quiz.refresh_from_db()
    with pytest.raises(ValidationError):
        start(student, quiz, "BAD")
    code = regenerate_code(quiz)
    assert start(student, quiz, code)


def test_publish_invalid(quiz):
    quiz.question_count = 3
    quiz.save()
    with pytest.raises(ValidationError):
        transition(quiz, "published")


def test_expired_code_and_snapshot(quiz, student):
    quiz.access = "private"
    quiz.shuffle_options = True
    quiz.save()
    transition(quiz, "published")
    quiz.refresh_from_db()
    code = quiz.access_code
    code.expires_at = timezone.now() - timedelta(seconds=1)
    code.save()
    with pytest.raises(ValidationError):
        start(student, quiz, code.code)
    code.expires_at = None
    code.save()
    a = start(student, quiz, code.code)
    snapshot = a.questions.first()
    original = snapshot.text
    q = quiz.question_links.first().question
    q.text = "Changed outside API"
    q.save()
    snapshot.refresh_from_db()
    assert snapshot.text == original
    a, _ = answer(a.pk, 123, 0, snapshot.correct_option, 0)
    assert finish(a.pk, 123, True).correct == 1
