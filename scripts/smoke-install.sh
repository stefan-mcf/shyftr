#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON:-python3.11}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN="python3"
fi
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN="python"
fi
TMP_VENV="$(mktemp -d "${TMPDIR:-/tmp}/shyftr-smoke-venv.XXXXXX")"
if command -v uv >/dev/null 2>&1; then
  uv venv --python "$PYTHON_BIN" "$TMP_VENV" >/dev/null
  uv pip install --python "$TMP_VENV/bin/python" -e "$ROOT_DIR[dev,service]" >/dev/null
else
  "$PYTHON_BIN" -m venv "$TMP_VENV"
  "$TMP_VENV/bin/python" -m pip install -U pip >/dev/null
  "$TMP_VENV/bin/python" -m pip install -e "$ROOT_DIR[dev,service]" >/dev/null
fi
"$TMP_VENV/bin/python" -m shyftr.cli --help >/dev/null
PYTHON="$TMP_VENV/bin/python" PATH="$TMP_VENV/bin:$PATH" bash "$ROOT_DIR/examples/run-local-lifecycle.sh"
echo "Smoke install passed with $($TMP_VENV/bin/python -V)"
rm -rf "$TMP_VENV"
