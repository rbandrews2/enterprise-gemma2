"""Opaque deployment identity; never includes configuration or secret values."""
import hashlib
import os
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def source_fingerprint():
    root = Path(__file__).parent
    digest = hashlib.sha256()
    paths = list(root.glob('*.py')) + [p for p in (root/'static').rglob('*') if p.is_file()]
    for path in sorted(paths):
        digest.update(path.relative_to(root).as_posix().encode() + b'\0')
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def release_version():
    return hashlib.sha256((source_fingerprint() + ':' + os.getenv('K_REVISION', '')).encode()).hexdigest()[:24]
