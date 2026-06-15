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

Requirements: Python 3.11+ and Node 20+.

> **First-time setup:** the app needs Supabase auth configured to run. Copy
> `frontend/.env.example` → `frontend/.env.local` and fill in your Supabase URL +
> anon key, and export `SUPABASE_URL` / `SUPABASE_JWT_SECRET` for the backend
> (see [Configuration](#configuration-env-vars) and [Deploy](#deploy-supabase--render--vercel)).
> The test suite needs none of this — it runs in local SQLite mode.

### One command

```bash
./dev.sh
```

Sets up the venv + npm deps on first run, then starts both servers:

- Frontend: <http://localhost:5173>
- Backend API + docs: <http://localhost:8000/api/health> · <http://localhost:8000/docs>

`Ctrl-C` stops both. SQLite and uploaded files persist under `backend/data/`.

### Or run the two services manually (two terminals)

**Backend:**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173 (proxies /api to :8000)
```

> No Docker. SQLite is a single file and the two processes run directly, so a
> container layer adds setup friction without buying anything in Stage 1. A
> production deploy (Stage 2) would containerize the backend — noted in DESIGN.md.

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
dev.sh   DESIGN.md
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

All `/api/analyses` routes require an `Authorization: Bearer <token>` header and
are scoped to that user; `/api/reference/*` and `/api/health` are public.
Interactive docs at `/docs` when the backend is running.

---

## Configuration (env vars)

**Backend** (`backend/`):

| Var | Default | Meaning |
|---|---|---|
| `BEL_DATABASE_URL` | `sqlite:///backend/data/app.db` | SQLAlchemy connection string (Postgres in prod) |
| `BEL_DATA_DIR` | `backend/data` | base dir for the DB + uploads (local mode) |
| `BEL_STORAGE_DIR` | `<data>/uploads` | uploaded meter files (local mode) |
| `BEL_CORS_ORIGINS` | `http://localhost:5173,...` | allowed frontend origins |
| `BEL_MAX_UPLOAD_MB` | `25` | per-file upload limit |
| `SUPABASE_URL` | _(unset → local mode)_ | Supabase project URL; enables JWT auth + bucket storage |
| `SUPABASE_JWT_SECRET` | _(unset)_ | HS256 secret used to verify access tokens (Settings → API) |
| `SUPABASE_SERVICE_ROLE_KEY` | _(unset)_ | server-only key for Storage uploads (never sent to the browser) |
| `SUPABASE_STORAGE_BUCKET` | `meter-files` | private bucket for uploaded meter files |

**Frontend** (`frontend/`, `VITE_`-prefixed → bundled into the browser, public):

| Var | Default | Meaning |
|---|---|---|
| `VITE_SUPABASE_URL` | — | Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | — | Supabase anon/publishable key (public) |
| `VITE_API_BASE` | `""` | backend base URL in prod; empty in dev → uses the Vite proxy |
| `VITE_API_TARGET` | `http://localhost:8000` | backend target for the dev proxy |

> **Local mode vs. Supabase mode.** With no `SUPABASE_*` vars set, the backend
> runs on SQLite + local-disk storage (handy for the test suite), but the
> `/api/analyses` routes require a valid token, so the **app** needs Supabase
> auth configured to be usable. The browser only ever holds the **anon** key;
> the **service-role** key and DB credentials live only on the backend host.

---

## Authentication & multi-user

Each user signs up / logs in (Supabase Auth, email + password) and sees **only
their own** analyses. The split:

- **Frontend** uses `@supabase/supabase-js` only for auth (login, signup, token
  refresh) and attaches the access token as a bearer token on every API call
  (`src/lib/auth.tsx`, `src/lib/api.ts`).
- **Backend** verifies that token on every `/api/analyses` route
  (`app/auth.py`) and scopes every query to the token's user
  (`Analysis.user_id`). Another user's analysis returns **404**, never their data.
- The browser holds only the **anon** key. The **service-role** key and the
  Postgres connection string live only on the backend host.

## Deploy (Supabase → Render → Vercel)

**1. Supabase** — create a project, then:
- **Auth → Providers → Email**: enabled. **Auth → URL Configuration**: set Site
  URL + redirect URLs to your Vercel domain and `http://localhost:5173`.
- **Storage → New bucket** named `meter-files`, **private**. (No RLS policies
  needed — the frontend never touches Storage/Postgres directly.)
- Collect: Project URL, anon key, service-role key, JWT secret (Settings → API),
  and the **Session-pooler** connection string (Settings → Database). Rewrite the
  pooler URI to SQLAlchemy form: `postgresql+psycopg://USER:PWD@HOST:5432/postgres`.

**2. Backend → Render** — `backend/render.yaml` is a ready blueprint (build
`pip install -r requirements.txt`, start `uvicorn app.main:app`). Set
`SUPABASE_URL`, `SUPABASE_JWT_SECRET`, `SUPABASE_SERVICE_ROLE_KEY`,
`BEL_DATABASE_URL` (the pooler URI), and `BEL_CORS_ORIGINS` (your Vercel domain).
Tables are auto-created on first boot.

**3. Frontend → Vercel** — import the repo with **Root Directory = `frontend`**
(`frontend/vercel.json` handles the SPA rewrite). Set `VITE_SUPABASE_URL`,
`VITE_SUPABASE_ANON_KEY`, and `VITE_API_BASE` (the Render URL). Redeploy, then
add the resulting Vercel URL back into Supabase's redirect URLs and Render's
`BEL_CORS_ORIGINS`.

## Stage 2+ (noted for later)

Live carbon-intensity & tariff APIs (Electricity Maps, WattTime, Open-Meteo) ·
weather/degree-day HVAC normalisation · the mixed-circuit NNLS cooling split
(interface hook present, off by default) · background processing (Celery/RQ) ·
Google/OAuth sign-in (easy add on the existing Supabase Auth) · PDF export &
month-over-month views.
