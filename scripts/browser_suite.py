"""Run real browser checks against an isolated database and disposable accounts.

Usage: .venv/bin/python scripts/browser_suite.py
Requires installed Python/npm dependencies and Chromium or CHROMIUM_PATH.
Production/user databases and media are never used.
"""

import argparse
import os
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BROWSER_SCRIPTS = [
    "browser-check.mjs",
    "panel-check.mjs",
    "integration-check.mjs",
    "management-check.mjs",
    "accessibility-check.mjs",
]


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_ready(url, process):
    for _ in range(100):
        if process.poll() is not None:
            raise RuntimeError("Service exited during browser setup.")
        try:
            with urllib.request.urlopen(url, timeout=1):
                return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError("Browser service readiness timed out.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scripts", nargs="+", choices=BROWSER_SCRIPTS, default=BROWSER_SCRIPTS
    )
    args = parser.parse_args()
    artifacts = Path(
        os.getenv("QUIZ_ARTIFACT_DIR", ROOT.parent / "artifacts" / "e2e")
    ).resolve()
    artifacts.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="quiz-bot-e2e-") as temp:
        workspace = Path(temp)
        backend_port = free_port()
        front_port = free_port()
        env = {
            **os.environ,
            "DJANGO_SECRET_KEY": secrets.token_urlsafe(48),
            "DJANGO_DEBUG": "true",
            "DJANGO_ALLOWED_HOSTS": "127.0.0.1,localhost",
            "DATABASE_URL": "sqlite:///" + str(workspace / "db.sqlite3"),
            "MEDIA_ROOT": str(workspace / "media"),
            "QUIZ_ARTIFACT_DIR": str(workspace / "artifacts"),
            "QUIZ_BASE_URL": f"http://127.0.0.1:{front_port}",
            "BACKEND_URL": f"http://127.0.0.1:{backend_port}",
            "VITE_PORT": str(front_port),
            "QUIZ_E2E_FIXTURES": "1",
            "CELERY_TASK_DEFAULT_QUEUE": "quiz-e2e-" + secrets.token_hex(12),
            "CELERY_RESULT_BACKEND": "redis://127.0.0.1:6379/4",
            "PYTHONPATH": str(ROOT / "backend"),
        }
        if not env.get("CHROMIUM_PATH"):
            for candidate in [
                "/usr/bin/chromium",
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            ]:
                if Path(candidate).exists():
                    env["CHROMIUM_PATH"] = candidate
                    break

        def run(command):
            subprocess.run(command, cwd=ROOT, env=env, check=True)

        run([sys.executable, "backend/manage.py", "migrate", "--noinput"])
        run([sys.executable, "scripts/create_e2e_fixtures.py"])
        processes = []
        try:
            with (
                (workspace / "backend.log").open("w") as backend_log,
                (workspace / "frontend.log").open("w") as frontend_log,
                (workspace / "worker.log").open("w") as worker_log,
            ):
                processes.append(
                    subprocess.Popen(
                        [
                            sys.executable,
                            "backend/manage.py",
                            "runserver",
                            f"127.0.0.1:{backend_port}",
                            "--noreload",
                        ],
                        cwd=ROOT,
                        start_new_session=True,
                        env=env,
                        stdout=backend_log,
                        stderr=subprocess.STDOUT,
                    )
                )
                processes.append(
                    subprocess.Popen(
                        [
                            "npm",
                            "run",
                            "dev",
                            "--",
                            "--port",
                            str(front_port),
                            "--strictPort",
                        ],
                        cwd=ROOT / "frontend",
                        start_new_session=True,
                        env=env,
                        stdout=frontend_log,
                        stderr=subprocess.STDOUT,
                    )
                )
                wait_ready(
                    f"http://127.0.0.1:{backend_port}/api/auth/csrf/", processes[0]
                )
                wait_ready(env["QUIZ_BASE_URL"], processes[1])
                processes.append(
                    subprocess.Popen(
                        [
                            sys.executable,
                            "-m",
                            "celery",
                            "-A",
                            "config",
                            "worker",
                            "--pool=solo",
                            "--concurrency=1",
                            "--loglevel=INFO",
                            "--hostname=" + env["CELERY_TASK_DEFAULT_QUEUE"],
                        ],
                        cwd=ROOT,
                        start_new_session=True,
                        env=env,
                        stdout=worker_log,
                        stderr=subprocess.STDOUT,
                    )
                )
                for _ in range(100):
                    if processes[-1].poll() is not None:
                        raise RuntimeError("Isolated Celery worker exited.")
                    if " ready." in (workspace / "worker.log").read_text():
                        break
                    time.sleep(0.2)
                else:
                    raise RuntimeError("Isolated Celery worker readiness timed out.")
                for script in args.scripts:
                    run(["node", str(ROOT / "frontend" / script)])
        finally:
            for process in reversed(processes):
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
            for file in (workspace / "artifacts").glob("*"):
                if file.name not in ["ui-identity.json", "ui-admin.json"]:
                    shutil.copy2(file, artifacts / file.name)
    print("Isolated browser suite passed. Screenshots/reports:", artifacts)


if __name__ == "__main__":
    main()
