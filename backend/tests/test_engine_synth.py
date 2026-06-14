"""Engine correctness on the synthetic dataset (brief §5).

Asserts structural invariants that must hold regardless of the exact (synthetic)
magnitudes: solar exclusion, faulty-voltage substitution, range ordering,
share normalisation, and the cost/carbon relationships.
"""

from __future__ import annotations

import pytest

from app.engine.core import run
from app.engine.types import EngineConfig
from app.ingestion.parse import parse_file
from tests.synth import build_dataset

CONFIG = EngineConfig()  # cv, 07–18, Mon–Fri, Delhi tariff, 0.7117


@pytest.fixture(scope="module")
def result():
    circuits = [parse_file(fn, c, mode="cv").circuit for fn, c in build_dataset()]
    return run([c for c in circuits if c], CONFIG)


def test_solar_excluded_from_totals(result):
    assert len(result.solar) == 1
    assert all(c.load_type != "Solar" for c in result.circuits)
    assert all(c.load_type != "Solar" for c in result.load_mix)


def test_two_faulty_voltage_substitutions(result):
    subs = [f for f in result.flags if f["type"] == "faulty_voltage_substituted"]
    assert len(subs) == 2
    assert any(c.voltage_substituted for c in result.circuits)


def test_total_is_an_ordered_band(result):
    t = result.total_kwh
    assert t.low < t.mid < t.high
    assert t.mid > 0


def test_load_mix_shares_normalise(result):
    assert abs(sum(e.share for e in result.load_mix) - 1.0) < 1e-6


def test_unoccupied_shares_consistent(result):
    assert 0.0 < result.unoccupied_share < 1.0
    combined = result.unoccupied_weekday_offhours_share + result.unoccupied_weekend_share
    assert abs(combined - result.unoccupied_share) < 1e-6


def test_baseload_below_average_below_peak(result):
    assert result.baseload_kw < result.average_load_kw < result.peak_kw


def test_interval_is_hourly(result):
    assert abs(result.interval_hours - 1.0) < 0.01


def test_cost_and_carbon_relationships(result):
    # mid period cost = total mid kWh * mid tariff
    assert result.period_cost.mid == pytest.approx(result.total_kwh.mid * CONFIG.tariff_mid)
    # carbon = mid kWh * factor/1000
    assert result.period_carbon_tco2 == pytest.approx(
        result.total_kwh.mid * CONFIG.emission_factor_tco2_per_mwh / 1000.0
    )
    # annual >= period (extrapolated up to a year)
    assert result.annual_cost.mid >= result.period_cost.mid
    # recoverable is a proper sub-range of the unoccupied envelope
    assert 0 < result.recoverable_cost_low < result.recoverable_cost_high


def test_profiles_are_24_long(result):
    assert len(result.hourly_profile.working_days) == 24
    assert len(result.hourly_profile.off_days) == 24


def test_assumptions_surface_changeable_inputs(result):
    a = result.assumptions
    for key in (
        "mode",
        "occupied_hours",
        "working_days",
        "tariff",
        "emission_factor_tco2_per_mwh",
        "interval_hours",
    ):
        assert key in a
    assert "bill" in a["tariff"]["note"].lower()
