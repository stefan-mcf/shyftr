# Phase 9 integration adapters closeout

Status: local Phase 9 implementation complete; Phase 10 local gate opened by operator review.

Recorded: 2026-05-06T13:22:05Z

Pre-implementation base SHA: `87492cbbffd7f95cbfd557b13211743de317bc1d`

Research and plan artifacts:

- research artifact: `2026-05-06-phase-9-integration-adapters-research.md`
- `docs/plans/2026-05-06-phase-9-integration-adapters-plan.md`

## Scope implemented

Phase 9 was adapted after research rather than implemented literally from the older phased plan.

Implemented:

- generic evidence adapters for markdown notes, raw text, chat summaries, task summaries, issue comments, and tool logs;
- closeout artifact adapter for public-safe local Markdown/JSON handoff artifacts;
- generic `SourceAdapter` ingest path that preserves deterministic source keys, boundary checks, source ledger truth, and external provenance;
- retrieval usage log contract for generic clients, exposed by Python API and local HTTP `/retrieval-logs` route with automatic `/v1/retrieval-logs` alias;
- tests covering idempotent ingestion, regulator rejection, artifact preservation, retrieval-log sanitization, and adapter plugin discovery;
- repo-local research, execution plan, and this status record.

Not implemented and intentionally blocked:

- Phase 10 metrics;
- Phase 10 decay scoring;
- Phase 10 proof-of-work/demo work;
- hosted service or production posture;
- stable-release wording;

## Adaptations from research

The older Phase 9 plan referenced a generic evidence adapter concept before Phase 8 had stabilized the adapter SDK. The implementation therefore reuses the existing `SourceAdapter` protocol instead of adding a parallel protocol.

Key adaptations:

- adapters materialize inline evidence into deterministic local evidence snapshots before ingestion;
- adapter provenance remains metadata on source ledger rows, while memory promotion remains review-gated;
- ingestion is idempotent by content hash plus stable external reference;
- closeout artifacts are artifact-first and are never modified by ingestion;
- retrieval usage logs are exposed as usage evidence only, not effectiveness metrics.

## Local acceptance evidence

Local checks to run before committing this closeout:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python scripts/terminology_inventory.py --fail-on-public-stale
.venv/bin/python scripts/terminology_inventory.py --fail-on-capitalized-prose
.venv/bin/python scripts/public_readiness_check.py
git diff --check
bash scripts/alpha_gate.sh
```

Observed local results before this status file was committed:

- full Python suite: `881 passed`;
- targeted Phase 9 test file: included in full suite (`tests/test_phase9_integration_adapters.py`);
- terminology inventory, public stale terms: PASS;
- terminology inventory, capitalized prose: PASS;
- public readiness check: PASS;
- whitespace diff check: PASS;
- alpha gate: `ALPHA_GATE_READY`;
- console build inside alpha gate: passed;
- production dependency audit inside alpha gate: `0 vulnerabilities`.

Exact-SHA CI evidence must be recorded after commit/push.

## Operator gate

Phase 9 acceptance is human-in-the-loop with the operator as the human reviewer. The tested local implementation, local gates, exact-SHA CI, and operator decision are sufficient to open the next local implementation phase.

The former external-report collection path has been removed as a phase gate. Public reports may still be filed as normal issues, but they are advisory inputs rather than gate requirements.

## Stop point

Phase 9 local implementation is complete. Phase 10 local implementation is opened by `docs/status/phase-10-operator-gate.md`. Stop before Checkpoint E/F, stable-release, hosted-service, production, or private-core-heavy claims unless separately approved by the operator.
