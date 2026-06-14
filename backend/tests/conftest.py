"""Test setup: point the app at an isolated temp DB + storage dir.

Env must be set before any ``app.*`` import so config/db/storage pick it up,
hence this lives at conftest import time rather than inside a fixture.
"""

from __future__ import annotations

import os
import tempfile

_TMP = tempfile.mkdtemp(prefix="bel-test-")
os.environ.setdefault("BEL_DATA_DIR", _TMP)
os.environ.setdefault("BEL_DATABASE_URL", f"sqlite:///{_TMP}/test.db")
os.environ.setdefault("BEL_STORAGE_DIR", f"{_TMP}/uploads")
