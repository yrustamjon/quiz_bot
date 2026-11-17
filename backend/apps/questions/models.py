import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


def image_path(instance, filename):
    return "questions/" + uuid.uuid4().hex + ".png"


class Question(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    text = models.TextField()
    subject = models.CharField(max_length=100, blank=True)
    options = models.JSONField(default=list)
    correct_option = models.PositiveSmallIntegerField()
    points = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=1,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    image = models.ImageField(upload_to=image_path, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(correct_option__gte=0, correct_option__lte=3),
                name="question_valid_correct",
            ),
            models.CheckConstraint(
                condition=models.Q(points__gt=0), name="question_positive_points"
            ),
        ]


class QuizQuestion(models.Model):
    quiz = models.ForeignKey(
        "quizzes.Quiz", on_delete=models.CASCADE, related_name="question_links"
    )
    question = models.ForeignKey(Question, on_delete=models.PROTECT)
    position = models.PositiveIntegerField()

    class Meta:
        ordering = ["position", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["quiz", "question"], name="quiz_question_unique"
            ),
            models.UniqueConstraint(
                fields=["quiz", "position"], name="quiz_position_unique"
            ),
        ]


class ImportSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    quiz = models.ForeignKey("quizzes.Quiz", on_delete=models.CASCADE)
    rows = models.JSONField(default=list)
    errors = models.JSONField(default=list)
    expires_at = models.DateTimeField()
    confirmed = models.BooleanField(default=False)
