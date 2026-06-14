"""Optional mixed-circuit cooling split (brief §5.9) — STRETCH, off by default.

For a combined power-and-cooling feed (e.g. "E-block Power & HVAC"), estimate its
HVAC fraction by non-negative least squares of its hourly series against the
aggregate pure-HVAC and pure-General-Power hourly series.

This is the *interface hook* the brief asks for. It is intentionally NOT wired
into ``core.run`` — the Stage 1 acceptance numbers assume the simple keyword
classifier (§5.4), and enabling the split changes expected HVAC ~41% -> ~35%.
A caller that opts in (``EngineConfig.enable_cooling_split``) can use this to
apportion a circuit's energy before/after the main run.
"""

from __future__ import annotations

import numpy as np


def estimate_hvac_fraction(
    circuit_hourly: np.ndarray,
    hvac_aggregate_hourly: np.ndarray,
    power_aggregate_hourly: np.ndarray,
) -> float:
    """Return the estimated HVAC fraction (0..1) of a combined circuit.

    Solves ``circuit ≈ a·hvac + b·power`` for non-negative ``a, b`` and reports
    ``a·hvac / (a·hvac + b·power)`` summed over the window. Falls back to 0.0 if
    the inputs are degenerate.
    """
    from scipy.optimize import nnls

    n = min(len(circuit_hourly), len(hvac_aggregate_hourly), len(power_aggregate_hourly))
    if n == 0:
        return 0.0
    a_matrix = np.column_stack(
        [
            np.nan_to_num(hvac_aggregate_hourly[:n]),
            np.nan_to_num(power_aggregate_hourly[:n]),
        ]
    )
    target = np.nan_to_num(circuit_hourly[:n])
    coef, _ = nnls(a_matrix, target)
    hvac_contrib = float(coef[0] * a_matrix[:, 0].sum())
    power_contrib = float(coef[1] * a_matrix[:, 1].sum())
    denom = hvac_contrib + power_contrib
    return hvac_contrib / denom if denom > 0 else 0.0
