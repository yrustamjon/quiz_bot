import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
app = Celery("quiz_bot")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Capture once when the worker loads its app, rather than hashing at task time.
# A running worker must not claim fresh code merely because files changed on disk.
from .runtime import source_fingerprint

WORKER_SOURCE_FINGERPRINT = source_fingerprint()


@app.task(name="config.runtime_health")
def runtime_health():
    return {"pid": os.getpid(), "source_fingerprint": WORKER_SOURCE_FINGERPRINT}
