from django.core.files.base import ContentFile
from rest_framework import serializers

from .images import normalize_image
from .models import Question


class QuestionSerializer(serializers.ModelSerializer):
    remove_image = serializers.BooleanField(
        write_only=True, required=False, default=False
    )
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            "id",
            "owner",
            "text",
            "subject",
            "options",
            "correct_option",
            "points",
            "image",
            "image_url",
            "remove_image",
            "created_at",
        ]
        read_only_fields = ["owner", "created_at"]
        extra_kwargs = {"image": {"write_only": True, "required": False}}

    def get_image_url(self, obj):
        return f"/api/questions/{obj.pk}/image/" if obj.image else None

    def validate_options(self, value):
        if (
            not isinstance(value, list)
            or len(value) != 4
            or not all(
                isinstance(x, str) and x.strip() and len(x) <= 2000 for x in value
            )
        ):
            raise serializers.ValidationError("To‘rtta javob variantini kiriting.")
        return value

    def validate_image(self, value):
        if not value:
            return value
        value.seek(0)
        return ContentFile(
            normalize_image(value.read(5 * 1024 * 1024 + 1)), name="image.png"
        )

    def update(self, instance, validated_data):
        remove = validated_data.pop("remove_image", False)
        if remove:
            instance.image = ""
        return super().update(instance, validated_data)

    def create(self, validated_data):
        validated_data.pop("remove_image", None)
        return super().create(validated_data)
