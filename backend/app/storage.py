"""File-storage interface with local-filesystem and Supabase implementations.

Abstracted behind ``Storage`` (brief §3) so the storage backend can change
without touching the API or ingestion code. Local disk is used for dev/tests;
Supabase Storage (S3-compatible, private bucket) is used in production.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Protocol

import httpx

from .config import (
    STORAGE_DIR,
    SUPABASE_SERVICE_ROLE_KEY,
    SUPABASE_STORAGE_BUCKET,
    SUPABASE_URL,
)


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


class SupabaseStorage:
    """Storage backed by a private Supabase Storage bucket (S3-compatible).

    Object keys are ``{analysis_id}/{filename}``. Since ``analysis_id`` is a UUID
    the key is globally unique, so ``delete_analysis`` needs only the id (no user
    prefix) and the ``Storage`` Protocol stays unchanged. The backend uses the
    service-role key, which bypasses RLS — access control is enforced upstream in
    the API layer, where every query is already scoped to the authenticated user.
    """

    def __init__(self) -> None:
        self.base = f"{SUPABASE_URL}/storage/v1"
        self.bucket = SUPABASE_STORAGE_BUCKET
        self._auth = {"Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"}

    @staticmethod
    def _key(analysis_id: str, filename: str) -> str:
        return f"{_safe(analysis_id)}/{_safe(filename)}"

    def save(self, analysis_id: str, filename: str, content: bytes) -> str:
        key = self._key(analysis_id, filename)
        r = httpx.post(
            f"{self.base}/object/{self.bucket}/{key}",
            headers={
                **self._auth,
                "x-upsert": "true",
                "Content-Type": "application/octet-stream",
            },
            content=content,
            timeout=60.0,
        )
        r.raise_for_status()
        return key

    def read(self, path: str) -> bytes:
        r = httpx.get(f"{self.base}/object/{self.bucket}/{path}", headers=self._auth, timeout=60.0)
        r.raise_for_status()
        return r.content

    def delete_analysis(self, analysis_id: str) -> None:
        prefix = _safe(analysis_id)
        listed = httpx.post(
            f"{self.base}/object/list/{self.bucket}",
            headers=self._auth,
            json={"prefix": prefix, "limit": 1000},
            timeout=60.0,
        )
        listed.raise_for_status()
        keys = [f"{prefix}/{obj['name']}" for obj in listed.json()]
        if not keys:
            return
        deleted = httpx.request(
            "DELETE",
            f"{self.base}/object/{self.bucket}",
            headers={**self._auth, "Content-Type": "application/json"},
            json={"prefixes": keys},
            timeout=60.0,
        )
        deleted.raise_for_status()


def _make_storage() -> Storage:
    if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
        return SupabaseStorage()
    return LocalStorage()


# Local disk for dev/tests; Supabase Storage when configured (production).
storage: Storage = _make_storage()
