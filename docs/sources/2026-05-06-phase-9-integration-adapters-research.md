# Phase 9 integration adapters research

Status: source/research note for adapting Phase 9 before implementation.

Recorded: 2026-05-06

## Scope

This research pass reviewed Phase 9 integration adapters before implementation. It used the source Phase 9 plan in `docs/plans/2026-04-24-shyftr-phased-plan.md`, the current Phase 8 adapter SDK/API implementation, and an external-pattern research lane covering adapter/port design, provenance, idempotency, bounded retrieval, failure isolation, telemetry, and evidence gates.

Stop scope: implement Phase 9 only through the operator gate. Do not begin Phase 10 metrics, decay, or proof-of-work demo work until the operator opens that scope.

## Source plan summary

Original Phase 9 tasks:

1. generic evidence adapters for direct notes, chat summaries, task closeouts, issue comments, and tool logs;
2. domain/task closeout adapter;
3. retrieval bundles with generic clients.

The original plan predates the Phase 8 adapter SDK and `/v1` API contract, so it needs adaptation rather than literal execution.

## Research findings

Recommended design principles:

- Treat integrations as ports/adapters: keep a small protocol and let concrete adapters produce ShyftR canonical payloads.
- Preserve provenance at the adapter edge: source URI, adapter id, external ids, source kind, and deterministic content hash.
- Make ingestion idempotent with content hash plus stable external reference metadata.
- Keep external runtimes from mutating canonical truth directly; adapters only provide evidence, then the ShyftR regulator/review path decides promotion.
- Keep retrieval bounded by explicit request limits and trust tiers, and expose retrieval usage logs as a contract for clients.
- Isolate adapter failures: a broken adapter should return an error record/summary and must not corrupt the closeout artifact or cell ledgers.
- Keep telemetry operational and schema-bounded in Phase 9; do not start Phase 10 effectiveness metrics or decay scoring.

Relevant public patterns reviewed:

- Hexagonal architecture / ports and adapters: keep the source protocol stable and concrete adapters swappable.
- W3C PROV and content-addressable systems: preserve lineage and deterministic hashes.
- Event-sourcing/idempotency patterns: append canonical events, deduplicate on stable keys, preserve auditability.
- Bounded RAG/context patterns: return pack/loadout content with explicit limits and selected ids.
- OpenAPI/consumer contracts: expose stable local `/v1` routes and schemas for external clients.
- Circuit-breaker/bulkhead patterns: isolate adapter failures from the rest of the pipeline.

## Adaptations applied to Phase 9

### Adaptation 1: reuse `SourceAdapter`

Do not add a new `memoryevidenceAdapter` protocol. That name is stale and would duplicate the existing runtime-neutral `SourceAdapter` contract in `src/shyftr/integrations/protocols.py`.

Phase 9 should add concrete evidence adapters that implement the existing `SourceAdapter` protocol.

### Adaptation 2: implement generic evidence as a source adapter layer

The existing `FileSourceAdapter` already covers files, globs, JSONL rows, and directories. Phase 9 should add a higher-level generic evidence adapter for inline or closeout-like evidence types:

- markdown note;
- raw text;
- chat summary JSON;
- task closeout markdown;
- issue comment;
- tool log.

The adapter should materialize inline evidence to deterministic local snapshots so downstream extraction still has a source URI to read.

### Adaptation 3: keep closeout attachment artifact-first

Do not couple Phase 9 to a private runtime. The public-safe closeout adapter should read closeout artifacts from a configured local folder and ingest them as evidence. External runtimes can write closeout artifacts and call the ShyftR CLI/API after closeout; ingestion failures must not corrupt the original artifact.

### Adaptation 4: expose retrieval logs as a client contract

Phase 9 should not rebuild pack generation. Existing `RuntimeLoadoutRequest` / `RuntimeLoadoutResponse`, `assemble_loadout`, MCP, CLI, and `/pack` already provide bounded retrieval bundles.

The missing Phase 9 improvement is exposing retrieval usage logs as a stable local client contract so external clients can audit which memory ids were selected and whether limits were applied.

### Adaptation 5: define the operator gate

Phase 9 should stop when local implementation is complete and the repo has recorded operator acceptance or a remaining operator blocker.

Evidence for operator review:

- the tested local adapter path writes or reads a public-safe closeout/evidence artifact;
- it is ingested through the Phase 9 adapter path;
- it requests a bounded pack through the generic client contract;
- it records feedback without private data;
- the result is recorded in a public-safe status artifact.

Until the operator opens the next scope, do not proceed to Phase 10.

## Revised Phase 9 implementation outline

1. Add generic evidence adapters that implement `SourceAdapter`.
2. Add a generic ingest function for any `SourceAdapter`, not only file-config adapters.
3. Add closeout adapter support for local closeout artifact directories.
4. Add retrieval log read/filter API for generic clients.
5. Add tests proving provenance, idempotency, closeout isolation, retrieval-log filtering, and no raw operational state leakage.
6. Add status docs for Phase 9 operator acceptance.
7. Stop before Phase 10.
