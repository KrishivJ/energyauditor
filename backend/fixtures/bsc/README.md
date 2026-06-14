# BSC acceptance fixture

The acceptance gate (`tests/test_engine_bsc.py`, brief §7) loads the real BSC
data from this directory. The files are proprietary and supplied by the project
owner, so they are **not** committed. Until they are present the acceptance test
skips with a clear message; the synthetic tests (`test_engine_synth.py`,
`test_ingestion.py`) cover the logic in the meantime.

## To activate the gate

1. Drop the **21 BSC meter files** (`.xlsx` / `.xls` / `.csv`, one per circuit)
   into this directory.
2. Add **`expected_outputs.json`** here using the structure below (values are the
   §7 headline targets; tolerances default sensibly and can be tightened).

```jsonc
{
  "config": {
    "mode": "cv",
    "occupiedStartHour": 7,
    "occupiedEndHour": 18,
    "workingDays": ["Mon", "Tue", "Wed", "Thu", "Fri"],
    "tariff": { "low": 11, "mid": 12, "high": 13 },
    "emissionFactorTco2PerMwh": 0.7117
  },
  "tolerances": {
    "total_kwh_pct": 0.01,   // totals within 1%
    "load_pct": 0.05,        // average/baseload/peak within 5%
    "share_abs": 0.03,       // shares within 3 percentage points
    "cost_pct": 0.02         // cost/carbon within 2%
  },
  "expected": {
    "total_kwh_mid": 160000,
    "total_kwh_band": [151300, 167200],
    "average_load_kw": 225,
    "baseload_kw": 117,
    "peak_kw": 380,
    "unoccupied_share": 0.45,
    "unoccupied_weekday_offhours_share": 0.27,
    "unoccupied_weekend_share": 0.18,
    "load_mix": {
      "HVAC": 0.41, "General Power": 0.31, "Lighting": 0.15,
      "UPS": 0.10, "Lift": 0.03, "Ventilation": 0.006
    },
    "faulty_voltage_count": 2,
    "solar_excluded_count": 1,
    "period_cost_mid": 1920000,
    "period_carbon_tco2": 114
  }
}
```

Each key in `expected` is optional — the test only asserts the ones present.
