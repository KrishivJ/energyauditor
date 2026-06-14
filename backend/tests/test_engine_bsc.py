"""BSC acceptance fixture — the correctness gate (brief §7).

Loads the 21 real BSC meter files from ``backend/fixtures/bsc/`` plus
``expected_outputs.json`` and asserts each headline within tolerance.

The real files are proprietary and supplied by the project owner. When they are
absent this test SKIPS with a clear message, so CI is green pre-drop and becomes
a hard gate the moment the files land. Drop the 21 files + expected_outputs.json
into ``backend/fixtures/bsc/`` to activate it (see the README there).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.engine.core import run
from app.engine.types import EngineConfig
from app.ingestion.parse import parse_file

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "bsc"
EXPECTED_PATH = FIXTURE_DIR / "expected_outputs.json"
DATA_GLOBS = ("*.xlsx", "*.xls", "*.csv")


def _meter_files() -> list[Path]:
    files: list[Path] = []
    for g in DATA_GLOBS:
        files += sorted(FIXTURE_DIR.glob(g))
    return files


pytestmark = pytest.mark.skipif(
    not EXPECTED_PATH.exists() or len(_meter_files()) < 21,
    reason=(
        "BSC fixture not present. Drop the 21 meter files + "
        "expected_outputs.json into backend/fixtures/bsc/ to activate the "
        "acceptance gate (see fixtures/bsc/README.md)."
    ),
)


def _config_from(spec: dict) -> EngineConfig:
    c = spec.get("config", {})
    t = c.get("tariff", {})
    return EngineConfig(
        mode=c.get("mode", "cv"),
        occupied_start_hour=c.get("occupiedStartHour", 7),
        occupied_end_hour=c.get("occupiedEndHour", 18),
        working_days=c.get("workingDays", ["Mon", "Tue", "Wed", "Thu", "Fri"]),
        tariff_low=t.get("low", 11),
        tariff_mid=t.get("mid", 12),
        tariff_high=t.get("high", 13),
        emission_factor_tco2_per_mwh=c.get("emissionFactorTco2PerMwh", 0.7117),
    )


@pytest.fixture(scope="module")
def outcome():
    spec = json.loads(EXPECTED_PATH.read_text())
    cfg = _config_from(spec)
    circuits = []
    for p in _meter_files():
        res = parse_file(p.name, p.read_bytes(), mode=cfg.mode)
        if res.circuit:
            circuits.append(res.circuit)
    return run(circuits, cfg), spec.get("expected", {}), spec.get("tolerances", {})


def _rel(actual, expected, pct):
    assert abs(actual - expected) <= abs(expected) * pct, f"{actual} vs {expected} (±{pct:.0%})"


def test_total_energy_within_band(outcome):
    result, exp, tol = outcome
    if "total_kwh_band" in exp:
        lo, hi = exp["total_kwh_band"]
        assert lo <= result.total_kwh.mid <= hi
    if "total_kwh_mid" in exp:
        _rel(result.total_kwh.mid, exp["total_kwh_mid"], tol.get("total_kwh_pct", 0.01))


def test_load_and_baseload(outcome):
    result, exp, tol = outcome
    pct = tol.get("load_pct", 0.05)
    if "average_load_kw" in exp:
        _rel(result.average_load_kw, exp["average_load_kw"], pct)
    if "baseload_kw" in exp:
        _rel(result.baseload_kw, exp["baseload_kw"], pct)
    if "peak_kw" in exp:
        _rel(result.peak_kw, exp["peak_kw"], pct)


def test_unoccupied_shares(outcome):
    result, exp, tol = outcome
    abs_tol = tol.get("share_abs", 0.03)
    for key, actual in (
        ("unoccupied_share", result.unoccupied_share),
        ("unoccupied_weekday_offhours_share", result.unoccupied_weekday_offhours_share),
        ("unoccupied_weekend_share", result.unoccupied_weekend_share),
    ):
        if key in exp:
            assert abs(actual - exp[key]) <= abs_tol, f"{key}: {actual} vs {exp[key]}"


def test_load_mix(outcome):
    result, exp, tol = outcome
    abs_tol = tol.get("share_abs", 0.03)
    mix = {e.load_type: e.share for e in result.load_mix}
    for lt, share in exp.get("load_mix", {}).items():
        assert abs(mix.get(lt, 0.0) - share) <= abs_tol, f"{lt}: {mix.get(lt)} vs {share}"


def test_flags_and_exclusions(outcome):
    result, exp, _ = outcome
    if "faulty_voltage_count" in exp:
        subs = [f for f in result.flags if f["type"] == "faulty_voltage_substituted"]
        assert len(subs) == exp["faulty_voltage_count"]
    if "solar_excluded_count" in exp:
        assert len(result.solar) == exp["solar_excluded_count"]


def test_cost_and_carbon(outcome):
    result, exp, tol = outcome
    pct = tol.get("cost_pct", 0.02)
    if "period_cost_mid" in exp:
        _rel(result.period_cost.mid, exp["period_cost_mid"], pct)
    if "period_carbon_tco2" in exp:
        _rel(result.period_carbon_tco2, exp["period_carbon_tco2"], pct)
