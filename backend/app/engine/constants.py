"""Centralised domain constants for the analysis engine (brief §5, §6).

Every magic number that drives a reported figure lives here so the assumptions
are inspectable in one place. Nothing in this module does I/O.
"""

from __future__ import annotations

# --- Power-factor bands per load type (low / mid / high) --- brief §5.3 -------
# Running all three produces ranges; reported totals are bands, never single
# false-precise numbers (brief §8).
PF_BANDS: dict[str, tuple[float, float, float]] = {
    "HVAC": (0.80, 0.85, 0.88),
    "Lighting": (0.85, 0.90, 0.95),
    "General Power": (0.85, 0.90, 0.95),  # also the default for unrecognised
    "UPS": (0.90, 0.93, 0.96),
    "Lift": (0.78, 0.83, 0.88),
    "Ventilation": (0.75, 0.80, 0.85),
    # Solar is excluded from totals; bands are irrelevant but kept for symmetry.
    "Solar": (0.90, 0.95, 1.00),
}
DEFAULT_LOAD_TYPE = "General Power"

# --- Load-type classification from circuit name --- brief §5.4 ----------------
# Ordered list of (regex, load_type); FIRST hit wins, case-insensitive.
LOAD_TYPE_RULES: list[tuple[str, str]] = [
    (r"SOLAR", "Solar"),
    (r"UPS", "UPS"),
    (r"HVAC|CHILL|AHU|COOL|RAMP", "HVAC"),
    (r"VENT|FAN", "Ventilation"),
    (r"LIFT|ELEVAT", "Lift"),
    (r"LIGH|LIGT|LAMP", "Lighting"),
    (r"POWER", "General Power"),
]

# Load type reported separately and EXCLUDED from building totals (brief §5.4).
EXCLUDED_FROM_TOTALS = {"Solar"}

# --- Faulty-voltage handling --- brief §5.5 -----------------------------------
# A circuit whose median V_LL is below this fraction of the building-wide healthy
# median is treated as a bad voltage channel (e.g. logging line-to-neutral or a
# dead channel); its voltage is substituted with the healthy median and flagged.
# The current channel on such meters is usually fine, so only voltage is touched.
FAULTY_VOLTAGE_FRACTION = 0.60

# --- Occupied-hours model defaults --- brief §5.6 -----------------------------
DEFAULT_OCCUPIED_START_HOUR = 7
DEFAULT_OCCUPIED_END_HOUR = 18
DEFAULT_WORKING_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]
WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]  # 0=Mon

# --- Baseload --- brief §5.7 --------------------------------------------------
# Deep-night window [start, end) in hours of day; mean total load here is the
# always-on floor. 01:00–04:00 -> hours 1, 2, 3.
BASELOAD_START_HOUR = 1
BASELOAD_END_HOUR = 4

# --- Cost / carbon --- brief §5.8 ---------------------------------------------
DAYS_PER_YEAR = 365
# Fraction of unoccupied energy realistically recoverable (range, never 100%).
RECOVERABLE_FRACTION_LOW = 0.40
RECOVERABLE_FRACTION_HIGH = 0.60

# --- Reference / display defaults --- brief §6 --------------------------------
DEFAULT_EMISSION_FACTOR_TCO2_PER_MWH = 0.7117  # India CEA v21.0, FY2024-25

# Expected logging interval (h); actual value is detected as the median gap and
# this is only a sanity reference for flagging.
EXPECTED_INTERVAL_HOURS = 1.0
