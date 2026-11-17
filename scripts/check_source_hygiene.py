"""Reject accidentally tracked runtime data or recognizable credential material.

Reports paths only, never matching secret values. This complements code review
and dependency/security tests; it is not a general-purpose secret detector.
"""

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATTERNS = [
    re.compile(rb"\b\d{8,12}:[A-Za-z0-9_-]{30,}\b"),
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"\bAKIA[A-Z0-9]{16}\b"),
]
FORBIDDEN_PARTS = {"node_modules", ".venv", "artifacts", "test-results"}


def main():
    output = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
    )
    failures = []
    for name in sorted(set(output.decode().split("\0")) - {""}):
        path = Path(name)
        forbidden = (
            path.name == ".env"
            or ".sqlite3" in path.name
            or bool(set(path.parts) & FORBIDDEN_PARTS)
            or name.startswith(("backend/media/", "frontend/dist/"))
        )
        absolute = ROOT / path
        if (
            forbidden
            or absolute.is_file()
            and any(pattern.search(absolute.read_bytes()) for pattern in PATTERNS)
        ):
            failures.append(name)
    if failures:
        print("Review prohibited runtime files or credential material in:")
        print("\n".join(failures))
        raise SystemExit(1)
    print("Source hygiene passed: no prohibited runtime files or recognized secrets.")


if __name__ == "__main__":
    main()
