from rest_framework import serializers

from .models import Quiz


class QuizSerializer(serializers.ModelSerializer):
    access_code = serializers.SerializerMethodField()

    def get_access_code(self, obj):
        return (
            obj.access_code.code
            if obj.access == "private"
            and hasattr(obj, "access_code")
            and obj.access_code.active
            else None
        )

    owner_name = serializers.SerializerMethodField()
    participants = serializers.IntegerField(read_only=True, default=0)

    def get_owner_name(self, obj):
        return obj.owner.full_name or obj.owner.username

    available_questions = serializers.IntegerField(
        source="question_links.count", read_only=True
    )

    class Meta:
        model = Quiz
        fields = "__all__"
        read_only_fields = [
            "owner",
            "status",
            "results_released",
            "created_at",
            "updated_at",
        ]

    def validate(self, data):
        opens = data.get("opens_at", getattr(self.instance, "opens_at", None))
        closes = data.get("closes_at", getattr(self.instance, "closes_at", None))
        if opens and closes and opens >= closes:
            raise serializers.ValidationError(
                "Yopilish vaqti boshlanishdan keyin bo‘lsin."
            )
        return data
