# Building Energy Lens — Stage 1 Design (Phase 0)

This document confirms the stack, architecture, API contract, DB schema, and
resource list from the build brief, and records the (small) deviations made.
Treat the brief's Section 5 (engine spec) and Section 7 (acceptance fixture) as
authoritative; this file does not restate them, it confirms how they are wired.

## 1. Stack — confirmed

| Layer      | Choice                                              | Status |
|------------|-----------------------------------------------------|--------|
| Backend    | Python 3.11+, FastAPI, uvicorn                      | as recommended |
| Schemas    | pydantic v2                                         | as recommended |
| Engine     | pandas, numpy (pure functions, no I/O)              | as recommended |
| Parsing    | openpyxl (.xlsx/.xls), pandas (.csv)               | as recommended |
| Stretch    | scipy (NNLS cooling split) — optional, off by default | as recommended |
| DB         | SQLite via SQLAlchemy 2.x                           | see deviation D1 |
| Storage    | local filesystem behind a `Storage` interface       | as recommended |
| Tests      | pytest, httpx (TestClient)                          | as recommended |
| Frontend   | React + TypeScript + Vite                           | as recommended |
| Styling    | Tailwind, design tokens from brief §1               | as recommended |
| Charts     | recharts (mix bars) + hand-rolled SVG load profile  | as recommended |
| Upload     | react-dropzone                                      | as recommended |
| API client | native fetch, typed                                 | see deviation D2 |
| Dev        | docker-compose (frontend, backend); SQLite is a file | see deviation D1 |

### Deviations (with rationale)
- **D1 — DB is a file, not a compose service.** SQLite is file-based, so there is
  no separate `db` container in Stage 1. `docker-compose.yml` runs two services
  (backend, frontend); the SQLite file lives on a mounted volume. A `db` service
  is unnecessary until the Stage 2 PostgreSQL swap. The SQLAlchemy layer keeps
  that swap a connection-string change.
- **D2 — native `fetch`, not axios.** One fewer dependency; the typed client in
  `lib/api.ts` is the contract surface. `zod` is omitted for Stage 1 (TS types on
  the shared response shapes are sufficient); noted as an easy add.
- **D3 — sync DB driver for Stage 1.** Using SQLAlchemy's sync engine with
  FastAPI run in a threadpool rather than `aiosqlite`. Datasets are tiny and
  analysis is synchronous (brief §3), so async DB adds complexity with no payoff.
  The session/engine setup is isolated in `db.py`; swapping to async is local.

## 2. Architecture

Monorepo exactly as brief §4. Engine is pure functions in `app/engine/`
(no file/DB/network I/O) so it is unit-testable against the fixture. Ingestion
(`app/ingestion/`) does all parsing + per-file column detection and hands the
engine plain typed structures. API handlers orchestrate: ingestion → persist →
engine → persist results.

```
Frontend ──upload──▶ POST /api/analyses ──▶ ingestion (parse + per-file detect)
                                          └▶ persist files + analysis (status=uploaded)
Frontend ◀── analysisId, files[], warnings[]
Frontend ──config──▶ PUT  /config ──▶ persist config
Frontend ──run─────▶ POST /run    ──▶ engine.run(parsed, config) ──▶ persist results
Frontend ◀── results JSON ──▶ dashboard
```

### Engine boundary (the important one)
`engine.run(circuits: list[CircuitInput], config: EngineConfig) -> EngineResult`

- `CircuitInput`: `filename, circuit_name, timestamps[], value[], voltage[]|None,
  load_type` — already parsed and column-resolved by ingestion.
- No pandas types cross the API boundary; the engine returns plain dataclasses
  serialised by pydantic schemas.
- All domain constants (PF bands, keyword map, faulty-voltage threshold,
  baseload window, opportunity fractions) live in `engine/constants.py`.

## 3. API contract — confirmed (brief §4)

```
POST   /api/analyses                 multipart -> { analysisId, files[], warnings[] }
GET    /api/analyses                 -> [ { id, name, createdAt, status } ]
GET    /api/analyses/{id}            -> { id, name, config, files[], results|null }
PUT    /api/analyses/{id}/config     body: AnalysisConfig -> { ok }
POST   /api/analyses/{id}/run        -> { results }
DELETE /api/analyses/{id}            -> { ok }
GET    /api/reference/emission-factors  -> [ { region, factor, unit, source, year } ]
GET    /api/reference/tariffs           -> [ { id, region, low, mid, high, currency, unit, note } ]
GET    /api/health                      -> { ok: true }   (added for Phase 1 deliverable)
```

`AnalysisConfig` and `EngineConfig` mirror brief §4. `columnOverrides` is keyed by
filename; an override merges over (and wins against) auto-detection per file.

## 4. DB schema (SQLAlchemy) — confirmed (brief §4)

- `analyses(id, name, created_at, status, config_json, results_json)`
  - `status ∈ {uploaded, configured, complete, error}`
- `files(id, analysis_id FK, filename, circuit_name, load_type, storage_path,
   row_count, start_ts, end_ts, detected_cols_json, flags_json)`

Reference datasets (`tariffs.json`, `emission_factors.json`) are bundled JSON in
`app/reference/`, loaded at startup — not DB tables (brief §4).

## 5. Resource list — confirmed (brief §6)
- Bundled: `reference/emission_factors.json` (India CEA 0.7117 tCO2/MWh seed),
  `reference/tariffs.json` (Delhi non-domestic 11/12/13 INR/kWh seed).
- `fixtures/bsc/` — real BSC files provided by the project owner. The acceptance
  test (`tests/test_engine_bsc.py`) loads them + `expected_outputs.json` and
  **skips with a clear message when they are absent**, so CI is green pre-drop and
  becomes a hard gate once the files land.
- A synthetic generator (`tests/synth.py`) builds a representative 21-circuit set
  exercising the frequency-shift column offset, faulty voltage, and solar
  exclusion, used by `test_ingestion.py` and `test_engine_synth.py` so engine and
  detection logic are verified now without the proprietary data.
- Stage 2 third-party APIs (Electricity Maps, WattTime, Open-Meteo) listed only;
  not integrated. No free Indian DERC tariff API assumed — tariffs stay
  user-configurable with the bundled preset.

## 6. Integrity wiring (brief §8)
- Energy totals carry `low/mid/high` PF bands end to end; the API returns ranges,
  the UI renders ranges, never a single false-precise figure.
- `EngineResult.assumptions` echoes every changeable input; `EngineResult.flags`
  carries faulty-voltage substitutions, solar exclusion, reading interval, gaps,
  and circuit/reading counts.
- Annualised and recoverable figures are tagged `extrapolation` and the tariff
  carries a "confirm against your bill" note surfaced in the UI.

## 7. Build order
Phases per brief §9: 0 (this doc) → 1 scaffold → 2 ingestion+engine+tests (the
correctness gate; built before any UI) → 3 API → 4 frontend → 5 persistence UX →
6 polish/docs.
