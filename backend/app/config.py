"""Runtime configuration via environment variables (brief §10).

Sensible local defaults; no secrets in the repo.
"""

from __future__ import annotations

import os
from pathlib import Path


def _env(key: str, default: str = "") -> str:
    """Env var with surrounding whitespace stripped.

    Dashboard env editors (Render, etc.) easily introduce stray leading/trailing
    spaces or newlines on paste, which silently break URL/secret parsing.
    """
    return os.environ.get(key, default).strip()


# Repo-local data dir for the SQLite file and uploaded meter files.
_DATA_DIR = Path(os.environ.get("BEL_DATA_DIR", Path(__file__).resolve().parent.parent / "data"))
_DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL: str = _env("BEL_DATABASE_URL", f"sqlite:///{_DATA_DIR / 'app.db'}")
STORAGE_DIR: Path = Path(os.environ.get("BEL_STORAGE_DIR", _DATA_DIR / "uploads"))
# Comma-separated allowed CORS origins for the Vite dev server.
CORS_ORIGINS: list[str] = [
    o.strip()
    for o in _env("BEL_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if o.strip()
]

MAX_UPLOAD_MB: int = int(os.environ.get("BEL_MAX_UPLOAD_MB", "25"))
ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".csv"}

# --- Supabase (Stage 2: auth + Postgres + storage) ---------------------------
# All optional: with none set, the app runs locally on SQLite + local-disk
# storage and auth must be overridden (tests do this). In production the backend
# verifies Supabase-issued JWTs and stores uploads in a private Supabase bucket.
SUPABASE_URL: str = _env("SUPABASE_URL").rstrip("/")
# HS256 verification secret (Settings → API → JWT Secret). Primary verify path.
SUPABASE_JWT_SECRET: str = _env("SUPABASE_JWT_SECRET")
SUPABASE_ANON_KEY: str = _env("SUPABASE_ANON_KEY")
# Server-only key (never shipped to the browser); used for Storage access.
SUPABASE_SERVICE_ROLE_KEY: str = _env("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_STORAGE_BUCKET: str = _env("SUPABASE_STORAGE_BUCKET", "meter-files")
