from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import StudentProfile, Group
User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name', 'specialty', 'role', 'is_active', 'must_change_password', 'created_at']
        read_only_fields = ['role', 'must_change_password', 'created_at']
    def validate_username(self, value):
        qs = User.objects.filter(username__iexact=value)
        if self.instance: qs = qs.exclude(pk=self.instance.pk)
        if qs.exists(): raise serializers.ValidationError('Bu login band.')
        return value
    def validate_email(self, value):
        qs = User.objects.filter(email__iexact=value)
        if self.instance: qs = qs.exclude(pk=self.instance.pk)
        if value and qs.exists(): raise serializers.ValidationError('Bu email band.')
        return value
    def validate_full_name(self, value):
        if len(value.strip()) < 3: raise serializers.ValidationError('To‘liq ismni kiriting.')
        return value.strip()

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = ['id', 'full_name', 'telegram_username', 'is_active', 'registered_at']

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name', 'students']
