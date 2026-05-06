# Phase 7.8 public/private split

Status: implemented as a public-safe foundation for local controlled pilots.

Regulated autonomous memory evolution in public `main` is proposal-first, simulation-aware, and review-gated. It detects candidate splits, duplicate memory consolidation, stale or contradicted memory, logical forgetting, redaction, replacement, and missing-memory opportunities, then writes review proposals. It does not silently rewrite canonical ledgers and it does not physically delete memory as normal behavior.

## Public/private split table

| Area | Public-safe implementation | Private-core reserved | Hard gate |
| --- | --- | --- | --- |
| arrival splitting | deterministic size/topic heuristics and split proposal schema | proprietary semantic segmentation scoring over real private data | proposals only until review |
| duplicate consolidation | transparent normalized text and token-overlap checks with deterministic synthetic tests | tuned thresholds, domain-specific entity disambiguation, private embeddings | never merge without review |
| supersession | lifecycle proposals from repeated contradiction/stale feedback and simulation reports | private contradiction ranking and confidence calibration | simulation plus review |
| forget/deprecate/redact | logical lifecycle proposals and projection exclusion tests | private retention/legal policy automation | operator-approved policy only |
| confidence evolution | public confidence/projection delta fields on proposals and simulations | advanced calibration/model-fit scoring | advisory, not authority |
| evolution scheduler | explicit `shyftr evolve scan` dry-run and `--write-proposals` mode | private autonomous cadence over real cells | disabled by default |
| UI/operator surfaces | CLI, local HTTP service, and browser console proposal visibility | private operator workflows | no hidden mutations |

## Public invariants

- cell ledgers remain canonical truth.
- evolution scan is dry-run by default.
- `--write-proposals` appends proposals only, never lifecycle mutations.
- accepted retrieval-affecting proposals require simulation evidence.
- acceptance applies existing append-only mutation/review paths.
- synthetic fixtures and tests are the public proof surface.
- real private cells, hosted deployment, automatic destructive policy, and production compliance automation are out of scope.

## Verification evidence

Initial implementation evidence is captured by the Phase 7.8 closeout checks and focused tests. Latest local closeout pass:

```bash
PYTHONPATH=src python -m pytest -q tests/test_eval_generator.py tests/test_memory_evolution_*.py  # 24 passed
PYTHONPATH=src python -m pytest -q                                                         # 870 passed
python scripts/terminology_inventory.py && python scripts/public_readiness_check.py && git diff --check
npm run build --prefix apps/console
bash scripts/alpha_gate.sh                                                                  # ALPHA_GATE_READY
```

Expected behavior: scan emits proposals only by default; review decisions are append-only; simulation reports line counts unchanged; logical forgetting/deprecation/redaction exclude memory from projections only after accepted review events.
