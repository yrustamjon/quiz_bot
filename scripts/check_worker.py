"""Verify a real broker/worker roundtrip and that the worker loaded current source.

Use after starting/restarting the native worker. An alive PID or a broker ping
alone does not establish that the worker is running the deployed code.
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()
from celery.exceptions import CeleryError
from config.celery import runtime_health
from config.runtime import source_fingerprint
from kombu.exceptions import OperationalError as BrokerError
from redis.exceptions import RedisError


def main():
    try:
        reply = runtime_health.delay().get(timeout=15)
        if reply.get("source_fingerprint") != source_fingerprint():
            raise RuntimeError("Worker source is stale; restart the worker.")
    except (CeleryError, BrokerError, RedisError, OSError, RuntimeError) as error:
        # Connection exceptions may contain credential-bearing broker URLs.
        print("Worker verification failed:", type(error).__name__)
        print("Check worker logs and restart it with current source before retrying.")
        return 1
    print(
        "Real worker roundtrip and loaded-source fingerprint passed; PID", reply["pid"]
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
