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
