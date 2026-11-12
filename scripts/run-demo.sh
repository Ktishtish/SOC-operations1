#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

export PATH="$HOME/.local/bin:$PATH"
export PYTHONPATH="$ROOT/backend"

echo "[socwatch] starting API on :8000"
cd "$ROOT/backend"
uvicorn app.main:app --host 127.0.0.1 --port 8000 &
API_PID=$!
trap 'kill $API_PID 2>/dev/null || true' EXIT

for i in {1..30}; do
  if curl -sf http://127.0.0.1:8000/api/health >/dev/null; then
    break
  fi
  sleep 0.2
done

echo "[socwatch] smoke: list scenarios"
curl -sf http://127.0.0.1:8000/api/scenarios | python3 -m json.tool | head -n 40

echo "[socwatch] smoke: start payroll scenario + AI assist"
SESSION=$(curl -sf -X POST http://127.0.0.1:8000/api/sessions \
  -H 'Content-Type: application/json' \
  -d '{"scenario_id":"spearphish_payroll"}')
SID=$(python3 -c 'import json,sys; print(json.load(sys.stdin)["session_id"])' <<<"$SESSION")
curl -sf -X POST "http://127.0.0.1:8000/api/sessions/$SID/ai/assist" \
  -H 'Content-Type: application/json' \
  -d '{"question":"What should I do first?"}' | python3 -m json.tool | head -n 30

echo "[socwatch] demo API OK (pid=$API_PID). Start frontend with: cd frontend && npm run dev"
wait $API_PID
