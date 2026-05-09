#!/usr/bin/env bash
# setup.sh — one-shot dev environment bootstrap (macOS/Linux)
# Usage: bash scripts/setup.sh

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=== SIRINAPHA Baan-Pla Link — Dev Setup ==="
echo "Root: $ROOT"
echo

echo "[1/3] Frontend — npm install..."
(cd "$ROOT/frontend" && npm install)
if [ ! -f "$ROOT/frontend/.env.local" ] && [ -f "$ROOT/frontend/.env.local.example" ]; then
  cp "$ROOT/frontend/.env.local.example" "$ROOT/frontend/.env.local"
  echo "  Created .env.local — please fill in keys"
fi

echo "[2/3] Backend — Python venv + pip install..."
(cd "$ROOT/backend" && {
  [ -d .venv ] || python3 -m venv .venv
  source .venv/bin/activate
  pip install --upgrade pip
  pip install -r lambda/requirements.txt
  pip install pytest hypothesis
})

echo "[3/3] Running sanity tests..."
(cd "$ROOT/backend" && source .venv/bin/activate && pytest -q --tb=line)
(cd "$ROOT/frontend" && npm test)

echo
echo "=== Setup complete ==="
echo "Next:"
echo "  cd frontend && npm run dev         # http://localhost:3000"
echo "  cd backend && source .venv/bin/activate && pytest"
