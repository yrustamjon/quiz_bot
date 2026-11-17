import os
os.environ.setdefault('DJANGO_SECRET_KEY', 'test-only-key-not-for-deployment-1234567890')
os.environ.setdefault('DJANGO_DEBUG', 'true')
import pytest
from django.core.cache import cache
from rest_framework.test import APIClient
from apps.accounts.models import User

@pytest.fixture(autouse=True)
def clean_cache(db):
    cache.clear()

@pytest.fixture
def teacher(db):
    return User.objects.create_user(username='teacher', password='Strong-Password-987', role='TEACHER', full_name='Test Teacher')

@pytest.fixture
def other(db):
    return User.objects.create_user(username='other', password='Strong-Password-987', role='TEACHER')

@pytest.fixture
def admin(db):
    return User.objects.create_superuser(username='admin', password='Strong-Password-987')

@pytest.fixture
def client(teacher):
    c = APIClient(); c.force_login(teacher); return c
