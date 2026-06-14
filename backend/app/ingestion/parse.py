"""File reading + column resolution into engine-ready CircuitInput (brief §5).

Circuit identity comes from the **filename** (lightly cleaned), not the column
headers, because headers are prefixed with the circuit name and are not unique
across files (brief §5.1).
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field

from ..engine.classify import classify_load_type
from ..engine.types import CircuitInput
from . import detect


@dataclass
class FileParseResult:
    filename: str
    circuit_name: str
    load_type: str
    header_row: int
    detected_cols: dict
    row_count: int
    start_ts: str | None
    end_ts: str | None
    warnings: list[str] = field(default_factory=list)
    circuit: CircuitInput | None = None


# --- raw reading -------------------------------------------------------------
def _read_xlsx(content: bytes) -> list[list]:
    from openpyxl import load_workbook

    wb = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    ws = wb.active
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    wb.close()
    return rows


def _read_csv(content: bytes) -> list[list]:
    text = content.decode("utf-8-sig", errors="replace")
    return [row for row in csv.reader(io.StringIO(text))]


def read_rows(filename: str, content: bytes) -> list[list]:
    lower = filename.lower()
    if lower.endswith(".csv"):
        return _read_csv(content)
    return _read_xlsx(content)  # .xlsx / .xls


# --- circuit name from filename ----------------------------------------------
def clean_circuit_name(filename: str) -> str:
    name = re.sub(r"\.(xlsx|xls|csv)$", "", filename, flags=re.IGNORECASE)
    name = re.sub(r"meter\s*report", "", name, flags=re.IGNORECASE)
    name = re.sub(r"[_]+", " ", name)
    name = re.sub(r"\s+", " ", name).strip(" -")
    return name or filename


# --- value coercion ----------------------------------------------------------
def _to_float(cell) -> float:
    if cell is None or cell == "":
        return float("nan")
    if isinstance(cell, (int, float)):
        return float(cell)
    try:
        return float(str(cell).replace(",", "").strip())
    except ValueError:
        return float("nan")


def parse_file(
    filename: str, content: bytes, mode: str = "cv", override: dict | None = None
) -> FileParseResult:
    """Parse one meter file into a FileParseResult (with CircuitInput on success).

    ``override`` (per-file, from AnalysisConfig.columnOverrides) wins over
    auto-detection for any key it specifies: timestamp/value/voltage/headerRow.
    """
    override = override or {}
    warnings: list[str] = []
    rows = read_rows(filename, content)

    header_row = override.get("headerRow")
    if header_row is None:
        header_row = detect.detect_header_row(rows)
    header = rows[header_row] if header_row < len(rows) else []
    data_rows = rows[header_row + 1 :]

    cols = detect.detect_columns(header, data_rows, mode=mode)
    # apply overrides (caller wins)
    for key in ("timestamp", "value", "voltage"):
        if override.get(key) is not None:
            cols[key] = override[key]

    circuit_name = clean_circuit_name(filename)
    load_type = classify_load_type(circuit_name)

    ts_col = cols.get("timestamp")
    val_col = cols.get("value")
    volt_col = cols.get("voltage")

    if ts_col is None:
        warnings.append("Could not detect a timestamp column; set it manually.")
    if val_col is None:
        kind = "energy/kWh" if mode == "energy" else "average-current"
        warnings.append(f"Could not detect the {kind} column; set it manually.")
    if mode == "cv" and volt_col is None:
        warnings.append("Could not detect a line-to-line voltage column; set it manually.")

    timestamps, values, voltages = [], [], []
    for r in data_rows:
        if ts_col is None or ts_col >= len(r):
            continue
        ts = r[ts_col]
        if ts is None or (isinstance(ts, str) and ts.strip() == ""):
            continue
        timestamps.append(str(ts) if not hasattr(ts, "isoformat") else ts.isoformat())
        values.append(
            _to_float(r[val_col]) if (val_col is not None and val_col < len(r)) else float("nan")
        )
        if mode == "cv" and volt_col is not None and volt_col < len(r):
            voltages.append(_to_float(r[volt_col]))
        elif mode == "cv":
            voltages.append(float("nan"))

    row_count = len(timestamps)
    circuit = None
    if row_count and ts_col is not None and val_col is not None:
        circuit = CircuitInput(
            filename=filename,
            circuit_name=circuit_name,
            load_type=load_type,
            timestamps=timestamps,
            value=values,
            voltage=voltages if mode == "cv" else None,
        )

    return FileParseResult(
        filename=filename,
        circuit_name=circuit_name,
        load_type=load_type,
        header_row=header_row,
        detected_cols=cols,
        row_count=row_count,
        start_ts=timestamps[0] if timestamps else None,
        end_ts=timestamps[-1] if timestamps else None,
        warnings=warnings,
        circuit=circuit,
    )
