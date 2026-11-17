"""Content identity for detecting workers left running after a source update."""

import hashlib
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[2]


def source_fingerprint(root=SOURCE_ROOT):
    digest = hashlib.sha256()
    for folder in ["backend/apps", "backend/config", "bot"]:
        for path in sorted((root / folder).rglob("*.py")):
            digest.update(path.relative_to(root).as_posix().encode())
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()
