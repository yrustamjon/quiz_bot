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
