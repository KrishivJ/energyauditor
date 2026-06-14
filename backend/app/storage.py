"""File-storage interface with a local-filesystem implementation (brief §3).

Abstracted behind ``Storage`` so an S3-compatible backend can replace it in
Stage 2 without touching the API or ingestion code.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Protocol

from .config import STORAGE_DIR


class Storage(Protocol):
    def save(self, analysis_id: str, filename: str, content: bytes) -> str: ...
    def read(self, path: str) -> bytes: ...
    def delete_analysis(self, analysis_id: str) -> None: ...


def _safe(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", name) or "file"


class LocalStorage:
    def __init__(self, root: Path = STORAGE_DIR) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, analysis_id: str, filename: str, content: bytes) -> str:
        d = self.root / _safe(analysis_id)
        d.mkdir(parents=True, exist_ok=True)
        p = d / _safe(filename)
        p.write_bytes(content)
        return str(p)

    def read(self, path: str) -> bytes:
        return Path(path).read_bytes()

    def delete_analysis(self, analysis_id: str) -> None:
        d = self.root / _safe(analysis_id)
        if d.exists():
            for f in d.iterdir():
                f.unlink()
            d.rmdir()


storage: Storage = LocalStorage()
