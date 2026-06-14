#!/usr/bin/env bash
# One-command local dev: starts the FastAPI backend (:8000) and the Vite
# frontend (:5173). Ctrl-C stops both. First run sets up the venv and npm deps.
# For manual / two-terminal control, see README.md.
set -euo pipefail
cd "$(dirname "$0")"

# --- backend setup (idempotent) ---
if [ ! -d backend/.venv ]; then
  echo "→ creating backend venv + installing deps…"
  python3 -m venv backend/.venv
  backend/.venv/bin/pip install -q --upgrade pip
  backend/.venv/bin/pip install -q -r backend/requirements.txt
fi

# --- frontend setup (idempotent) ---
if [ ! -d frontend/node_modules ]; then
  echo "→ installing frontend deps…"
  (cd frontend && npm install)
fi

# --- run both, clean up on exit ---
(cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000) &
BE=$!
(cd frontend && npm run dev) &
FE=$!

trap 'kill "$BE" "$FE" 2>/dev/null || true' EXIT INT TERM

echo ""
echo "  Backend   → http://localhost:8000   (docs at /docs)"
echo "  Frontend  → http://localhost:5173"
echo "  Ctrl-C to stop both."
echo ""
wait
