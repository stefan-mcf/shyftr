# Runtime Integration Demo

This demo shows a runtime-neutral closed learning loop using only files and
JSON contracts. It avoids product-specific runtime details; any worker system
that can write files and call the ShyftR CLI can use the same pattern.

Fixture files live in `examples/integrations/worker-runtime/`:

- `adapter.yaml` declares how ShyftR discovers runtime evidence.
- `pulse-closeout.md` is a human-readable closeout Pulse from a completed task.
- `signal-log.jsonl` is an append-only runtime event stream.
- `task-request.json` is a Pack request before work starts.
- `signal-report.json` is a Signal report after work finishes.

## 1. Validate the adapter

```bash
shyftr adapter validate --config examples/integrations/worker-runtime/adapter.yaml
```

Validation proves the runtime can describe its evidence locations without custom
code in ShyftR.

## 2. Discover and ingest runtime Pulses

```bash
shyftr adapter discover --config examples/integrations/worker-runtime/adapter.yaml --dry-run
shyftr adapter ingest --config examples/integrations/worker-runtime/adapter.yaml --cell-path ./demo-cell
```

The adapter turns the closeout Pulse, Signal JSONL rows, task request, and
Signal report into append-only Cell ledger Sources. The Cell Ledger remains
canonical truth; adapter state and indexes are rebuildable acceleration.

## 3. Review and promote memory

The demo test exercises the Pulse -> Spark -> Charge path by extracting a Spark
from the closeout Pulse, approving it, and promoting it into a Charge. That
Charge can later appear in a Pack.

## 4. Request a Pack before the next task

`task-request.json` demonstrates the runtime-side request shape. It asks for a
small trust-filtered Pack relevant to adapter config validation and JSONL sync.
The current stable API module is `shyftr.integrations.loadout_api`; the public
theme term is Pack.

## 5. Report Signal after the task

`signal-report.json` demonstrates the runtime-side report shape. It records
applied and useful Charge IDs, runtime references, and verification evidence.
The current stable API module is `shyftr.integrations.outcome_api`; the public
theme term is Signal.

## 6. Closed loop

The fixture includes all four signals required for a useful learning loop:

- successful workflow: a Pack was applied and the task succeeded;
- repeated failure signature: multiple timeout/no-report runs;
- recovery pattern: timeout window increased after repeated evidence;
- caution: ShyftR emits reviewable evidence rather than mutating runtime policy.

The accompanying test `tests/test_runtime_integration_demo.py` proves the demo
end to end without any product-specific runtime dependency.

## 7. Local HTTP service (optional)

When shelling out to the CLI is impractical (e.g. a runtime that only speaks
HTTP), use the optional local service wrapper:

```bash
# Install with the optional HTTP extras
pip install shyftr[service]

# Start the service
python -m shyftr.server

# Or with custom bind address & port
python -m shyftr.server --host 127.0.0.1 --port 8014
```

### Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/validate` | POST | Validate an adapter config file |
| `/ingest` | POST | Ingest a Pulse via an adapter config |
| `/pack` | POST | Request a Loadout/Pack |
| `/signal` | POST | Report a Signal/Outcome |
| `/proposals/export` | POST | Export advisory runtime proposals |

### Example: Pack request via curl

```bash
curl -X POST http://127.0.0.1:8014/pack \
  -H "Content-Type: application/json" \
  -d '{
    "cell_path_or_id": "./demo-cell",
    "query": "adapter config validation",
    "task_kind": "validation",
    "external_system": "worker-runtime",
    "external_scope": "demo"
  }'
```

### Example: Signal report via curl

```bash
curl -X POST http://127.0.0.1:8014/signal \
  -H "Content-Type: application/json" \
  -d '{
    "cell_path_or_id": "./demo-cell",
    "loadout_id": "loadout-demo-001",
    "result": "success",
    "external_system": "worker-runtime",
    "external_scope": "demo",
    "external_run_id": "run-001",
    "applied_trace_ids": ["trace-abc"],
    "useful_trace_ids": ["trace-abc"],
    "verification_evidence": {"tests": "passed"}
  }'
```

### Example: Proposal export via curl

```bash
curl -X POST http://127.0.0.1:8014/proposals/export \
  -H "Content-Type: application/json" \
  -d '{
    "cell_path": "./demo-cell",
    "external_system": "worker-runtime",
    "include_accepted": false
  }'
```
