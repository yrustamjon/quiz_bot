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


def test_restart_expired_start_preserves_finalization(quiz, student):
    transition(quiz, "published")
    quiz.refresh_from_db()
    a = start(student, quiz)
    Attempt.objects.filter(pk=a.pk).update(
        deadline=timezone.now() - timedelta(seconds=1)
    )
    again = start(student, quiz)
    assert again.pk == a.pk and again.status == "timed_out"
    a.refresh_from_db()
    assert a.status == "timed_out"


def test_at_exact_deadline_and_duplicate_reconciliation(quiz, student):
    from unittest.mock import patch

    from apps.attempts.tasks import reconcile

    transition(quiz, "published")
    quiz.refresh_from_db()
    a = start(student, quiz)
    with patch("apps.attempts.services.timezone.now", return_value=a.deadline):
        result, ok = answer(a.pk, 123, 0, 0, 0)
        assert not ok and result.status == "timed_out" and result.earned == 0
    assert reconcile() == 0 and reconcile() == 0
    a.refresh_from_db()
    assert a.revision == 1


def test_private_start_throttle_survives_failed_transaction(quiz, student):
    from rest_framework.exceptions import Throttled

    quiz.access = "private"
    quiz.save()
    transition(quiz, "published")
    quiz.refresh_from_db()
    for _ in range(10):
        with pytest.raises(ValidationError):
            start(student, quiz, "BAD")
    with pytest.raises(Throttled):
        start(student, quiz, "BAD")


def test_bot_rankings_cannot_leak_hidden_percentage(quiz, student):
    from bot.services import quiz_ranking, student_ranking

    quiz.show_percentage = False
    quiz.save()
    transition(quiz, "published")
    quiz.refresh_from_db()
    a = start(student, quiz)
    a = finish(a.pk, 123, True)
    data = student_result(a, 123)
    assert "percentage" not in data and "rank" in data
    rows, _ = student_ranking(123)
    assert not rows
    rows, own = quiz_ranking(123, quiz.pk)
    assert own == 1 and rows[0]["percentage"] is None
    assert quiz_ranking(999, quiz.pk) is None


def test_access_code_read_and_rotation_are_owner_scoped(client, quiz, student, other):
    from apps.quizzes.services import regenerate_code

    quiz.access = "private"
    quiz.save()
    transition(quiz, "published")
    quiz.refresh_from_db()
    old = quiz.access_code.code
    response = client.get(f"/api/quizzes/{quiz.pk}/access-code/")
    assert (
        response.data["code"] == old
        and response["Cache-Control"] == "private, no-store"
    )
    new = regenerate_code(quiz)
    with pytest.raises(ValidationError):
        start(student, quiz, old)
    assert start(student, quiz, new)
    quiz.owner = other
    quiz.save()
    assert client.get(f"/api/quizzes/{quiz.pk}/access-code/").status_code == 404


def test_private_code_lookup_hides_unavailable_quiz(quiz, student):
    from apps.quizzes.services import regenerate_code

    from bot.services import by_code

    quiz.access = "private"
    quiz.save()
    code = regenerate_code(quiz)
    assert by_code(student.telegram_id, code) is None
    transition(quiz, "published")
    quiz.refresh_from_db()
    code = quiz.access_code.code
    assert by_code(student.telegram_id, code).pk == quiz.pk
    quiz.status = "closed"
    quiz.save()
    assert by_code(student.telegram_id, code) is None


def test_percentage_display_rounding():
    from apps.attempts.scoring import percent_display

    assert percent_display("2.675000") == "2.68"
    assert percent_display("2.665000") == "2.67"
    assert percent_display("99.995000") == "100.00"


def test_manual_release_rejects_draft_and_preserves_owner_scope(client, quiz, other):
    assert client.post(f"/api/quizzes/{quiz.pk}/release-results/").status_code == 400
    quiz.status = "published"
    quiz.save()
    assert client.post(f"/api/quizzes/{quiz.pk}/release-results/").status_code == 200
    quiz.refresh_from_db()
    assert quiz.results_released
    quiz.owner = other
    quiz.save()
    assert client.post(f"/api/quizzes/{quiz.pk}/release-results/").status_code == 404


def test_finish_preview_counts_answers_and_reconciles_expiration(quiz, student):
    from datetime import timedelta

    from apps.attempts.services import preview_finish

    transition(quiz, "published")
    quiz.refresh_from_db()
    a = start(student, quiz)
    answer(a.pk, student.telegram_id, 0, 0, 0)
    pending, total, saved = preview_finish(a.pk, student.telegram_id)
    assert pending.status == "in_progress" and total == 2 and saved == 1
    with pytest.raises(PermissionDenied):
        preview_finish(a.pk, student.telegram_id + 1)
    Attempt.objects.filter(pk=a.pk).update(
        deadline=timezone.now() - timedelta(seconds=1)
    )
    expired, _, _ = preview_finish(a.pk, student.telegram_id)
    assert (
        expired.status == "timed_out"
        and expired.correct == 1
        and expired.unanswered == 1
    )
