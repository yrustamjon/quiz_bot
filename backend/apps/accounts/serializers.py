from decimal import ROUND_HALF_UP

from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import serializers

from .models import Group, StudentProfile

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    quiz_count = serializers.SerializerMethodField()

    def get_quiz_count(self, obj):
        return obj.quiz_count if hasattr(obj, "quiz_count") else obj.quizzes.count()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "full_name",
            "specialty",
            "role",
            "is_active",
            "must_change_password",
            "created_at",
            "quiz_count",
        ]
        read_only_fields = ["role", "must_change_password", "created_at"]

    def validate_username(self, value):
        qs = User.objects.filter(Q(username__iexact=value) | Q(email__iexact=value))
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Bu login band.")
        return value

    def validate_email(self, value):
        qs = User.objects.filter(Q(email__iexact=value) | Q(username__iexact=value))
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if value and qs.exists():
            raise serializers.ValidationError("Bu email band.")
        return value

    def validate_full_name(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("To‘liq ismni kiriting.")
        return value.strip()


class StudentSerializer(serializers.ModelSerializer):
    participation_count = serializers.IntegerField(read_only=True)
    average_percentage = serializers.DecimalField(
        max_digits=9,
        decimal_places=2,
        read_only=True,
        allow_null=True,
        rounding=ROUND_HALF_UP,
    )
    last_activity = serializers.DateTimeField(read_only=True, allow_null=True)

    class Meta:
        model = StudentProfile
        fields = [
            "id",
            "full_name",
            "telegram_username",
            "is_active",
            "registered_at",
            "participation_count",
            "average_percentage",
            "last_activity",
        ]


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ["id", "name", "students"]
