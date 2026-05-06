# Runtime Integration Contract

ShyftR is a runtime-agnostic memory-cell substrate. Any external agent runtime can
attach a ShyftR Cell by implementing four integration flows. This document defines
the contract: what each flow requires, what external runtimes own versus what ShyftR
owns, the identity fields that link external state to ShyftR memory, and the safety
regulator between proposing and applying.

## The four integration flows

```text
External runtime -> Pulses          -> ShyftR Cell
External runtime <- Packs         <- ShyftR Cell
External runtime -> Signal         -> ShyftR Cell
External runtime <- Proposals        <- ShyftR Cell
```

### 1. Pulse ingest

The external runtime sends evidence to ShyftR: task closeouts, tool logs, chat
transcripts, review notes, verification output, or any other material that may
contain durable lessons.

Pulse ingest must include:

- **Pulse text or content** — the raw evidence
- **Pulse kind** — one or more labels such as `closeout`, `log`, `note`,
  `transcript`, `review`, `artifact`, `error`
- **Pulse kind map** — maps the external runtime's notion of a pulse kind to
  ShyftR's pulse kind vocabulary; two basic kinds are `file` and `jsonl_row`
- **External references** — see [External identity fields](#external-identity-fields)

ShyftR accepts the Pulse, stores it in an append-only ledger, and then extracts
candidate Sparks. Pulses themselves do not become durable memory — only reviewed
Sparks promoted to Charges do.

### 2. Pack request

Before beginning work, the external runtime asks ShyftR for applicable memory.

A Pack request must include at minimum:

- **Cell identifier** — which ShyftR Cell to query
- **Query or task description** — natural language or structured description of
  the upcoming work
- **External identity fields** — see below

Optional request fields:

- **Task kind** — a label the runtime uses to classify work
- **Tags** — additional filter labels
- **Max items or tokens** — bound the Pack size
- **Requested trust tiers** — for example, Rail only, Charges + Rail, or
  include Sparks as background

ShyftR returns a Pack: a bounded, trust-labeled memory bundle containing:

- **Guidance items** — Charges, Rail rules, or Coils likely to help
- **Caution items** — failure signatures, anti-patterns, or expired rules that
  warn against repeating past mistakes
- **Background items** — lower-confidence or candidate-level context (Sparks
  or unverified material)
- **Conflict items** — if memory disagrees, both sides are shown
- **Risk flags** — if the query touches a known high-risk or fragile domain

Every Pack item includes:

- A stable unique ID
- A trust tier label (Pulse, Spark, Charge, Coil, Rail)
- Confidence score
- Memory kind (success_pattern, failure_signature, anti_pattern, etc.)
- Provenance references back to the original Pulse

### 3. Signal report

After work completes, the external runtime tells ShyftR what happened.

An Signal report must include at minimum:

- **Pack ID** — which Pack was used
- **External identity fields** — see below
- **Result** — one of: `success`, `failure`, `partial`, or `unknown`

Optional report fields:

- **Applied Charge IDs** — which retrieved memory items were actually used
- **Useful Charge IDs** — which items actively helped
- **Harmful Charge IDs** — which items misled or caused problems
- **Ignored Charge IDs** — which items were retrieved but set aside
- **Violated caution IDs** — if a caution was present and violated
- **Missing memory notes** — what the runtime wished ShyftR had known
- **Verification evidence** — output references or digests that prove the result
- **Runtime metadata** — any additional runtime-specific context

ShyftR stores the Signal in an append-only Signal ledger, then adjusts Charge
confidence scores: rising for applied-and-successful items, falling for
applied-and-failed or harmful items.

### 4. Proposal review and export

ShyftR periodically generates proposals: suggestions for new Charges, Coils,
Rail updates, deprecation candidates, or process improvements. Proposals
are not automatically applied — they are exported for human or manager review.

Proposals typically arise from:

- Recurring Spark patterns that suggest a new Charge
- Multiple related Charges that could be consolidated into an Coil
- Cross-Cell resonance that suggests Rail promotion
- Decay signals that suggest deprecation or supersession
- Repeated Signal patterns that reveal a systemic gap

The external runtime or its operator reviews proposals and decides whether to
accept, reject, or defer each one. ShyftR mutates durable memory only after
review approval.

#### Runtime proposal export contract

Runtime proposal export uses a stable JSON object with contract identifier
`shyftr.runtime_proposals.v1`. Each exported proposal is advisory data, not an
instruction to mutate a runtime.

A `RuntimeProposal` contains:

| Field | Required | Description |
|---|---|---|
| `proposal_id` | Yes | Stable proposal identifier |
| `proposal_type` | Yes | One of the supported advisory proposal types |
| `target_external_system` | Yes | Runtime system identifier supplied by the adapter |
| `target_external_scope` | Yes | Runtime scope within that system |
| `target_external_refs` | No | Structured external references such as task, file, issue, or policy references |
| `recommendation` | Yes | Human-readable advisory recommendation |
| `evidence_charge_ids` | No | Charge IDs that support the proposal |
| `evidence_pulse_ids` | No | Pulse IDs that support the proposal |
| `confidence` | Yes | Confidence score from `0.0` to `1.0` |
| `review_status` | Yes | `pending`, `accepted`, `rejected`, or `deferred` |
| `created_timestamp` | Yes | Timestamp for proposal creation |
| `metadata` | No | Additional structured context |

Supported proposal types are:

- `memory_application_hint`
- `routing_hint`
- `verification_hint`
- `retry_caution`
- `policy_change_candidate`
- `missing_memory_candidate`

The default export includes only `pending` and `deferred` proposals. Accepted
proposals may be included explicitly for audit or synchronization, but accepted
status still means that review happened elsewhere; export alone never applies a
proposal.

CLI contract:

```bash
shyftr proposals export --cell <path> --external-system <id> --json
```

The response includes:

- `advisory_only: true`
- `requires_external_review: true`
- `mutates_external_runtime: false`
- a `proposals` array containing provenance-linked `RuntimeProposal` objects

ShyftR may write an export file inside the Cell when an output path is supplied,
but it must not edit external runtime policy files, queues, task state, or
configuration as part of proposal export.

### Optional adapter plugins

ShyftR core includes a built-in file/JSONL adapter for local Pulse ingest. Other
runtime adapters can live in separate Python packages and advertise themselves
through the `shyftr.adapters` entry point group.

Adapter plugin metadata includes:

| Field | Description |
|---|---|
| `name` | Stable adapter name shown by ShyftR |
| `version` | Adapter package or metadata version |
| `supported_input_kinds` | Input kinds such as `file`, `glob`, `jsonl`, or `directory` |
| `config_schema_version` | ShyftR adapter config schema version supported by the adapter |
| `description` | Human-readable adapter summary |
| `adapter_class` | Optional import path for the adapter implementation |

The CLI command for discovery is:

```bash
shyftr adapter list --json
```

Discovery is introspection-only. Listing plugins must not ingest Pulses, mutate
Cell ledgers, edit runtime policy, or require optional adapter dependencies to be
installed for ShyftR core imports to succeed.

Third-party packages can register adapters with packaging metadata such as:

```toml
[project.entry-points."shyftr.adapters"]
custom-runtime = "custom_runtime_shyftr:adapter_plugin"
```

The entry point should return adapter metadata; actual runtime-specific adapter
code can remain outside ShyftR core.

## Runtime regulator: who owns what

### External runtime responsibilities

The external runtime owns all operational execution:

- Task scheduling and dispatch
- Active task state and queue management
- Worker or agent execution
- Model and backend selection
- Retry and error handling
- Monitoring and alerting
- Runtime-specific policy files and configuration
- Immediate safety decisions

### ShyftR responsibilities

ShyftR owns durable learning:

- Pulse capture and append-only persistence
- Spark extraction and provenance linking
- Review-gated Charge promotion
- Trust-labeled Pack assembly and retrieval
- Signal recording and confidence evolution
- Coil and Rail proposal generation
- Audit, hygiene, decay, and recursive distillation

ShyftR may advise a runtime but must not silently control it. All durable
memory mutations are review-gated.

## External identity fields

Every Pulse, Pack request, and Signal report must carry stable external
identity fields so ShyftR can correlate memory across runs and systems.

| Field | Required | Description |
|---|---|---|
| `external_system` | Yes | Name of the external runtime (for example `runtime-a`, `batch-runner`, or `custom-agent`) |
| `external_scope` | Yes | Scope within that system (for example `project-alpha`, `user-profile`, or `team-engineering`) |
| `external_run_id` | Yes | Unique identifier for this run or execution attempt |
| `external_task_id` | Yes | Unique identifier for the task being executed |
| `external_refs` | No | Optional list of additional references (URLs, file paths, issue IDs, etc.) |

These fields are metadata only — they enable provenance tracing and cross-system
deduplication. ShyftR must not treat them as durable lesson content.

## Idempotency requirements

### File ingest

Ingesting the same file twice must produce exactly one Pulse record. Content
hash is the deduplication key. If the file content changes, the new content
produces a new Pulse; the old Pulse remains unchanged.

### JSONL ingest

Each JSONL row has a stable identity based on:

- **File path**
- **Byte offset or line number**
- **Row content hash**

Ingesting the same JSONL file twice must not duplicate previously ingested rows.
New rows appended to the file must be ingested incrementally without re-processing
already-ingested rows.

### Sync state

For append-only external files, ShyftR maintains per-adapter sync state:

- Adapter ID
- Pulse path
- Last ingested byte offset
- Last ingested line number
- Last content hash
- Last sync timestamp

Sync state is stored alongside the Cell's configuration. File truncation or
rotation triggers a safety check that requires explicit reset or backfill before
new ingestion proceeds.

## Safety regulator

```text
ShyftR proposes. The runtime applies.
```

- ShyftR generates proposals for new Charges, Coils, Rail updates, and
  deprecation candidates.
- Proposals are exported for review — they are not automatically committed to
  durable memory.
- The external runtime or its operator reviews proposals and decides what to
  accept, reject, or defer.
- ShyftR must never directly mutate the external runtime's task queue, worker
  policy, configuration, or operational state.
- Active execution state is never durable memory. Operational facts such as
  "task X is in progress" or "worker Y holds branch Z" belong in the runtime's
  own state management, not in ShyftR's Cells.

This regulator holds even when ShyftR is embedded in the same process as a
runtime. The separation is logical, not topological.

## Relationship to the ShyftR vocabulary

This contract uses ShyftR's canonical terms for all durable memory concepts:

- **Pulse** — raw evidence sent from a runtime
- **Spark** — bounded candidate memory extracted from a Pulse
- **Charge** — reviewed, promoted durable memory
- **Coil** — recursively distilled pattern from multiple Charges
- **Rail** — shared promoted rule
- **Cell** — isolated, attachable memory namespace
- **Grid** — retrieval indexes and acceleration layer
- **Pack** — bounded memory bundle returned before work
- **Signal** — learning signal returned after work
- **Proposal** — review-gated suggestion for memory mutation

No runtime-specific product names, queue terminology, worker framework labels,
or transport details appear in these terms.
