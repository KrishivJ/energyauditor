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
