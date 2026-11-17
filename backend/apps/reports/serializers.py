from rest_framework import serializers

from apps.attempts.models import Attempt


class ResultSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    quiz_title = serializers.CharField(source="quiz.title", read_only=True)

    class Meta:
        model = Attempt
        fields = [
            "id",
            "quiz",
            "quiz_title",
            "student",
            "student_name",
            "number",
            "status",
            "started_at",
            "deadline",
            "finished_at",
            "correct",
            "incorrect",
            "unanswered",
            "earned",
            "maximum",
            "percentage",
            "elapsed_seconds",
        ]
