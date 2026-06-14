"""Pydantic v2 request/response schemas — the API contract (brief §4, §10)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from ..engine.types import (
    Band,
    CircuitResult,
    EngineConfig,
    EngineResult,
    HourlyProfile,
    LoadMixEntry,
)


# --- request: AnalysisConfig (brief §4) --------------------------------------
class TariffIn(BaseModel):
    low: float = 11
    mid: float = 12
    high: float = 13
    currency: str = "INR"
    unit: str = "per kWh"


class ColumnOverride(BaseModel):
    timestamp: int | None = None
    value: int | None = None
    voltage: int | None = None
    headerRow: int | None = None


class AnalysisConfig(BaseModel):
    mode: str = "cv"  # "cv" | "energy"
    columnOverrides: dict[str, ColumnOverride] = Field(default_factory=dict)
    occupiedStartHour: int = 7
    occupiedEndHour: int = 18
    workingDays: list[str] = Field(default_factory=lambda: ["Mon", "Tue", "Wed", "Thu", "Fri"])
    tariff: TariffIn = Field(default_factory=TariffIn)
    emissionFactorTco2PerMwh: float = 0.7117

    def to_engine_config(self) -> EngineConfig:
        return EngineConfig(
            mode=self.mode,
            occupied_start_hour=self.occupiedStartHour,
            occupied_end_hour=self.occupiedEndHour,
            working_days=self.workingDays,
            tariff_low=self.tariff.low,
            tariff_mid=self.tariff.mid,
            tariff_high=self.tariff.high,
            tariff_currency=self.tariff.currency,
            tariff_unit=self.tariff.unit,
            emission_factor_tco2_per_mwh=self.emissionFactorTco2PerMwh,
        )


# --- response pieces ----------------------------------------------------------
class FileMeta(BaseModel):
    filename: str
    circuitName: str
    loadType: str
    rowCount: int
    startTs: str | None = None
    endTs: str | None = None
    detectedCols: dict
    headerRow: int
    warnings: list[str] = Field(default_factory=list)


class UploadResponse(BaseModel):
    analysisId: str
    files: list[FileMeta]
    warnings: list[str] = Field(default_factory=list)


class AnalysisSummary(BaseModel):
    id: str
    name: str
    createdAt: str
    status: str


class BandOut(BaseModel):
    low: float
    mid: float
    high: float

    @classmethod
    def of(cls, b: Band) -> BandOut:
        return cls(low=b.low, mid=b.mid, high=b.high)


class CircuitOut(BaseModel):
    filename: str
    circuitName: str
    loadType: str
    kwh: BandOut
    medianVoltage: float
    voltageSubstituted: bool
    excludedFromTotals: bool
    rowCount: int

    @classmethod
    def of(cls, c: CircuitResult) -> CircuitOut:
        return cls(
            filename=c.filename,
            circuitName=c.circuit_name,
            loadType=c.load_type,
            kwh=BandOut.of(c.kwh),
            medianVoltage=c.median_voltage,
            voltageSubstituted=c.voltage_substituted,
            excludedFromTotals=c.excluded_from_totals,
            rowCount=c.row_count,
        )


class HourlyProfileOut(BaseModel):
    workingDays: list[float]
    offDays: list[float]

    @classmethod
    def of(cls, p: HourlyProfile) -> HourlyProfileOut:
        return cls(workingDays=p.working_days, offDays=p.off_days)


class LoadMixOut(BaseModel):
    loadType: str
    kwh: float
    share: float

    @classmethod
    def of(cls, e: LoadMixEntry) -> LoadMixOut:
        return cls(loadType=e.load_type, kwh=e.kwh, share=e.share)


class ResultsOut(BaseModel):
    totalKwh: BandOut
    averageLoadKw: float
    baseloadKw: float
    peakKw: float
    intervalHours: float
    periodDays: float
    unoccupiedShare: float
    unoccupiedWeekdayOffhoursShare: float
    unoccupiedWeekendShare: float
    hourlyProfile: HourlyProfileOut
    loadMix: list[LoadMixOut]
    circuits: list[CircuitOut]
    solar: list[CircuitOut]
    periodCost: BandOut
    annualCost: BandOut
    periodCarbonTco2: float
    annualCarbonTco2: float
    recoverableCostLow: float
    recoverableCostHigh: float
    recoverableCarbonLow: float
    recoverableCarbonHigh: float
    assumptions: dict
    flags: list[dict]

    @classmethod
    def of(cls, r: EngineResult) -> ResultsOut:
        return cls(
            totalKwh=BandOut.of(r.total_kwh),
            averageLoadKw=r.average_load_kw,
            baseloadKw=r.baseload_kw,
            peakKw=r.peak_kw,
            intervalHours=r.interval_hours,
            periodDays=r.period_days,
            unoccupiedShare=r.unoccupied_share,
            unoccupiedWeekdayOffhoursShare=r.unoccupied_weekday_offhours_share,
            unoccupiedWeekendShare=r.unoccupied_weekend_share,
            hourlyProfile=HourlyProfileOut.of(r.hourly_profile),
            loadMix=[LoadMixOut.of(e) for e in r.load_mix],
            circuits=[CircuitOut.of(c) for c in r.circuits],
            solar=[CircuitOut.of(c) for c in r.solar],
            periodCost=BandOut.of(r.period_cost),
            annualCost=BandOut.of(r.annual_cost),
            periodCarbonTco2=r.period_carbon_tco2,
            annualCarbonTco2=r.annual_carbon_tco2,
            recoverableCostLow=r.recoverable_cost_low,
            recoverableCostHigh=r.recoverable_cost_high,
            recoverableCarbonLow=r.recoverable_carbon_low,
            recoverableCarbonHigh=r.recoverable_carbon_high,
            assumptions=r.assumptions,
            flags=r.flags,
        )


class AnalysisDetail(BaseModel):
    id: str
    name: str
    status: str
    createdAt: str
    config: AnalysisConfig | None = None
    files: list[FileMeta] = Field(default_factory=list)
    results: ResultsOut | None = None


class RunResponse(BaseModel):
    results: ResultsOut


class OkResponse(BaseModel):
    ok: bool = True


class EmissionFactorOut(BaseModel):
    region: str
    factor: float
    unit: str
    source: str
    year: int


class TariffOut(BaseModel):
    id: str
    region: str
    low: float
    mid: float
    high: float
    currency: str
    unit: str
    note: str
