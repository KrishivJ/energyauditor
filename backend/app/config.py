"""Runtime configuration via environment variables (brief §10).

Sensible local defaults; no secrets in the repo.
"""

from __future__ import annotations

import os
from pathlib import Path

# Repo-local data dir for the SQLite file and uploaded meter files.
_DATA_DIR = Path(os.environ.get("BEL_DATA_DIR", Path(__file__).resolve().parent.parent / "data"))
_DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL: str = os.environ.get("BEL_DATABASE_URL", f"sqlite:///{_DATA_DIR / 'app.db'}")
STORAGE_DIR: Path = Path(os.environ.get("BEL_STORAGE_DIR", _DATA_DIR / "uploads"))
# Comma-separated allowed CORS origins for the Vite dev server.
CORS_ORIGINS: list[str] = os.environ.get(
    "BEL_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
).split(",")

MAX_UPLOAD_MB: int = int(os.environ.get("BEL_MAX_UPLOAD_MB", "25"))
ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".csv"}

# --- Supabase (Stage 2: auth + Postgres + storage) ---------------------------
# All optional: with none set, the app runs locally on SQLite + local-disk
# storage and auth must be overridden (tests do this). In production the backend
# verifies Supabase-issued JWTs and stores uploads in a private Supabase bucket.
SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "").rstrip("/")
# HS256 verification secret (Settings → API → JWT Secret). Primary verify path.
SUPABASE_JWT_SECRET: str = os.environ.get("SUPABASE_JWT_SECRET", "")
SUPABASE_ANON_KEY: str = os.environ.get("SUPABASE_ANON_KEY", "")
# Server-only key (never shipped to the browser); used for Storage access.
SUPABASE_SERVICE_ROLE_KEY: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_STORAGE_BUCKET: str = os.environ.get("SUPABASE_STORAGE_BUCKET", "meter-files")
