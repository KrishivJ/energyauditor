"""Ingestion + per-file column-detection tests (brief §10).

Includes the frequency-shift case explicitly: a file with a Frequency column
must detect its voltage one position to the right of a file without one.
"""

from __future__ import annotations

from app.ingestion import detect
from app.ingestion.parse import clean_circuit_name, parse_file
from tests.synth import build_dataset

DATASET = build_dataset()
BY_NAME = {fn: content for fn, content in DATASET}


def _file(substr: str):
    for fn, content in DATASET:
        if substr in fn:
            return fn, content
    raise KeyError(substr)


def test_header_row_detected_at_row_four():
    fn, content = _file("HVAC Chiller 1")
    res = parse_file(fn, content, mode="cv")
    assert res.header_row == 3  # 0-based row 4


def test_frequency_shifts_voltage_column():
    """The §7 regression guard: per-file detection, not a global index."""
    freq_fn, freq_content = _file("HVAC Chiller 1")  # has frequency
    plain_fn, plain_content = _file("Lighting 1")  # no frequency
    freq = parse_file(freq_fn, freq_content, mode="cv")
    plain = parse_file(plain_fn, plain_content, mode="cv")
    # voltage column index is further right in the frequency file
    assert freq.detected_cols["voltage"] == plain.detected_cols["voltage"] + 1
    # both still resolve to a real ~415 V channel, not undercounted
    assert freq.circuit is not None and plain.circuit is not None


def test_avg_current_excludes_phase_columns():
    fn, content = _file("HVAC Chiller 1")
    res = parse_file(fn, content, mode="cv")
    # avg current is column C (index 2), not the per-phase B/R/Y columns
    assert res.detected_cols["value"] == 2


def test_all_circuits_parse():
    parsed = [parse_file(fn, content, mode="cv") for fn, content in DATASET]
    assert len(parsed) == 21
    assert all(p.circuit is not None for p in parsed)
    assert all(p.row_count == 712 for p in parsed)


def test_override_wins_over_detection():
    fn, content = _file("Lighting 1")
    res = parse_file(fn, content, mode="cv", override={"value": 5})
    assert res.detected_cols["value"] == 5


def test_circuit_name_from_filename():
    assert clean_circuit_name("TRF1_HVAC_Chiller_1.xlsx") == "TRF1 HVAC Chiller 1"
    assert clean_circuit_name("E-block Power & HVAC.csv") == "E-block Power & HVAC"


def test_header_detection_helpers():
    rows = [["Meter Report"], ["Bldg"], [], ["Sl No", "Timestamp", "Current (A)(avg)"]]
    assert detect.detect_header_row(rows) == 3
