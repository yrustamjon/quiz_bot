"""Isolated test configuration; file-backed SQLite exercises real write contention."""

import os

os.environ.setdefault(
    "DJANGO_SECRET_KEY", "test-only-key-not-for-deployment-1234567890"
)
from .settings import *

DEBUG = True
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
DATABASES["default"]["TEST"] = {
    "NAME": os.getenv("TEST_DATABASE_NAME", "/tmp/quiz_bot_tests.sqlite3")
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "isolated-tests",
    }
}

import atexit
import shutil
import tempfile
from pathlib import Path

MEDIA_ROOT = Path(tempfile.mkdtemp(prefix="quiz-bot-unit-media-"))
atexit.register(shutil.rmtree, MEDIA_ROOT, ignore_errors=True)
