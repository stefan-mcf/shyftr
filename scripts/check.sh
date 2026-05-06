#!/usr/bin/env bash
set -euo pipefail
python -m pytest -q
python -m shyftr.cli --help >/dev/null
bash examples/run-local-lifecycle.sh
if [ -d apps/console ] && command -v npm >/dev/null 2>&1; then
  (cd apps/console && npm run build && npm audit --omit=dev)
else
  echo "Skipping console check: npm not available"
fi
python scripts/public_readiness_check.py
