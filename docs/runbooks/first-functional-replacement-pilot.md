# First Functional Replacement Runbook

This runbook covers the first bounded-domain replacement pilot for a managed agent-memory backend. It stops at the replacement checkpoint; operator approval is still required before ShyftR becomes primary memory for any real runtime domain.

## Scope

- Domain: one bounded runtime/domain only.
- Authority: ShyftR may become primary only for that bounded domain after readiness passes and the operator approves.
- Fallback: the existing backend remains export/archive/fallback during the pilot.
- Evidence: every Pack, Signal, confidence update, affinity update, import/export, and readiness decision must have diagnostic logs.

## 1. Shadow import

1. Export the existing managed memory backend to JSON.
2. Import through ShyftR's Regulator-governed provider path, not direct ledger writes.
3. Reject noisy operational state, secrets, queue status, branch state, transient closeouts, and unsupported verification claims.
4. Preserve source IDs/provenance in Pulse metadata.

CLI smoke runs the fixture in a shadow Cell so fixture memories do not enter the target Cell's canonical Charge ledger:

```bash
shyftr readiness /path/to/cell --replacement-pilot --fixture tests/fixtures/replacement/managed_memory_export.json
```

Expected:

- `status: passed`
- rejected noisy operational-state fixture count is non-zero
- readiness output `diagnostic_summary` includes shadow evidence for `managed_memory_import`, `pack`, `signal`, and `export_snapshot`
- target Cell diagnostics include `replacement_readiness`

## 2. Advisory Pack comparison

1. Keep existing backend primary.
2. Request ShyftR Packs for the same bounded-domain tasks.
3. Compare selected Charge IDs, excluded IDs, scoring components, token estimate, and warnings.
4. Report Signals for every ShyftR-influenced task, even if the Pack was ignored.

Useful diagnostics:

```bash
shyftr diagnostics /path/to/cell --summary
shyftr diagnostics /path/to/cell --operation pack --limit 10
```

## 3. Bounded-domain primary mode

Enter this mode only when:

- Phase 1 through Tranche 1.9 is complete.
- Full tests/CI pass.
- Replacement replay passes.
- Pack/Signal APIs are stable for the domain.
- Diagnostic logs explain selection, exclusion, Signal linkage, confidence changes, and affinity changes.
- Existing backend export/archive is available.
- Operator explicitly approves bounded-domain primary memory.

Operational rules:

- Use ShyftR as primary for this domain only.
- Keep existing backend read-only fallback/archive.
- Emit Signals for every task affected by a ShyftR Pack.
- Review harmful, contradicted, or repeatedly ignored memory before expanding authority.

## 4. Fallback mode

Fallback to the existing backend when:

- readiness returns `blocked`;
- diagnostic logs are missing or incomplete;
- Pack generation returns empty or over-retrieved context for critical tasks;
- harmful/contradicted Signals exceed the pilot threshold;
- import/export snapshot fails;
- operator disables bounded-domain primary mode.

## 5. Rollback/archive procedure

1. Export a ShyftR snapshot:

```bash
python - <<'PY'
import json
from shyftr.provider.memory import MemoryProvider
payload = MemoryProvider('/path/to/cell').export_snapshot()
print(json.dumps(payload, indent=2, sort_keys=True))
PY
```

2. Preserve the existing backend export/archive.
3. Stop injecting ShyftR Packs into the bounded-domain runtime.
4. Resume existing backend primary mode.
5. Keep ShyftR diagnostic and readiness reports for analysis.

## Verification bundle

Before declaring replacement checkpoint reached:

```bash
python3 -m pytest -q
python3 -m pytest tests/test_replacement_readiness.py -q
shyftr readiness /path/to/cell --replacement-pilot --fixture tests/fixtures/replacement/managed_memory_export.json
shyftr diagnostics /path/to/cell --summary
git diff --check
```

For source-tree smoke runs before installation, prefix CLI commands with `PYTHONPATH=src python3 -m shyftr.cli`.
