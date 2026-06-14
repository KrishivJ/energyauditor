# Building Energy Lens — Stage 1

Turns raw circuit-level smart-meter exports into an energy picture for a
building: where power goes, how much is consumed while the building is
unoccupied, the always-on baseload, and the cost and carbon impact — with
prioritised, **range-based** findings that surface every assumption.

Stage 1 is a working full-stack prototype: a FastAPI backend with a validated
analysis engine, a React dashboard, and saved analyses persisted in SQLite.

- **Design / Phase 0 decisions:** [`DESIGN.md`](DESIGN.md)
- **Engine spec & acceptance fixture:** the build brief §5 / §7, mirrored by
  `backend/tests/test_engine_bsc.py` and `backend/fixtures/bsc/README.md`.

---

## Quick start

### Option A — Docker (recommended)

```bash
docker compose up --build
```

- Frontend: <http://localhost:5173>
- Backend API + docs: <http://localhost:8000/api/health> · <http://localhost:8000/docs>

SQLite and uploaded files persist in the `bel_data` volume.

### Option B — run the two services directly

**Backend** (Python 3.11+):

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend** (Node 20+):

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173 (proxies /api to :8000)
```

---

## Using it

1. **New analysis → upload** one meter file per circuit (`.xlsx`, `.xls`,
   `.csv`). Columns are auto-detected **per file**.
2. **Review the mapping** — every circuit's detected timestamp / value / voltage
   columns, with manual overrides if a meter is laid out differently.
3. **Set assumptions** — meter mode, occupied hours, working days, tariff band
   (preset loadable), emission factor.
4. **Run** → the dashboard shows the headline unoccupied share, daily load
   profile (working vs off days), load mix, baseload, cost & carbon, data-quality
   flags, and the assumptions panel.
5. **Saved analyses** persist; reopen, re-run with new assumptions, or delete.

Estimates are reported as **ranges** (energy depends on assumed power factors),
annual figures are flagged as extrapolations, and the tariff always carries a
"confirm against your bill" prompt.

---

## Tests

```bash
cd backend && source .venv/bin/activate
pytest -q                 # engine, ingestion (incl. frequency-shift), API cycle
ruff check app tests      # lint
black --check app tests   # format
```

```bash
cd frontend
npm run lint              # eslint
npm run format:check      # prettier
npm run build             # tsc -b type-check + production build
```

### Acceptance gate (BSC fixture)

The correctness gate (`tests/test_engine_bsc.py`) reproduces the validated BSC
results within tolerance. The 21 BSC files are proprietary and supplied by the
project owner, so the test **skips with a clear message until they are present**.
Drop the files + `expected_outputs.json` into `backend/fixtures/bsc/` to activate
it — see [`backend/fixtures/bsc/README.md`](backend/fixtures/bsc/README.md).

In the meantime, a synthetic 21-circuit dataset (`backend/tests/synth.py`)
exercises the same code paths — the per-file column detection (including the
frequency-shift offset that the brief flags as a once-fixed regression), the
faulty-voltage substitution, and solar exclusion.

---

## Architecture

```
/backend   FastAPI app
  app/engine/      pure analysis functions (no I/O) — the heart of the product
  app/ingestion/   file parsing + per-file column detection
  app/api/         route handlers
  app/reference/   bundled tariff & emission-factor datasets
  app/models/      SQLAlchemy models   app/schemas/  pydantic contract
  app/db.py  app/storage.py  app/services.py  app/config.py
  tests/     fixtures/bsc/
/frontend  React + TypeScript + Vite + Tailwind
  src/components/  Uploader, MappingPanel, ConfigPanel, Dashboard, charts
  src/pages/       NewAnalysis, SavedAnalyses, AnalysisView
  src/lib/api.ts   typed API client (the contract surface)
docker-compose.yml   DESIGN.md
```

### API

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/analyses` | multipart upload → `{ analysisId, files[], warnings[] }` |
| `GET` | `/api/analyses` | list saved analyses |
| `GET` | `/api/analyses/{id}` | full detail (config, files, results) |
| `PUT` | `/api/analyses/{id}/config` | save `AnalysisConfig` |
| `POST` | `/api/analyses/{id}/run` | run the engine → results |
| `DELETE` | `/api/analyses/{id}` | delete |
| `GET` | `/api/reference/emission-factors` · `/api/reference/tariffs` | bundled presets |
| `GET` | `/api/health` | health check |

Interactive docs at `/docs` when the backend is running.

---

## Configuration (env vars)

| Var | Default | Meaning |
|---|---|---|
| `BEL_DATABASE_URL` | `sqlite:///backend/data/app.db` | SQLAlchemy connection string |
| `BEL_DATA_DIR` | `backend/data` | base dir for the DB + uploads |
| `BEL_STORAGE_DIR` | `<data>/uploads` | uploaded meter files |
| `BEL_CORS_ORIGINS` | `http://localhost:5173,...` | allowed frontend origins |
| `BEL_MAX_UPLOAD_MB` | `25` | per-file upload limit |
| `VITE_API_TARGET` | `http://localhost:8000` | backend target for the dev proxy |

No secrets are required or stored in the repo.

---

## Stage 2 (out of scope here, noted for later)

User accounts/auth · live carbon-intensity & tariff APIs (Electricity Maps,
WattTime, Open-Meteo) · weather/degree-day HVAC normalisation · the mixed-circuit
NNLS cooling split (interface hook present, off by default) · background
processing (Celery/RQ) · PostgreSQL (connection-string swap) · S3 storage
(behind the existing `Storage` interface) · PDF export & month-over-month views.
