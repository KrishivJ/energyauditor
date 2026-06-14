"""Bundled reference datasets (tariffs, emission factors) loaded at startup."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_DIR = Path(__file__).resolve().parent


@lru_cache
def emission_factors() -> list[dict]:
    return json.loads((_DIR / "emission_factors.json").read_text())


@lru_cache
def tariffs() -> list[dict]:
    return json.loads((_DIR / "tariffs.json").read_text())
