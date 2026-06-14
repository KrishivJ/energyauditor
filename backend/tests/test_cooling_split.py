"""Test the optional §5.9 cooling-split hook (off the acceptance path)."""

from __future__ import annotations

import numpy as np

from app.engine.cooling_split import estimate_hvac_fraction


def test_recovers_known_mix():
    rng = np.random.default_rng(3)
    hvac = np.abs(rng.normal(100, 20, 200))
    power = np.abs(rng.normal(60, 10, 200))
    # combined circuit is 70% hvac + 30% power by these scalings
    combined = 0.7 * hvac + 0.3 * power
    frac = estimate_hvac_fraction(combined, hvac, power)
    assert 0.6 < frac < 0.8


def test_degenerate_inputs_return_zero():
    assert estimate_hvac_fraction(np.array([]), np.array([]), np.array([])) == 0.0
