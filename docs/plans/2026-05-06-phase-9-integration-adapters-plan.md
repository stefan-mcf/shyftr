# Phase 9 integration adapters plan

Status: executable Phase 9 plan adapted after research.

Recorded: 2026-05-06

Source research:

- `docs/sources/2026-05-06-phase-9-integration-adapters-research.md`

Source plan:

- `docs/plans/2026-04-24-shyftr-phased-plan.md`, Phase 9.

## Scope

Implement public-safe Phase 9 integration adapter logic through the external evidence gate.

Allowed:

- generic evidence adapters using the existing `SourceAdapter` protocol;
- closeout artifact adapter;
- generic ingest function for arbitrary source adapters;
- retrieval usage log contract for local HTTP clients;
- tests, docs, and status evidence.

Blocked:

- Phase 10 metrics;
- Phase 10 decay scoring;
- Phase 10 proof-of-work demo;
- Checkpoint E/F release posture changes;
- hosted-service, production, or private-core claims;
- real private runtime data.

## Tranche 9.1: generic evidence source adapters

Objective: support direct notes, raw text, chat summaries, task closeouts, issue comments, and tool logs without adding a new protocol.

Implementation:

- create `src/shyftr/integrations/evidence_adapters.py`;
- implement `EvidenceDocument` and `GenericEvidenceAdapter` over the existing `SourceAdapter` protocol;
- provide factory helpers for markdown notes, raw text, chat summaries, closeout markdown, issue comments, and tool logs;
- materialize inline evidence to deterministic local snapshots so downstream extraction can read from a source URI;
- preserve adapter id, external system/scope, source kind, source URI, external ids, content hash, and metadata.

Acceptance:

- all generic evidence adapter variants produce `ExternalSourceRef` and `SourcePayload` records;
- content hashes are deterministic;
- adapter harness passes;
- no new legacy protocol or stale public vocabulary is introduced.

## Tranche 9.2: generic source-adapter ingest path

Objective: allow any `SourceAdapter` implementation to append evidence to a cell without going through a file config wrapper.

Implementation:

- add `ingest_sources_from_adapter(cell_path, adapter, dry_run=False)` to `src/shyftr/ingest.py`;
- reuse the existing boundary check, source-key deduplication, source ledger append, and cell id validation;
- return counts, discovery summary, source ids, skipped keys, and errors;
- preserve source ledger truth and do not mutate external artifacts.

Acceptance:

- generic evidence adapters ingest into `ledger/sources.jsonl`;
- repeated ingestion skips already-seen adapter source keys;
- boundary-rejected evidence returns an error and does not append a source;
- extraction can read the materialized snapshot and create candidate fragments.

## Tranche 9.3: closeout evidence adapter

Objective: attach ShyftR to generic task/domain closeout flows by reading closeout artifacts as evidence.

Implementation:

- create `src/shyftr/integrations/closeout_adapter.py`;
- discover Markdown and JSON closeout artifacts from a configured directory;
- treat the source artifact as immutable external evidence;
- preserve provenance and closeout-specific metadata;
- document that external runtimes should write the closeout artifact first, then call ShyftR ingestion.

Acceptance:

- closeout files ingest through `SourceAdapter -> ingest_sources_from_adapter -> extract_fragments`;
- ingestion failures do not edit or corrupt the original closeout artifact;
- tests cover both Markdown and JSON closeout artifacts.

## Tranche 9.4: retrieval usage log contract

Objective: make retrieval bundle usage auditable to generic clients without starting Phase 10 metrics.

Implementation:

- create `src/shyftr/integrations/retrieval_logs.py`;
- expose bounded read/filter of `ledger/retrieval_logs.jsonl` by loadout id, query, selected memory id, and limit;
- sanitize returned records to public contract fields only;
- add `GET /retrieval-logs` which is automatically aliased under `/v1/retrieval-logs`;
- document that this is usage evidence, not effectiveness scoring.

Acceptance:

- retrieval logs are readable via Python API and local HTTP route;
- returned records contain selected memory ids and score traces but no raw operational state payloads;
- tests prove filtering and sanitization.

## Tranche 9.5: status and external evidence gate

Objective: record local Phase 9 completion and stop at the external evidence gate.

Implementation:

- create `docs/status/phase-9-integration-adapters-closeout.md`;
- update `docs/status/tranched-plan-status.md` and roadmap/status references as needed;
- if useful, add or refresh a GitHub tracker for external Phase 9 adapter evidence.

Local close condition:

- full test suite passes;
- terminology guards pass;
- public readiness passes;
- alpha gate passes;
- exact-SHA CI is green after push.

External evidence gate:

Stop before Phase 10 until a public-safe external runtime or non-operator integration has recorded evidence that it can:

1. write a closeout/evidence artifact;
2. ingest it through the Phase 9 adapter path;
3. request a bounded pack through the generic client contract;
4. report feedback;
5. provide exact SHA, environment, commands, result, friction, and public-safe failures.

Do not claim external Phase 9 validation until that evidence is recorded and reviewed.
