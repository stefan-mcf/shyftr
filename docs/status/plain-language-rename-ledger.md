# Plain-Language Rename Ledger

## Decision summary

ShyftR is migrating its public canonical lifecycle vocabulary to:

```text
evidence -> candidate -> memory -> pattern -> rule
```

Support terms use lowercase common nouns in prose: cell, ledger, regulator, grid, pack, feedback, decay, quarantine.

## Old-to-new mapping

| Old/current term | New canonical term | Compatibility status |
| --- | --- | --- |
| Pulse / Source / Feed | Evidence | Old model/field/ledger names are legacy read aliases only. |
| Spark / Fragment | Candidate | Old model/field/CLI names are legacy aliases only. |
| Charge / Trace | Memory | Old model/field/ledger names are legacy read aliases only. |
| Coil / Alloy / Circuit | Pattern | Old model/module names are legacy aliases only. |
| Rail / Doctrine | Rule | Old model/module names are legacy aliases only. |
| Loadout | Pack | Old CLI/API names are legacy aliases only. |
| Outcome / Signal | Feedback | Old CLI/API names are legacy aliases only. |
| Isolation | Quarantine | Old event naming is legacy/internal compatibility only. |

## Baseline evidence

- Baseline commit: `d838c7df811f9dd7a340b9b92930c6ff22b60b19`
- Baseline status: only the rename plan and source note were untracked before implementation.
- Baseline tests: `python -m pytest -q` -> 747 passed, 22 warnings.

## Files touched

Updated during implementation; see `git diff --name-status` for the authoritative file list.

## Compatibility aliases intentionally kept

Compatibility aliases are intentionally retained for old JSON payloads, old ledgers, old CLI commands, old routes, old module imports, and old class imports. New writes and public docs should prefer canonical vocabulary.

## Stale-term scan results

Final public stale guard evidence, 2026-05-06:

```bash
python scripts/terminology_inventory.py --fail-on-public-stale
# exit 0
```

The full report currently classifies remaining old-term matches as intentional compatibility, implementation/test compatibility, historical/source planning material, or generic English usage:

```text
capitalized_prose:allowed: 500
legacy_implementation:allowed: 2361
power_theme:allowed: 410
support_legacy:allowed: 898
```

## Capitalization scan results

Final capitalization guard evidence, 2026-05-06:

```bash
python scripts/terminology_inventory.py --fail-on-capitalized-prose
# exit 0
```

Normal public prose uses lowercase lifecycle/support nouns; title case remains allowed for headings, diagrams, tables, UI labels, and code/type names.

## Test evidence

Final local verification evidence, 2026-05-06:

```bash
python -m pytest tests/test_terminology_inventory.py tests/test_models.py tests/test_cli.py tests/test_demo_flow.py tests/test_pack.py tests/test_feedback.py tests/test_pack_api.py tests/test_feedback_api.py tests/test_patterns.py tests/test_rules.py tests/test_runtime_integration_demo.py -q
# 253 passed

bash examples/run-local-lifecycle.sh
# ShyftR local lifecycle complete.

python scripts/public_readiness_check.py
# ShyftR public readiness check: PASS

git diff --check
# exit 0

bash scripts/check.sh
# 755 passed; console build passed; npm audit found 0 vulnerabilities; public readiness PASS; terminology guards passed.

bash scripts/alpha_gate.sh
# ALPHA_GATE_READY
```

## Open decisions

- Remote push remains human-gated.
- Future removal of legacy aliases remains human-gated.
