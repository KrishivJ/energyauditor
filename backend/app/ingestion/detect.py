"""Per-file header-row and column detection (brief §5.1, §5.2).

Columns are detected **per file** using that file's own header row. This is the
documented pitfall: the four TRF1 files that log frequency shift the voltage
column one position right, so a single global index undercounts the total by
~a third. Detection here is independent per file.
"""

from __future__ import annotations

import re

HEADER_HINT = re.compile(r"current|voltage|energy|power", re.IGNORECASE)
TIMESTAMP_HINT = re.compile(r"time|date|stamp", re.IGNORECASE)
PHASE_HINT = re.compile(r"\bB\b|\bR\b|\bY\b|phase", re.IGNORECASE)
CURRENT_HINT = re.compile(r"current", re.IGNORECASE)
AVG_HINT = re.compile(r"avg|aver", re.IGNORECASE)
ENERGY_HINT = re.compile(r"kwh|energy", re.IGNORECASE)
VOLT_LL_HINT = re.compile(r"ll.*aver|line.?to.?line|voltage.*ll", re.IGNORECASE)
VOLT_LL_FALLBACK = re.compile(r"\bll\b", re.IGNORECASE)

_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}")


def _is_nonempty_str(cell) -> bool:
    return isinstance(cell, str) and cell.strip() != ""


def _looks_like_date(cell) -> bool:
    if cell is None:
        return False
    if hasattr(cell, "year") and hasattr(cell, "month"):  # datetime
        return True
    return bool(_DATE_RE.search(str(cell)))


def detect_header_row(rows: list[list], scan: int = 12) -> int:
    """First row (within ``scan``) whose cells include an energy-domain header;
    else the first row with >= 3 non-empty string cells. Defaults to 0.

    A real header row carries several labelled columns, so the keyword branch
    also requires >= 2 non-empty cells — this prevents a single-cell title row
    (e.g. a building name that happens to contain "Power") from being mistaken
    for the header."""
    limit = min(scan, len(rows))
    for i in range(limit):
        cells = rows[i]
        nonempty = [c for c in cells if _is_nonempty_str(c)]
        if len(nonempty) >= 2 and any(HEADER_HINT.search(c) for c in nonempty):
            return i
    for i in range(limit):
        if sum(1 for c in rows[i] if _is_nonempty_str(c)) >= 3:
            return i
    return 0


def _find(header: list, pattern: re.Pattern, exclude: re.Pattern | None = None) -> int | None:
    for j, cell in enumerate(header):
        if not _is_nonempty_str(cell):
            continue
        if pattern.search(cell) and not (exclude and exclude.search(cell)):
            return j
    return None


def detect_timestamp_col(header: list, data_rows: list[list]) -> int | None:
    j = _find(header, TIMESTAMP_HINT)
    if j is not None:
        return j
    # else: the column whose data parses as dates
    if data_rows:
        ncols = len(header)
        for col in range(ncols):
            hits = sum(1 for r in data_rows[:10] if col < len(r) and _looks_like_date(r[col]))
            if hits >= 3:
                return col
    return None


def detect_current_col(header: list) -> int | None:
    # header matching `current` AND avg/aver, excluding per-phase columns
    for j, cell in enumerate(header):
        if (
            _is_nonempty_str(cell)
            and CURRENT_HINT.search(cell)
            and AVG_HINT.search(cell)
            and not PHASE_HINT.search(cell)
        ):
            return j
    # fallback: any current that is not a phase column
    return _find(header, CURRENT_HINT, exclude=PHASE_HINT)


def detect_energy_col(header: list) -> int | None:
    return _find(header, ENERGY_HINT)


def detect_voltage_ll_col(header: list) -> int | None:
    j = _find(header, VOLT_LL_HINT)
    if j is not None:
        return j
    return _find(header, VOLT_LL_FALLBACK)


def detect_columns(header: list, data_rows: list[list], mode: str = "cv") -> dict:
    """Return detected 0-based column indices for one file.

    Keys: ``timestamp``, and either ``value`` (cv: avg current) or ``energy``,
    plus ``voltage`` (cv only). ``None`` where detection failed (caller falls
    back to the user's manual override for that file)."""
    cols: dict[str, int | None] = {"timestamp": detect_timestamp_col(header, data_rows)}
    if mode == "energy":
        cols["value"] = detect_energy_col(header)
        cols["voltage"] = None
    else:
        cols["value"] = detect_current_col(header)
        cols["voltage"] = detect_voltage_ll_col(header)
    return cols
