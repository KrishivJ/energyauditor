"""Synthetic 21-circuit meter dataset for tests (brief §6, §7 stand-in).

Produces real ``.xlsx`` bytes through the same schema as the BSC files so the
full ingestion path is exercised, including:
  * the frequency-shift quirk — some files carry a Frequency column that pushes
    voltage one position right (the §7 regression the per-file detector guards);
  * two faulty-voltage circuits (median ~230 V vs healthy ~415 V) — §5.5;
  * a solar circuit that must be excluded from totals — §5.4.

This is NOT the proprietary BSC data; it is a representative generator so engine
and detection logic are verifiable without it. Deterministic (seeded).
"""

from __future__ import annotations

import io

import numpy as np

START = np.datetime64("2026-04-01T00:00:00")
N_READINGS = 712
OFFSET = "+05:30"

# (circuit name, has_frequency_col, faulty_voltage, base_current_A, diurnal_amp)
CIRCUITS = [
    ("TRF1 HVAC Chiller 1", True, False, 180, 120),
    ("TRF1 HVAC Chiller 2", True, False, 150, 110),
    ("TRF1 AHU 1", True, False, 60, 40),
    ("TRF1 Power 1", True, True, 70, 25),  # faulty voltage (freq file)
    ("TRF1 Lighting 1", False, False, 40, 35),
    ("TRF1 UPS 1", False, False, 55, 8),
    ("TRF1 Lift 1", False, False, 14, 10),
    ("TRF1 Solar 1", False, False, 90, 80),  # excluded from totals
    ("TRF2 HVAC Cooling 1", False, False, 130, 90),
    ("TRF2 HVAC Cooling 2", False, False, 95, 70),
    ("TRF2 AHU 2", False, False, 45, 30),
    ("TRF2 Ventilation Fan 1", False, False, 8, 4),
    ("TRF2 Power 2", False, False, 85, 40),
    ("TRF2 Power 3", False, False, 75, 35),
    ("TRF2 Power 4", False, False, 65, 30),
    ("TRF2 Lighting 2", False, False, 50, 45),
    ("TRF2 Lighting 3", False, False, 35, 30),
    ("TRF2 UPS 2", False, True, 48, 6),  # faulty voltage
    ("TRF2 Lift 2", False, False, 13, 9),
    ("TRF2 Lift 3", False, False, 11, 8),
    ("TRF2 General Power 5", False, False, 60, 28),
]


def _timestamps() -> list[str]:
    base = START + np.arange(N_READINGS) * np.timedelta64(1, "h")
    return [f"{np.datetime_as_string(t, unit='s')}{OFFSET}" for t in base]


def _current_series(
    rng, base: float, amp: float, hours: np.ndarray, weekdays: np.ndarray
) -> np.ndarray:
    """Occupancy-shaped current: higher 07–18 on weekdays, plus night floor."""
    occupied = (hours >= 7) & (hours < 18) & (weekdays < 5)
    weekend = weekdays >= 5
    shape = np.full(N_READINGS, 0.35)  # night/idle floor fraction
    shape[occupied] = 1.0
    shape[weekend & ~occupied] = 0.30
    noise = rng.normal(1.0, 0.05, N_READINGS)
    return np.clip(base * 0.4 + amp * shape * noise, 0, None)


def build_dataset(seed: int = 7) -> list[tuple[str, bytes]]:
    from openpyxl import Workbook

    rng = np.random.default_rng(seed)
    ts = _timestamps()
    t64 = START + np.arange(N_READINGS) * np.timedelta64(1, "h")
    hours = ((t64 - t64.astype("datetime64[D]")) / np.timedelta64(1, "h")).astype(int)
    # 2026-04-01 is a Wednesday -> weekday index 2
    weekdays = ((np.arange(N_READINGS) // 24) + 2) % 7

    files: list[tuple[str, bytes]] = []
    for name, has_freq, faulty, base, amp in CIRCUITS:
        wb = Workbook()
        ws = wb.active
        ws.append(["Meter Report"])
        ws.append([name])
        ws.append([])
        # header row (row 4)
        header = [
            "Sl No",
            "Timestamp",
            f"{name} Current (A)(avg)",
            f"{name} Current B (A)",
            f"{name} Current R (A)",
            f"{name} Current Y (A)",
        ]
        if has_freq:
            header.append(f"{name} Frequency (Hz)")  # <-- shifts voltage right
        header += [f"{name} Voltage LL (V)(avg)", f"{name} Voltage LN (V)(avg)"]
        ws.append(header)

        cur = _current_series(rng, base, amp, hours, weekdays)
        v_ll = 230.0 if faulty else 415.0  # faulty logs line-to-neutral
        for i in range(N_READINGS):
            row = [
                i + 1,
                ts[i],
                round(cur[i], 2),
                round(cur[i] * 0.99, 2),
                round(cur[i] * 1.01, 2),
                round(cur[i], 2),
            ]
            if has_freq:
                row.append(round(rng.normal(50.0, 0.02), 3))
            row += [
                round(v_ll + rng.normal(0, 1.5), 1),
                round(v_ll / 1.732 + rng.normal(0, 1.0), 1),
            ]
            ws.append(row)

        buf = io.BytesIO()
        wb.save(buf)
        files.append((f"{name}.xlsx", buf.getvalue()))
    return files
