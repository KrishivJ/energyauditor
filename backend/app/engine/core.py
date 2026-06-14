"""The analysis engine (brief §5). Pure: no file/DB/network I/O.

``run(circuits, config)`` takes column-resolved per-circuit series + config and
returns an ``EngineResult``. Energy is derived under three power-factor bands so
every total is a range (brief §8). Solar is reported separately and excluded
from building totals.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from . import constants as C
from .types import (
    Band,
    CircuitInput,
    CircuitResult,
    EngineConfig,
    EngineResult,
    HourlyProfile,
    LoadMixEntry,
)

SQRT3 = math.sqrt(3.0)


# --- helpers -----------------------------------------------------------------
def _to_datetime_index(timestamps: list) -> pd.DatetimeIndex:
    idx = pd.to_datetime(pd.Series(timestamps), utc=False, format="mixed")
    return pd.DatetimeIndex(idx)


def _interval_hours(idx: pd.DatetimeIndex) -> float:
    if len(idx) < 2:
        return C.EXPECTED_INTERVAL_HOURS
    diffs = np.diff(idx.view("int64")) / 3.6e12  # ns -> hours
    diffs = diffs[diffs > 0]
    if len(diffs) == 0:
        return C.EXPECTED_INTERVAL_HOURS
    return float(np.median(diffs))


def _occupied_mask(
    hours: np.ndarray, weekdays: np.ndarray, working_idx: set[int], start: int, end: int
) -> np.ndarray:
    """Occupied = weekday in working set AND hour within [start, end) (wrap-aware)."""
    if start <= end:
        in_window = (hours >= start) & (hours < end)
    else:  # overnight window
        in_window = (hours >= start) | (hours < end)
    in_working_day = np.isin(weekdays, list(working_idx))
    return in_window & in_working_day


# --- main entry --------------------------------------------------------------
def run(circuits: list[CircuitInput], config: EngineConfig) -> EngineResult:
    working_idx = {C.WEEKDAY_NAMES.index(d) for d in config.working_days if d in C.WEEKDAY_NAMES}

    # 1. Parse each circuit, compute its own interval and median voltage.
    parsed = []
    for c in circuits:
        idx = _to_datetime_index(c.timestamps)
        value = np.asarray(c.value, dtype=float)
        n = min(len(idx), len(value))
        idx, value = idx[:n], value[:n]
        if config.mode == "cv":
            volt = np.asarray(c.voltage, dtype=float) if c.voltage is not None else None
            if volt is not None:
                volt = volt[:n]
            med_v = float(np.nanmedian(volt)) if volt is not None and len(volt) else float("nan")
        else:
            volt, med_v = None, float("nan")
        parsed.append(
            {
                "circuit": c,
                "idx": idx,
                "value": value,
                "volt": volt,
                "median_voltage": med_v,
                "interval": _interval_hours(idx),
                "load_type": c.load_type,
            }
        )

    # 2. Faulty-voltage detection + substitution (cv mode only) -- §5.5
    flags: list[dict] = []
    if config.mode == "cv":
        all_meds = [p["median_voltage"] for p in parsed if not math.isnan(p["median_voltage"])]
        ref = float(np.median(all_meds)) if all_meds else float("nan")
        faulty = [
            p
            for p in parsed
            if not math.isnan(p["median_voltage"])
            and not math.isnan(ref)
            and p["median_voltage"] < C.FAULTY_VOLTAGE_FRACTION * ref
        ]
        healthy = [
            p["median_voltage"]
            for p in parsed
            if p not in faulty and not math.isnan(p["median_voltage"])
        ]
        healthy_median = float(np.median(healthy)) if healthy else ref
        for p in parsed:
            p["voltage_substituted"] = p in faulty
            if p in faulty:
                p["volt"] = np.full(len(p["idx"]), healthy_median)
                flags.append(
                    {
                        "type": "faulty_voltage_substituted",
                        "circuit": p["circuit"].circuit_name,
                        "filename": p["circuit"].filename,
                        "observed_median_v": round(p["median_voltage"], 1),
                        "substituted_v": round(healthy_median, 1),
                        "message": (
                            f"{p['circuit'].circuit_name}: median voltage "
                            f"{p['median_voltage']:.0f} V implausibly low; "
                            f"substituted healthy median {healthy_median:.0f} V."
                        ),
                    }
                )
    else:
        for p in parsed:
            p["voltage_substituted"] = False

    # 3. Per-reading kWh under each PF band; per-reading kW (mid) for profiles.
    building_interval = (
        float(np.median([p["interval"] for p in parsed])) if parsed else C.EXPECTED_INTERVAL_HOURS
    )
    circuit_results: list[CircuitResult] = []
    solar_results: list[CircuitResult] = []
    # combined kW(mid) per timestamp, non-solar only, for profile/occupancy
    kw_frames: list[pd.Series] = []

    for p in parsed:
        c = p["circuit"]
        lt = p["load_type"]
        pf_low, pf_mid, pf_high = C.PF_BANDS.get(lt, C.PF_BANDS[C.DEFAULT_LOAD_TYPE])
        interval = p["interval"]
        excluded = lt in C.EXCLUDED_FROM_TOTALS

        if config.mode == "cv":
            base = SQRT3 * np.nan_to_num(p["volt"]) * np.nan_to_num(p["value"]) / 1000.0
            kwh_low = float(np.sum(base * pf_low) * interval)
            kwh_mid = float(np.sum(base * pf_mid) * interval)
            kwh_high = float(np.sum(base * pf_high) * interval)
            kw_mid_series = base * pf_mid  # instantaneous kW per reading
        else:  # energy-direct: kWh straight from value, no PF dependence
            kwh = float(np.nansum(p["value"]))
            kwh_low = kwh_mid = kwh_high = kwh
            kw_mid_series = np.nan_to_num(p["value"]) / interval

        cr = CircuitResult(
            filename=c.filename,
            circuit_name=c.circuit_name,
            load_type=lt,
            kwh=Band(kwh_low, kwh_mid, kwh_high),
            median_voltage=(
                round(p["median_voltage"], 1) if not math.isnan(p["median_voltage"]) else 0.0
            ),
            voltage_substituted=p["voltage_substituted"],
            excluded_from_totals=excluded,
            row_count=len(p["idx"]),
        )
        if excluded:
            solar_results.append(cr)
        else:
            circuit_results.append(cr)
            kw_frames.append(pd.Series(kw_mid_series, index=p["idx"]))

    # 4. Combined building timeline (mid PF, non-solar) -- §5.7
    if kw_frames:
        combined = pd.concat(kw_frames, axis=1)
        total_kw = combined.sum(axis=1, skipna=True).sort_index()
    else:
        total_kw = pd.Series(dtype=float)

    ts = pd.DatetimeIndex(total_kw.index)
    hours = ts.hour.to_numpy()
    weekdays = ts.dayofweek.to_numpy()
    n_ts = len(total_kw)
    total_hours = n_ts * building_interval
    period_days = total_hours / 24.0 if total_hours else 0.0

    # diurnal profiles
    df = pd.DataFrame({"kw": total_kw.to_numpy(), "hour": hours, "wd": weekdays})
    is_working_day = np.isin(weekdays, list(working_idx))
    prof_work = (
        df[is_working_day].groupby("hour")["kw"].mean().reindex(range(24)).fillna(0.0).to_list()
    )
    prof_off = (
        df[~is_working_day].groupby("hour")["kw"].mean().reindex(range(24)).fillna(0.0).to_list()
    )

    baseload_mask = (hours >= C.BASELOAD_START_HOUR) & (hours < C.BASELOAD_END_HOUR)
    baseload_kw = float(np.mean(total_kw.to_numpy()[baseload_mask])) if baseload_mask.any() else 0.0
    peak_kw = float(max(max(prof_work, default=0.0), max(prof_off, default=0.0)))
    average_load_kw = float(np.mean(total_kw.to_numpy())) if n_ts else 0.0

    # 5. Totals (band) over non-solar circuits -- §5.3
    total = Band(
        sum(cr.kwh.low for cr in circuit_results),
        sum(cr.kwh.mid for cr in circuit_results),
        sum(cr.kwh.high for cr in circuit_results),
    )

    # 6. Occupied vs unoccupied (kWh, mid) -- §5.6
    kwh_per_ts = total_kw.to_numpy() * building_interval
    occ = _occupied_mask(
        hours, weekdays, working_idx, config.occupied_start_hour, config.occupied_end_hour
    )
    in_working_day = np.isin(weekdays, list(working_idx))
    weekday_offhours = in_working_day & ~occ
    weekend = ~in_working_day
    total_mid = float(np.sum(kwh_per_ts)) or 1.0
    unoccupied_kwh = float(np.sum(kwh_per_ts[~occ]))
    unoccupied_share = unoccupied_kwh / total_mid
    weekday_off_share = float(np.sum(kwh_per_ts[weekday_offhours])) / total_mid
    weekend_share = float(np.sum(kwh_per_ts[weekend])) / total_mid

    # 7. Load mix by type (mid) -- §5.7
    mix: dict[str, float] = {}
    for cr in circuit_results:
        mix[cr.load_type] = mix.get(cr.load_type, 0.0) + cr.kwh.mid
    mix_total = sum(mix.values()) or 1.0
    load_mix = [
        LoadMixEntry(lt, kwh, kwh / mix_total)
        for lt, kwh in sorted(mix.items(), key=lambda kv: -kv[1])
    ]

    # 8. Cost / carbon -- §5.8
    annual_factor = (C.DAYS_PER_YEAR / period_days) if period_days else 0.0
    period_cost = Band(
        total.low * config.tariff_low,
        total.mid * config.tariff_mid,
        total.high * config.tariff_high,
    )
    annual_cost = Band(
        period_cost.low * annual_factor,
        period_cost.mid * annual_factor,
        period_cost.high * annual_factor,
    )
    ef = config.emission_factor_tco2_per_mwh / 1000.0  # tCO2 per kWh
    period_carbon = total.mid * ef
    annual_carbon = period_carbon * annual_factor

    annual_unoccupied_kwh = unoccupied_kwh * annual_factor
    rec_cost_low = annual_unoccupied_kwh * C.RECOVERABLE_FRACTION_LOW * config.tariff_mid
    rec_cost_high = annual_unoccupied_kwh * C.RECOVERABLE_FRACTION_HIGH * config.tariff_mid
    rec_carbon_low = annual_unoccupied_kwh * C.RECOVERABLE_FRACTION_LOW * ef
    rec_carbon_high = annual_unoccupied_kwh * C.RECOVERABLE_FRACTION_HIGH * ef

    # 9. Flags + assumptions -- §8
    if solar_results:
        flags.append(
            {
                "type": "solar_excluded",
                "message": (
                    f"{len(solar_results)} solar circuit(s) reported "
                    "separately and excluded from building totals."
                ),
                "circuits": [s.circuit_name for s in solar_results],
            }
        )
    gaps = (
        int(
            np.sum(
                np.abs(np.diff(ts.view("int64")) / 3.6e12 - building_interval)
                > 0.5 * building_interval
            )
        )
        if n_ts > 1
        else 0
    )
    if gaps:
        flags.append(
            {
                "type": "timestamp_gaps",
                "count": gaps,
                "message": f"{gaps} irregular interval(s) detected in the timeline.",
            }
        )
    flags.append(
        {
            "type": "coverage",
            "message": (
                f"{len(circuit_results)} circuit(s) and {n_ts} reading(s) "
                f"analysed at a {building_interval:.2f} h interval over "
                f"{period_days:.1f} day(s)."
            ),
            "circuits_analysed": len(circuit_results),
            "readings": n_ts,
        }
    )

    assumptions = {
        "mode": config.mode,
        "occupied_hours": [config.occupied_start_hour, config.occupied_end_hour],
        "working_days": config.working_days,
        "power_factor_bands": "per load type (low/mid/high); totals are ranges",
        "tariff": {
            "low": config.tariff_low,
            "mid": config.tariff_mid,
            "high": config.tariff_high,
            "currency": config.tariff_currency,
            "unit": config.tariff_unit,
            "note": "Tariff is the softest input — confirm against an actual bill.",
        },
        "emission_factor_tco2_per_mwh": config.emission_factor_tco2_per_mwh,
        "baseload_window": [C.BASELOAD_START_HOUR, C.BASELOAD_END_HOUR],
        "interval_hours": round(building_interval, 3),
        "annualisation": "extrapolated from the measured window; provide a full year of bills to confirm.",
        "recoverable_fraction": [C.RECOVERABLE_FRACTION_LOW, C.RECOVERABLE_FRACTION_HIGH],
    }

    return EngineResult(
        total_kwh=total,
        average_load_kw=average_load_kw,
        baseload_kw=baseload_kw,
        peak_kw=peak_kw,
        interval_hours=round(building_interval, 3),
        period_days=round(period_days, 2),
        unoccupied_share=unoccupied_share,
        unoccupied_weekday_offhours_share=weekday_off_share,
        unoccupied_weekend_share=weekend_share,
        hourly_profile=HourlyProfile(working_days=prof_work, off_days=prof_off),
        load_mix=load_mix,
        circuits=circuit_results,
        solar=solar_results,
        period_cost=period_cost,
        annual_cost=annual_cost,
        period_carbon_tco2=period_carbon,
        annual_carbon_tco2=annual_carbon,
        recoverable_cost_low=rec_cost_low,
        recoverable_cost_high=rec_cost_high,
        recoverable_carbon_low=rec_carbon_low,
        recoverable_carbon_high=rec_carbon_high,
        assumptions=assumptions,
        flags=flags,
    )
