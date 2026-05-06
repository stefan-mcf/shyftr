# ShyftR Examples

All examples are synthetic and local-only. They are safe fixtures for learning the Pulse -> Spark -> Charge -> Pack -> Signal loop without network access, API keys, or external services.

## Files

| Path | Purpose | Used by |
|---|---|---|
| `examples/pulse.md` | Synthetic Pulse describing a Pack relevance lesson. | `shyftr ingest`, demo lifecycle, tests. |
| `examples/task.json` | Synthetic task request for Pack generation. | Documentation and JSON parse checks. |
| `examples/run-local-lifecycle.sh` | End-to-end local lifecycle using a temp Cell. | README quickstart, CI smoke, `scripts/check.sh`. |
| `examples/integrations/runtime-adapter.yaml` | Runtime-neutral adapter config fixture. | Adapter validation examples. |
| `examples/integrations/task-request.json` | Runtime-neutral Pack request fixture. | Integration docs/tests. |
| `examples/integrations/outcome-report.json` | Runtime-neutral Signal report fixture. | Integration docs/tests. |
| `examples/integrations/worker-runtime/**` | Richer synthetic worker-runtime fixture. | `tests/test_runtime_integration_demo.py`. |

## Run the local lifecycle

```bash
python -m pip install -e '.[dev,service]'
bash examples/run-local-lifecycle.sh
```

The script creates a temporary Cell under `${TMPDIR:-/tmp}`, prints its path, and leaves it in place for inspection. Remove that path when you are done.
