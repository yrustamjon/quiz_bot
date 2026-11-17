from concurrent.futures import ThreadPoolExecutor

import pytest
from apps.accounts.models import StudentProfile, User
from apps.attempts.models import AttemptAnswer
from apps.attempts.services import answer, finish, start
from apps.questions.models import Question, QuizQuestion
from apps.quizzes.models import Quiz
from apps.quizzes.services import transition
from django.db import close_old_connections
from rest_framework.exceptions import ValidationError


@pytest.mark.django_db(transaction=True)
def test_concurrent_start_answer_finish():
    teacher = User.objects.create_user(username="concurrent", role="TEACHER")
    student = StudentProfile.objects.create(telegram_id=12345, full_name="Race Test")
    quiz = Quiz.objects.create(
        owner=teacher, title="Race", subject="Fan", question_count=1
    )
    question = Question.objects.create(
        owner=teacher, text="One", options=["1", "2", "3", "4"], correct_option=0
    )
    QuizQuestion.objects.create(quiz=quiz, question=question, position=0)
    transition(quiz, "published")
    quiz.refresh_from_db()

    def run_start(_):
        close_old_connections()
        try:
            return start(student, quiz).pk
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        ids = list(pool.map(run_start, range(2)))
    assert ids[0] == ids[1] and quiz.attempts.count() == 1

    def run_answer(_):
        close_old_connections()
        try:
            try:
                return answer(ids[0], student.telegram_id, 0, 0, 0)[1]
            except ValidationError:
                return False
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        accepted = list(pool.map(run_answer, range(2)))
    assert sum(accepted) == 1 and AttemptAnswer.objects.count() == 1

    def run_finish(_):
        close_old_connections()
        try:
            return finish(ids[0], student.telegram_id, True).percentage
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        percentages = list(pool.map(run_finish, range(2)))
    assert percentages == [100, 100]


@pytest.mark.django_db(transaction=True)
def test_finish_races_with_timeout_reconciliation():
    from datetime import timedelta

    from apps.attempts.models import Attempt
    from apps.attempts.tasks import reconcile
    from django.utils import timezone

    teacher = User.objects.create_user(username="timeout-owner", role="TEACHER")
    student = StudentProfile.objects.create(telegram_id=7137, full_name="Timeout Race")
    quiz = Quiz.objects.create(
        owner=teacher, title="Timeout", subject="Fan", question_count=1
    )
    question = Question.objects.create(
        owner=teacher, text="One", options=["1", "2", "3", "4"], correct_option=0
    )
    QuizQuestion.objects.create(quiz=quiz, question=question, position=0)
    transition(quiz, "published")
    quiz.refresh_from_db()
    attempt = start(student, quiz)
    attempt, _ = answer(attempt.pk, student.telegram_id, 0, 0, 0)
    Attempt.objects.filter(pk=attempt.pk).update(
        deadline=timezone.now() - timedelta(seconds=1)
    )

    def complete():
        close_old_connections()
        try:
            return finish(attempt.pk, student.telegram_id, True).percentage
        finally:
            close_old_connections()

    def expire():
        close_old_connections()
        try:
            return reconcile()
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        f = pool.submit(complete)
        t = pool.submit(expire)
        assert f.result() == 100
        t.result()
    attempt.refresh_from_db()
    assert (
        attempt.status == "timed_out"
        and attempt.correct == 1
        and attempt.unanswered == 0
    )
    assert reconcile() == 0


@pytest.mark.django_db(transaction=True)
def test_resume_racing_expiration_keeps_answers_and_original_deadline():
    from datetime import timedelta

    from apps.attempts.models import Attempt
    from apps.attempts.services import resume
    from apps.attempts.tasks import reconcile
    from django.utils import timezone

    teacher = User.objects.create_user(username="resume-owner", role="TEACHER")
    student = StudentProfile.objects.create(telegram_id=8831, full_name="Resume Race")
    quiz = Quiz.objects.create(
        owner=teacher, title="Resume", subject="Fan", question_count=2
    )
    for position in range(2):
        question = Question.objects.create(
            owner=teacher,
            text=f"Q{position}",
            options=["1", "2", "3", "4"],
            correct_option=0,
        )
        QuizQuestion.objects.create(quiz=quiz, question=question, position=position)
    transition(quiz, "published")
    quiz.refresh_from_db()
    attempt = start(student, quiz)
    answer(attempt.pk, student.telegram_id, 0, 0, 0)
    deadline = timezone.now() - timedelta(seconds=1)
    Attempt.objects.filter(pk=attempt.pk).update(deadline=deadline)

    def recover():
        close_old_connections()
        try:
            return resume(student.telegram_id)
        finally:
            close_old_connections()

    def expire():
        close_old_connections()
        try:
            return reconcile()
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        resumed, expired = pool.submit(recover), pool.submit(expire)
        recovered = resumed.result(timeout=30)
        expired.result(timeout=30)
    attempt.refresh_from_db()
    assert recovered is None or (
        recovered.pk == attempt.pk and recovered.status == "timed_out"
    )
    assert attempt.status == "timed_out" and attempt.deadline == deadline
    assert attempt.correct == 1 and attempt.unanswered == 1 and attempt.percentage == 50
    assert (
        quiz.attempts.count() == 1
        and AttemptAnswer.objects.filter(question__attempt=attempt).count() == 1
    )
    assert reconcile() == 0


@pytest.mark.django_db(transaction=True)
def test_question_update_and_publication_cannot_interleave():
    from threading import Event
    from unittest.mock import patch

    from apps.questions.serializers import QuestionSerializer
    from rest_framework.test import APIClient

    teacher = User.objects.create_user(username="edit-owner", role="TEACHER")
    quiz = Quiz.objects.create(
        owner=teacher, title="Edit race", subject="Fan", question_count=1
    )
    question = Question.objects.create(
        owner=teacher, text="Original", options=["1", "2", "3", "4"], correct_option=0
    )
    QuizQuestion.objects.create(quiz=quiz, question=question, position=0)
    client = APIClient()
    client.force_login(teacher)
    entered, release, publishing, published = Event(), Event(), Event(), Event()
    original_update = QuestionSerializer.update

    def paused_update(serializer, instance, validated):
        entered.set()
        if not release.wait(timeout=5):
            raise RuntimeError("Test gate timed out")
        return original_update(serializer, instance, validated)

    def edit():
        close_old_connections()
        try:
            return client.patch(
                f"/api/questions/{question.pk}/", {"text": "Edited"}, format="json"
            ).status_code
        finally:
            close_old_connections()

    def publish():
        close_old_connections()
        try:
            publishing.set()
            transition(quiz, "published")
            published.set()
        finally:
            close_old_connections()

    with (
        patch.object(QuestionSerializer, "update", paused_update),
        ThreadPoolExecutor(max_workers=2) as pool,
    ):
        editing = pool.submit(edit)
        try:
            assert entered.wait(timeout=5)
            publication = pool.submit(publish)
            assert publishing.wait(timeout=5)
            # Publication must wait for the entire checked update, not overtake
            # its status check and then let it mutate an already-published quiz.
            assert not published.wait(timeout=0.25)
        finally:
            release.set()
        assert editing.result(timeout=30) == 200
        publication.result(timeout=30)
    quiz.refresh_from_db()
    question.refresh_from_db()
    assert quiz.status == "published" and question.text == "Edited"
    assert (
        client.patch(
            f"/api/questions/{question.pk}/", {"text": "Late edit"}
        ).status_code
        == 400
    )
    question.refresh_from_db()
    assert question.text == "Edited"
