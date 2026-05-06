#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON:-python}"
if [[ -n "${PYTHON:-}" ]]; then
  export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
  SHYFTR=("$PYTHON_BIN" -m shyftr.cli)
elif command -v shyftr >/dev/null 2>&1; then
  SHYFTR=(shyftr)
else
  export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
  SHYFTR=("$PYTHON_BIN" -m shyftr.cli)
fi

BASE="$(mktemp -d "${TMPDIR:-/tmp}/shyftr-demo.XXXXXX")"
CELL="$BASE/demo-cell"
EVIDENCE="$ROOT_DIR/examples/evidence.md"
BACKUP_DIR="$BASE/backups"
mkdir -p "$BACKUP_DIR"

json_get() {
  "$PYTHON_BIN" -c 'import json,sys; data=json.load(sys.stdin); key=sys.argv[1]; print(data[key])' "$1"
}
json_first_candidate() {
  "$PYTHON_BIN" -c 'import json,sys; data=json.load(sys.stdin); print(data[0]["candidate_id"])'
}

echo "Creating temp cell: $CELL"
"${SHYFTR[@]}" init-cell "$CELL" --cell-id demo-cell --cell-type domain >/tmp/shyftr-demo-init.json
EVIDENCE_ID=$("${SHYFTR[@]}" ingest "$CELL" "$EVIDENCE" --kind lesson | json_get evidence_id)
FRAGMENT_ID=$("${SHYFTR[@]}" candidate "$CELL" "$EVIDENCE_ID" | json_first_candidate)
"${SHYFTR[@]}" approve "$CELL" "$FRAGMENT_ID" --reviewer demo-script --rationale "Synthetic demo candidate is bounded and useful." >/tmp/shyftr-demo-review.json
MEMORY_ID=$("${SHYFTR[@]}" memory "$CELL" "$FRAGMENT_ID" --promoter demo-script --statement "Scope-tagged memories improve pack relevance." --rationale "Promoted from synthetic demo evidence." | json_get memory_id)
"${SHYFTR[@]}" search "$CELL" "pack relevance" >/tmp/shyftr-demo-search.json
"${SHYFTR[@]}" profile "$CELL" >/tmp/shyftr-demo-profile.json
LOADOUT_ID=$("${SHYFTR[@]}" pack "$CELL" "pack relevance" --task-id demo-script-task --max-items 5 --query-tags domain:testing --include-candidates | json_get pack_id)
"${SHYFTR[@]}" feedback "$CELL" "$LOADOUT_ID" success --applied "$MEMORY_ID" --useful "$MEMORY_ID" --verification '{"demo":"local lifecycle"}' >/tmp/shyftr-demo-feedback.json
"${SHYFTR[@]}" grid rebuild --cell "$CELL" --backend in-memory >/tmp/shyftr-demo-grid.json
"${SHYFTR[@]}" hygiene "$CELL" >/tmp/shyftr-demo-hygiene.json
"${SHYFTR[@]}" diagnostics "$CELL" --summary >/tmp/shyftr-demo-diagnostics.json
"${SHYFTR[@]}" readiness "$CELL" >/tmp/shyftr-demo-readiness.json
"${SHYFTR[@]}" verify-ledger --cell "$CELL" --adopt >/tmp/shyftr-demo-ledger-adopt.json
"${SHYFTR[@]}" verify-ledger --cell "$CELL" >/tmp/shyftr-demo-ledger-verify.json
"${SHYFTR[@]}" backup --cell "$CELL" --output "$BACKUP_DIR" >/tmp/shyftr-demo-backup.json

echo "ShyftR local lifecycle complete."
echo "cell path: $CELL"
echo "Temp JSON outputs: /tmp/shyftr-demo-*.json"
echo "Remove demo files with: rm -rf '$BASE' /tmp/shyftr-demo-*.json"
