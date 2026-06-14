"""Typed data structures crossing the engine boundary (brief §4, §10).

The engine takes ``CircuitInput`` + ``EngineConfig`` and returns ``EngineResult``.
No pandas/numpy types leak across this boundary; everything here is plain
dataclasses that pydantic schemas can serialise directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CircuitInput:
    """One circuit's parsed series, already column-resolved by ingestion."""

    filename: str
    circuit_name: str
    load_type: str
    # ISO-8601 timestamp strings (with offset) OR python datetimes; the engine
    # normalises. One entry per reading.
    timestamps: list
    # cv mode: average current (A). energy mode: energy (kWh) per reading.
    value: list[float]
    # Line-to-line voltage (V) per reading; None in energy-direct mode.
    voltage: list[float] | None = None


@dataclass
class EngineConfig:
    mode: str = "cv"  # "cv" | "energy"
    occupied_start_hour: int = 7
    occupied_end_hour: int = 18
    working_days: list[str] = field(default_factory=lambda: ["Mon", "Tue", "Wed", "Thu", "Fri"])
    tariff_low: float = 11.0
    tariff_mid: float = 12.0
    tariff_high: float = 13.0
    tariff_currency: str = "INR"
    tariff_unit: str = "per kWh"
    emission_factor_tco2_per_mwh: float = 0.7117
    enable_cooling_split: bool = False  # §5.9 stretch, off for acceptance


@dataclass
class Band:
    """A low/mid/high range produced by the three PF bands."""

    low: float
    mid: float
    high: float


@dataclass
class CircuitResult:
    filename: str
    circuit_name: str
    load_type: str
    kwh: Band
    median_voltage: float
    voltage_substituted: bool
    excluded_from_totals: bool
    row_count: int


@dataclass
class HourlyProfile:
    """Mean total building load (kW, mid PF) by hour of day, 0..23."""

    working_days: list[float]
    off_days: list[float]


@dataclass
class LoadMixEntry:
    load_type: str
    kwh: float
    share: float  # fraction of total (excl. solar), mid PF


@dataclass
class EngineResult:
    # Headlines (mid PF unless a Band is given)
    total_kwh: Band
    average_load_kw: float
    baseload_kw: float
    peak_kw: float
    interval_hours: float
    period_days: float

    unoccupied_share: float  # fraction of total kWh
    unoccupied_weekday_offhours_share: float
    unoccupied_weekend_share: float

    hourly_profile: HourlyProfile
    load_mix: list[LoadMixEntry]
    circuits: list[CircuitResult]
    solar: list[CircuitResult]

    # Cost / carbon
    period_cost: Band
    annual_cost: Band
    period_carbon_tco2: float
    annual_carbon_tco2: float
    recoverable_cost_low: float
    recoverable_cost_high: float
    recoverable_carbon_low: float
    recoverable_carbon_high: float

    assumptions: dict
    flags: list[dict]
