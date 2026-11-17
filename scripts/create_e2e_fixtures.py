"""Explicitly opt-in test fixtures; requires the isolated suite's environment."""

import json
import os
import secrets
import sys
from pathlib import Path

if os.getenv("QUIZ_E2E_FIXTURES") != "1":
    raise RuntimeError("Use scripts/browser_suite.py for isolated fixtures.")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()
from apps.accounts.models import User
from apps.questions.importer import template

artifacts = Path(os.environ["QUIZ_ARTIFACT_DIR"])
artifacts.mkdir(parents=True, exist_ok=True)
for name, admin in [("ui-identity.json", False), ("ui-admin.json", True)]:
    password = secrets.token_urlsafe(24)
    user = (
        User.objects.create_superuser(
            username="browser-admin", password=password, full_name="Admin tekshiruvi"
        )
        if admin
        else User.objects.create_user(
            username="browser-teacher",
            password=password,
            role="TEACHER",
            full_name="Interfeys tekshiruvi",
        )
    )
    if not admin:
        teacher = user
    path = artifacts / name
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(
            {"id": user.pk, "username": user.username, "password": password}, stream
        )
(artifacts / "template.xlsx").write_bytes(template())
print("Disposable browser identities created; no credentials printed.")

from apps.accounts.models import StudentProfile
from apps.attempts.services import answer, finish, start
from apps.questions.models import Question, QuizQuestion
from apps.quizzes.models import Quiz
from apps.quizzes.services import transition

student = StudentProfile.objects.create(telegram_id=101, full_name="Sinov O‘quvchi")
quiz = Quiz.objects.create(
    owner=teacher,
    title="Brauzer sinovi — Matematika",
    subject="Matematika",
    question_count=1,
)
question = Question.objects.create(
    owner=teacher,
    text="2 + 2 nechaga teng?",
    options=["3", "4", "5", "6"],
    correct_option=1,
)
QuizQuestion.objects.create(quiz=quiz, question=question, position=0)
transition(quiz, "published")
quiz.refresh_from_db()
a = start(student, quiz)
a, _ = answer(a.pk, student.telegram_id, 0, 1, 0)
finish(a.pk, student.telegram_id, True)
draft = Quiz.objects.create(
    owner=teacher, title="Wizard brauzer sinovi", subject="Matematika", question_count=1
)
QuizQuestion.objects.create(quiz=draft, question=question, position=0)
private = Quiz.objects.create(
    owner=teacher,
    title="Yopiq brauzer sinovi",
    subject="Matematika",
    question_count=1,
    access="private",
)
QuizQuestion.objects.create(quiz=private, question=question, position=0)
transition(private, "published")
bank_question = Question.objects.create(
    owner=teacher,
    text="Bankdan tanlanadigan savol",
    options=["a", "b", "c", "d"],
    correct_option=1,
)
from PIL import Image

Image.new("RGB", (16, 16), "#2563eb").save(artifacts / "question.png")
(artifacts / "fixture-records.json").write_text(
    json.dumps(
        {
            "student": student.pk,
            "quiz": quiz.pk,
            "draft": draft.pk,
            "private": private.pk,
        }
    )
)
