import uuid

from django.db import models


class Attempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(
        "quizzes.Quiz", on_delete=models.PROTECT, related_name="attempts"
    )
    student = models.ForeignKey(
        "accounts.StudentProfile", on_delete=models.PROTECT, related_name="attempts"
    )
    number = models.PositiveIntegerField()
    status = models.CharField(
        max_length=16,
        default="in_progress",
        db_index=True,
        choices=[
            ("in_progress", "Jarayonda"),
            ("completed", "Yakunlangan"),
            ("timed_out", "Vaqt tugagan"),
        ],
    )
    navigation = models.CharField(max_length=16)
    cursor = models.PositiveIntegerField(default=0)
    revision = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField()
    deadline = models.DateTimeField(db_index=True)
    finished_at = models.DateTimeField(null=True)
    correct = models.PositiveIntegerField(default=0)
    incorrect = models.PositiveIntegerField(default=0)
    unanswered = models.PositiveIntegerField(default=0)
    earned = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    maximum = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    percentage = models.DecimalField(max_digits=9, decimal_places=6, default=0)
    elapsed_seconds = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "quiz", "number"], name="attempt_number_unique"
            ),
            models.UniqueConstraint(
                fields=["student", "quiz"],
                condition=models.Q(status="in_progress"),
                name="one_active_attempt",
            ),
        ]


class AttemptQuestion(models.Model):
    attempt = models.ForeignKey(
        Attempt, on_delete=models.CASCADE, related_name="questions"
    )
    position = models.PositiveIntegerField()
    text = models.TextField()
    options = models.JSONField()
    correct_option = models.PositiveSmallIntegerField()
    points = models.DecimalField(max_digits=8, decimal_places=2)
    image_name = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(
                fields=["attempt", "position"], name="attempt_position_unique"
            )
        ]


class AttemptAnswer(models.Model):
    question = models.OneToOneField(
        AttemptQuestion, on_delete=models.CASCADE, related_name="answer"
    )
    option = models.PositiveSmallIntegerField()
    submitted_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(option__gte=0, option__lte=3),
                name="answer_valid_option",
            )
        ]
