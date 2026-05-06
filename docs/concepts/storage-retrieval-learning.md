# Storage, Retrieval, and Learning Rail

ShyftR is a file-backed, auditable memory-cell substrate. Databases and vector stores accelerate retrieval, while Cell ledgers remain canonical truth.

Canonical storage and application vocabulary:

- ShyftR Cell: a bounded attachable memory unit.
- Regulator: the review and policy layer controlling admission, promotion, retrieval, and export.
- Cell Ledger: the append-only canonical truth inside a Cell.
- Charge: a reviewed durable memory item.
- Grid: the rebuildable retrieval and index layer.
- Pack: the bounded memory bundle supplied to an agent or runtime.
- Signal: the pulseback record that tells ShyftR whether retrieved memory helped or harmed.

## Storage rail

The Cell Ledger is canonical truth. It lives in append-only, replayable files:

```text
cells/<cell_id>/memory/
  ledger/
    pulses.jsonl
    sparks.jsonl
    reviews.jsonl
    promotions.jsonl
    retrieval_logs.jsonl
    signal.jsonl
  charges/
    approved.jsonl
    decayed.jsonl
  coils/
    proposed.jsonl
    approved.jsonl
  rail/
    proposed.jsonl
    approved.jsonl
```

The Grid is rebuildable acceleration. It materializes retrieval/index views from the Cell Ledger:

```text
cells/<cell_id>/memory/
  grid/
    metadata.sqlite
    sparse.sqlite
    vectors.sqlite
```

Golden rule:

```text
Cell ledgers are truth.
The Grid is acceleration.
The Pack is application.
Signal is learning.
Charge confidence is evolution.
```

## Recommended MVP database stack

Use this for the first implementation:

- JSONL append-only ledgers for canonical truth
- SQLite in WAL mode for metadata, audit views, and query materialization
- SQLite FTS5 for sparse/BM25 retrieval
- sqlite-vec for local vector retrieval
- local embedding provider interface, with deterministic test embeddings

Why this stack:

- local-first
- inspectable
- portable
- no server required
- fast enough for early Cells
- easy proof-of-work story
- indexes can be rebuilt from ledgers

Future adapters can support LanceDB or Qdrant for larger deployments, but they should remain optional indexes rather than canonical stores.

## Retrieval rail

ShyftR should not retrieve nearest text. ShyftR should retrieve the safest, most relevant, most proven memory for the current agent/task.

Retrieval should be hybrid and trust-aware:

1. Cell scope filter
2. trust-tier filter
3. type/kind filter
4. sparse search
5. dense vector search
6. symbolic tag match
7. confidence/signal weighting
8. optional reranking
9. bounded Pack assembly

Suggested trust tiers:

- Tier 1: Rail — shared promoted rules
- Tier 2: Charges — reviewed durable memory
- Tier 3: Coils — recursively distilled patterns
- Tier 4: Sparks — candidate memory, background-only unless approved
- Tier 5: Pulses — raw evidence only

A Pack must label trust tiers clearly. Sparks must never masquerade as Charges. The Regulator applies scope, trust, token, and export limits before a Pack can be supplied to an agent or runtime.

### Role-labeled Pack assembly

Pack assembly separates retrieved memory into explicit roles so an attached runtime can apply guidance without losing warnings or provenance:

- `guidance_items`: action-oriented Charges and Rails the agent should apply.
- `caution_items`: failure signatures, anti-patterns, supersession warnings, and other negative-space Charges that should shape safe behavior.
- `background_items`: supporting Coils, Sparks, and contextual evidence that may help interpretation.
- `conflict_items`: items flagged as contradictory or requiring review before use.

Caution items carry the same trust tier, kind, confidence, score, and provenance as guidance items. The Pack budget reserves bounded space for caution while preserving the total item and token caps, so warnings cannot crowd out all action guidance. Retrieval logs record candidate IDs, selected IDs, caution IDs, suppressed IDs, and per-item score traces for later Sweep and Signal analysis.

## Signal learning rail

Every agent run should eventually produce Signal. Signal teach ShyftR whether retrieved memory helped or harmed.

Recommended `signal.jsonl` fields:

```json
{
  "signal_id": "tel_...",
  "cell_id": "core",
  "task_id": "task_...",
  "pack_id": "pack_...",
  "retrieved_charge_ids": [],
  "applied_charge_ids": [],
  "useful_charge_ids": [],
  "harmful_charge_ids": [],
  "missing_memory": [],
  "result": "success|failure|partial|unknown",
  "verification_evidence": [],
  "pulseback": [],
  "error_signatures": [],
  "created_at": "..."
}
```

Charge confidence should rise when a Charge is retrieved, applied, and followed by verified success. It should fall when a Charge is applied and followed by failure, contradicted, superseded, or marked harmful.

## Automatic learning regulator

ShyftR should automate discovery but gate durable authority. These gates are the Regulator in practice: admission checks before Pulses become usable, review gates before Sparks become Charges, retrieval filters before Packs leave the Cell, and explicit review before shared Rails or external proposals gain authority.

Automatic:

- Pulse capture
- Spark extraction
- regulator checks
- duplicate detection
- clustering
- confidence scoring
- Coil proposals
- decay proposals
- index rebuilds

Gated:

- Charge promotion
- Rail promotion
- destructive deprecation
- policy changes shared between Cells

This keeps agents learning constantly without allowing unreviewed noise to become durable authority.

## Learning from success and failure

ShyftR should learn from mistakes and successes. Charge kinds should include:

- success_pattern
- failure_signature
- anti_pattern
- recovery_pattern
- verification_heuristic
- routing_heuristic
- tool_quirk
- escalation_rule
- preference
- constraint
- workflow
- rail_candidate

A high-quality failure learning loop usually separates:

- failure_signature: how to recognize the problem
- anti_pattern: behavior that caused or worsened it
- recovery_pattern: what fixed it
- verification_heuristic: how to prove it is fixed

## Cross-Cell resonance

If similar Sparks, Charges, or Coils recur across Cells, ShyftR should detect resonance and propose stronger learning.

Example:

```text
core Cell sees a verification-provenance Spark
project Cell sees the same pattern
agent Cell sees the same pattern
domain Cell sees the same pattern
  -> propose Coil
  -> if reviewed and broadly useful, propose Rail
```

Resonance should increase promotion readiness but should not bypass review.

## Runtime integration

ShyftR Cells are designed to attach to any external agent runtime. The
[runtime integration contract](runtime-integration-contract.md)
defines the four flows (Pulse ingest, Pack request, Signal report, and
Proposal review/export), the external identity fields that link runtime state
to ShyftR memory, idempotency requirements for file and JSONL ingest, and the
safety regulator that keeps ShyftR proposing and the runtime applying.

This contract is runtime-agnostic. It contains no assumptions about any
specific agent framework, queue system, worker model, or transport protocol.

## Universal memory substrate contracts

The universal substrate scope extends the same storage, retrieval, and learning
rail to agent-memory providers and knowledge workspaces. The core remains the
Cell ledger model:

```text
Cell ledgers are truth.
The Grid is acceleration.
Packs, profiles, markdown pages, documents, dashboards, and summaries are
applications or projections.
```

The [universal memory substrate](universal-memory-substrate.md) scope defines
ShyftR as a local-first memory substrate while keeping orchestration, note
editing, hosted collaboration, and vector storage as optional external surfaces
or adapters. The [memory provider contract](memory-provider-contract.md)
defines ShyftR-native compatibility for `remember`, `search`, `profile`,
`forget`, `replace`, `deprecate`, `pack`, `record_signal`,
`import_memory_export`, and `export_memory_snapshot`. The
[knowledge workspace contract](knowledge-workspace-contract.md) defines
compatibility for note ingest, note sync, document ingest, backlinks, topic and
project projections, review queues, and markdown export.

These contracts are category-level. Adapters may map named tools into the
contracts, but public ShyftR docs should describe capability categories rather
than product-specific comparisons. Generated profiles, snapshots, markdown,
documents, dashboards, and indexes remain rebuildable outputs derived from Cell
ledgers.

The first UMS implementation pass exposes the direct provider API under
`shyftr.provider`. That pass implements `remember`, `search`, `profile`,
`forget`, `replace`, and `deprecate` as a narrow provider surface over Cell
ledgers. UMS-2 adds `remember_trusted` and `TrustedMemoryProvider` as a narrow
trusted explicit-memory surface: callers must supply actor, trust reason, Pulse
channel, and creation time; trusted writes still pass Regulator pollution checks;
and promotion remains provenance-linked through Source/Pulse, Fragment/Spark,
review, promotion, Charge, and Trace rows. ShyftR does not move canonical truth
into profile text, search indexes, trusted-call metadata, or external runtime
state. Later UMS tranches cover profile projection hardening, lifecycle
semantics, Pack and Signal wrappers, and import/export compatibility.
