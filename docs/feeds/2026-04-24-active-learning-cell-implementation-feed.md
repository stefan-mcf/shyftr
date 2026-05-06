# Active Learning cell Implementation evidence

Status: review evidence, not yet merged into the tranche plan.

Purpose: turn the active-learning ideas into implementable ShyftR design evidence material. This document is intentionally detailed so it can be reviewed, edited, and later migrated into the implementation tranche plan.

## Executive summary

ShyftR should evolve from file-backed memory storage into an active recall-and-learning cell substrate.

The core rule remains unchanged:

```text
cell ledgers are truth.
The grid is acceleration.
The pack is application.
feedback is learning.
memory confidence is evolution.
```

The additions proposed here are:

1. Negative-space retrieval: use `failure_signature` and `anti_pattern` memories to warn against unsafe or stale approaches.
2. pack Miss logging: record when a memory is loaded but not applied, so retrieval quality can improve over time.
3. Sweep maintenance pass: asynchronously inspect retrieval logs, packs, feedback, and audit records to propose confidence and retrieval-affinity changes.
4. Challenger audit loop: actively search for counter-evidence against high-impact memories and create Audit candidates when contradictions or supersessions are found.
5. Disk grid scale path: preserve the current SQLite-first MVP while defining an adapter path for larger disk-backed vector indexes such as LanceDB.

The near-term implementation should not allow background workers to silently rewrite durable truth. The first versions should append evidence and proposals. Accepted changes should be represented as ledger events and then materialized into rebuildable indexes.

## Design principles

### 1. Background workers propose; ledgers decide

Maintenance jobs may detect stale logic, conflicts, misses, or scale pressure, but they should not directly mutate canonical memory authority in early versions.

Allowed automatically:

- append retrieval records
- append pack records
- append feedback records
- append audit/proposal records
- rebuild grid indexes
- compute derived views and reports

Review-gated initially:

- memory promotion
- rule promotion
- destructive deprecation
- quarantine of high-confidence memories
- policy changes shared between cells
- irreversible confidence collapse

Later, low-risk automatic adjustments can be allowed by explicit policy.

### 2. Confidence and retrieval fitness are separate feedbacks

A memory can be true but over-retrieved.

Example: a memory saying "this project uses pytest" may be correct, but if it appears in many non-testing packs and is never applied, the system should reduce its retrieval affinity for those query clusters rather than lowering its global truth confidence.

Therefore ShyftR should distinguish:

- memory confidence: belief that the memory is true, useful, and still valid.
- Retrieval affinity: how strongly the memory should match a query/task cluster.
- pack utility: how often the memory helps when placed into an agent context.
- feedback value: whether applying the memory correlated with verified success or failure.

### 3. Negative memory should surface warnings

Anti-patterns and failure signatures should do more than subtract from scores. Often they should be surfaced as explicit Caution items in the pack.

A task can be valid while one approach to the task is dangerous.

Example: a query about repository work may retrieve both:

- positive guidance: use the active private R&D repo
- caution guidance: do not use the reserved public repo for active implementation

The pack should contain both the action guidance and the warning.

### 4. The grid stays rebuildable

All retrieval acceleration remains disposable. If an embedding model, index backend, scoring formula, or quantization strategy changes, the grid can be rebuilt from canonical cell ledgers.

Scale adapters should not become the product identity. ShyftR remains a file-backed, auditable memory-cell substrate.

## Proposed data model additions

### memory kinds

The existing learning rule already names several memory kinds. The active-learning loop should rely on these in retrieval and audit scoring:

- `success_pattern`
- `failure_signature`
- `anti_pattern`
- `recovery_pattern`
- `verification_heuristic`
- `routing_heuristic`
- `tool_quirk`
- `escalation_rule`
- `preference`
- `constraint`
- `workflow`
- `rule_candidate`

Additional optional kinds for review:

- `supersession`: records that an older memory has been replaced by a newer one.
- `scope_exception`: records that a memory is only wrong outside a particular scope.
- `audit_finding`: records a reviewed audit result.

### memory status values

Current and future retrieval should understand these states:

- `approved`: reviewed durable memory.
- `challenged`: audit evidence exists but no final action is accepted yet.
- `quarantine_candidate`: strong unresolved concern; should be avoided or shown with warning.
- `quarantined`: not used in normal packs; retained for provenance and audit.
- `superseded`: replaced by a newer memory.
- `deprecated`: retired but retained in history.

Default retrieval should exclude `quarantined`, `superseded`, and `deprecated` except for audit/debug modes. It may include `challenged` or `quarantine_candidate` only with clear labels and penalties.

### Retrieval log expansion

Current retrieval logs record selected IDs and score memories. To support pack Misses and later Sweep logic, retrieval logs should become more explicit.

Proposed `retrieval_logs.jsonl` record:

```json
{
  "retrieval_id": "ret_...",
  "pack_id": "lo_...",
  "cell_id": "core",
  "task_id": "task_...",
  "query": "...",
  "query_kind": "...",
  "query_tags": [],
  "candidate_ids": [],
  "selected_ids": [],
  "caution_ids": [],
  "suppressed_ids": [],
  "score_memories": {
    "memory_...": {
      "positive_similarity": 0.81,
      "negative_similarity": 0.14,
      "confidence_weight": 0.9,
      "feedback_weight": 0.2,
      "decay_penalty": 0.0,
      "final_score": 1.42,
      "selection_reason": "positive_guidance|caution|suppressed|filtered"
    }
  },
  "generated_at": "..."
}
```

Notes:

- `candidate_ids` records items considered before final pack assembly.
- `selected_ids` records positive guidance items placed in the pack.
- `caution_ids` records anti-pattern/failure items placed into the Caution section.
- `suppressed_ids` records candidates not shown because risk or status penalties removed them.
- `score_memories` must remain explainable and deterministic enough to test.

### pack record expansion

A pack should have separate sections rather than a flat list only.

Proposed shape:

```json
{
  "pack_id": "lo_...",
  "cell_id": "core",
  "task_id": "task_...",
  "query": "...",
  "guidance_items": [],
  "caution_items": [],
  "background_items": [],
  "conflict_items": [],
  "total_tokens": 0,
  "generated_at": "..."
}
```

Section semantics:

- `guidance_items`: what the agent should likely apply.
- `caution_items`: what the agent should avoid or treat as risky.
- `background_items`: low-authority or contextual items.
- `conflict_items`: items that reveal unresolved contradiction or scope ambiguity.

For early implementation, this can be represented in the existing pack item model by adding a `pack_role` field:

- `guidance`
- `caution`
- `background`
- `conflict`

### feedback expansion for pack Misses

Current feedback records already include `retrieved_memory_ids`, `applied_memory_ids`, `useful_memory_ids`, and `harmful_memory_ids`. To support pack Misses explicitly, add:

```json
{
  "ignored_memory_ids": [],
  "ignored_caution_ids": [],
  "contradicted_memory_ids": [],
  "over_retrieved_memory_ids": [],
  "pack_misses": [
    {
      "memory_id": "memory_...",
      "miss_type": "not_relevant|not_actionable|contradicted|duplicative|unknown",
      "evidence": "short explanation or verifier reference"
    }
  ]
}
```

Miss types:

- `not_relevant`: the memory did not apply to this task.
- `not_actionable`: true but too vague to use.
- `contradicted`: agent or verifier found it wrong for the task.
- `duplicative`: another memory covered the same guidance better.
- `unknown`: loaded but not used, with no reliable reason.

Important rule: a single pack Miss should not lower global memory confidence by itself. Repeated misses within a query/task cluster should lower retrieval affinity first.

### New proposal ledgers

To keep background jobs append-only and reviewable, add proposal ledgers under `ledger/`:

```text
cells/<cell_id>/memory/ledger/
  confidence_events.jsonl
  retrieval_affinity_events.jsonl
  audit_candidates.jsonl
  audit_reviews.jsonl
```

If the implementation wants fewer files initially, `audit_candidates.jsonl` can carry multiple proposal types. The more explicit structure is easier to inspect and test.

#### Confidence event

```json
{
  "event_id": "conf_...",
  "memory_id": "memory_...",
  "cell_id": "core",
  "event_type": "increase|decrease|no_change|proposal",
  "delta": -0.05,
  "reason": "harmful_feedback|verified_success|contradicted|superseded|stale_logic|review_acceptance",
  "evidence_ids": ["feedback_...", "audit_..."],
  "policy": "manual|automatic_low_risk|proposal_only",
  "created_at": "..."
}
```

#### Retrieval affinity event

```json
{
  "event_id": "aff_...",
  "memory_id": "memory_...",
  "cell_id": "core",
  "query_cluster": "cluster_...",
  "delta": -0.12,
  "reason": "repeated_pack_miss|successful_reuse|over_retrieved|scope_refinement",
  "evidence_ids": ["feedback_...", "ret_..."],
  "created_at": "..."
}
```

#### Audit candidate

```json
{
  "audit_id": "audit_...",
  "target_memory_id": "memory_...",
  "cell_id": "core",
  "finding_type": "direct_contradiction|supersession|scope_exception|environment_specific|temporal_update|ambiguous_counterevidence|policy_conflict|implementation_drift",
  "severity": "low|medium|high|critical",
  "counter_evidence_ids": ["evidence_...", "candidate_...", "feedback_..."],
  "summary": "...",
  "suggested_action": "keep|rewrite|split|lower_confidence|quarantine|supersede|manual_review",
  "status": "proposed|accepted|rejected|resolved",
  "created_at": "..."
}
```

## Feature 1: Negative-space retrieval

### Problem

Ordinary retrieval answers: what should the agent remember?

ShyftR should also answer: what should the agent avoid repeating?

A known failure can be more important than a nearby success. If the current task resembles a known failure, the pack should either warn the agent or suppress risky guidance.

### Design

Hybrid retrieval should run or simulate two retrieval passes:

1. Positive pass: retrieve applicable guidance memories.
2. Negative pass: retrieve `failure_signature`, `anti_pattern`, `supersession`, and high-severity challenged/quarantined items that match the same query.

The reranker combines positive and negative evidence.

Conceptual formula:

```text
final_score =
  alpha * positive_similarity
  + gamma * confidence_weight
  + delta * proven_feedback_weight
  + eta * symbolic_match_weight
  - beta * negative_similarity
  - theta * risk_penalty
```

Where:

- `beta` is the Caution Coefficient.
- `negative_similarity` comes from nearby failure/anti-pattern memories.
- `risk_penalty` comes from status, harmful feedback, or audit severity.

However, high negative similarity should not always hide the memory. It may produce a Caution item.

### pack behavior

For each query:

- Include high-ranking positive memories as `guidance`.
- Include directly relevant `failure_signature` and `anti_pattern` memories as `caution`.
- If a positive memory is semantically close to a high-severity anti-pattern, either:
  - lower its score,
  - include it with a warning,
  - or move it into `conflict` for review.

### Acceptance criteria

- A `failure_signature` memory can appear in the Caution section of a pack.
- An `anti_pattern` memory can reduce the score of a related positive memory.
- Negative-space scoring is explainable in `score_memory`.
- Related failures do not block positive work by default.
- Tests cover a valid task with one good approach and one known bad approach.

### Suggested tests

1. Given a positive workflow memory and a nearby anti-pattern memory, retrieval returns the workflow as guidance and the anti-pattern as caution.
2. Given a high-severity failure with strong similarity, a weak positive memory is suppressed or moved to conflict.
3. Given a failure in a different scope, the positive memory remains guidance and the failure is either ignored or labeled as scoped caution.

## Feature 2: pack Miss logging

### Problem

Current retrieval can learn from success/failure only if it knows which loaded memories were actually used. A memory that is frequently loaded but rarely used may be over-retrieved, too vague, stale, or incorrectly embedded.

### Design

Each feedback should compare:

- IDs placed in the pack
- IDs the agent applied
- IDs verified as useful
- IDs verified as harmful
- IDs explicitly ignored or contradicted

Derived categories:

```text
pack_miss_ids = selected_ids - applied_memory_ids - useful_memory_ids - harmful_memory_ids
```

This raw set needs additional context. The feedback recorder should allow a miss reason when available.

### Miss interpretation

A pack Miss may mean:

- the memory is irrelevant for this query type
- the memory is too generic
- the memory was superseded by another item
- the agent failed to notice useful memory
- the task changed after retrieval
- the memory is stale or wrong

Therefore the first automatic impact should usually be on retrieval affinity, not global confidence.

### Acceptance criteria

- feedback recording stores ignored or non-applied memory IDs.
- Repeated misses can be summarized by memory and query cluster.
- A miss alone does not immediately deprecate a memory.
- pack Misses are visible in hygiene reports.

### Suggested tests

1. If a pack contains three memories and only one is applied, the other two are recorded as misses unless marked useful/harmful another way.
2. If a memory is repeatedly missed for a query tag, the Sweep proposes a retrieval-affinity decrease for that tag/cluster.
3. If a memory is missed but later marked useful by verification, preserve its score.

## Feature 3: Sweep maintenance pass

### Problem

Just-in-time decay during retrieval is simple, but it makes the hot path carry maintenance logic. It also misses cross-run patterns such as over-retrieval, declining application rate, and stale logic.

### Design

Add a low-priority maintenance command:

```text
shyftr sweep --cell <path> [--dry-run] [--apply-low-risk]
```

The Sweep reads:

- `ledger/retrieval_logs.jsonl`
- `ledger/feedbacks.jsonl`
- `ledger/audit_candidates.jsonl`
- `ledger/confidence_events.jsonl`
- approved/deprecated/quarantined memory ledgers

It computes:

- application rate per memory
- useful rate per memory
- harmful rate per memory
- miss rate per memory
- miss rate per memory per query cluster
- stale age since last useful application
- contradiction count
- supersession evidence
- over-retrieval clusters

It emits:

- confidence event proposals
- retrieval-affinity event proposals
- hygiene report entries
- optional index rebuild requests

### Core metrics

For a memory `t`:

```text
retrieval_count(t) = times t was selected in a pack
application_count(t) = times t was applied
useful_count(t) = times t was verified useful
harmful_count(t) = times t was harmful
miss_count(t) = times t was selected but neither applied nor useful/harmful
application_rate(t) = application_count / max(1, retrieval_count)
useful_rate(t) = useful_count / max(1, application_count)
harmful_rate(t) = harmful_count / max(1, application_count)
miss_rate(t) = miss_count / max(1, retrieval_count)
```

Potential stale logic feedback:

```text
stale_logic_score =
  high_similarity_retrievals
  * declining_application_rate
  * low_recent_useful_rate
  * age_weight
```

### Proposed actions

- `retrieval_affinity_decrease`: memory appears often for a cluster but is usually ignored.
- `confidence_decrease`: memory was applied and correlated with verified failure or contradiction.
- `confidence_increase`: memory was applied and correlated with verified success.
- `manual_review`: evidence is ambiguous or high-impact.
- `split_memory`: memory seems too broad and has mixed feedback across scopes.
- `supersession_candidate`: newer memory consistently outperforms older memory.

### Safety policy

Dry run should be the default for early development.

`--apply-low-risk` may append low-risk retrieval-affinity events, but should not quarantine or deprecate memories.

Confidence changes should either:

- be proposals only, or
- be very small automatic events under a configured policy.

### Acceptance criteria

- Sweep can run with no network access.
- Sweep never rewrites existing JSONL records.
- Sweep can produce a deterministic report from fixtures.
- pack Misses can generate retrieval-affinity proposals.
- Harmful applied memories can generate confidence-decrease proposals.
- Useful applied memories can generate confidence-increase proposals.

### Suggested tests

1. A memory retrieved ten times and applied zero times produces an affinity decrease proposal, not a deprecation.
2. A memory applied twice and marked harmful twice produces a confidence decrease proposal.
3. A memory with mixed feedback across different query tags produces a split/scope review proposal.
4. Running Sweep twice does not duplicate identical open proposals.

## Feature 4: Challenger audit loop

### Problem

High-confidence memory can become dangerous if it is wrong, stale, too broad, or contradicted by later evidence. Agents can also pollute memory by promoting weak lessons or over-trusting hallucinated success.

### Design

Add a Challenger audit pass:

```text
shyftr challenge --cell <path> [--memory-id <id>] [--top-impact N] [--dry-run]
```

The Challenger selects target memories based on:

- high confidence
- high retrieval frequency
- high application frequency
- rule promotion readiness
- old age with recent continued use
- recent harmful feedback
- unresolved miss/contradiction feedbacks

It searches for counter-evidence in:

- evidences
- candidates
- feedback
- audit records
- newer memories
- deprecated/superseded memories

It emits Audit candidates rather than directly deleting or demoting memory.

### Finding classification

The Challenger must classify the relationship between the memory and evidence:

- `direct_contradiction`: evidence says the memory is wrong.
- `supersession`: newer evidence replaces older guidance.
- `scope_exception`: memory is valid only in a narrower scope.
- `environment_specific`: memory is true in one environment but false in another.
- `temporal_update`: memory was true before but became stale.
- `ambiguous_counterevidence`: possible conflict but not enough authority.
- `policy_conflict`: memory conflicts with a higher-authority constraint.
- `implementation_drift`: code or docs no longer match the memory.

### quarantine workflow

Suggested statuses:

1. `approved`: normal use.
2. `challenged`: Audit candidate exists.
3. `quarantine_candidate`: high-severity unresolved concern.
4. `quarantined`: excluded from normal retrieval.
5. `superseded` or `deprecated`: retired with provenance.

Initial implementation should only append `challenged` findings and report quarantine candidates. quarantine itself should be review-gated.

### Acceptance criteria

- Challenger can identify high-impact memories for audit.
- Challenger emits Audit candidates with counter-Evidence IDs.
- Challenger distinguishes contradiction from scope exception or supersession.
- Normal retrieval can penalize or label challenged memories.
- No memory is deleted by Challenger.

### Suggested tests

1. A high-confidence memory contradicted by a later evidence produces a direct contradiction Audit candidate.
2. A memory replaced by a newer memory produces a supersession finding.
3. A memory true for one tool/environment and false for another produces a scope or environment finding.
4. A challenged memory remains in the ledger but is labeled/penalized in retrieval.

## Feature 5: Disk-backed grid scale path

### Problem

The MVP grid can use SQLite, FTS5, and local vector abstractions. Larger cells may eventually need disk-backed vector indexing and approximate search.

### Design

Keep the MVP stack:

- JSONL append-only ledgers for canonical truth
- SQLite WAL for metadata and audit views
- SQLite FTS5 for sparse retrieval
- sqlite-vec or local vector adapter for early vector retrieval
- deterministic test embeddings

Define an adapter interface so future indexes can include:

- LanceDB
- Qdrant
- FAISS-backed local indexes
- other disk-backed vector stores

Do not make these canonical stores. They are grid adapters only.

### Index metadata

Every vector index should record:

```json
{
  "index_id": "idx_...",
  "cell_id": "core",
  "backend": "sqlite_vec|lancedb|qdrant|faiss|memory",
  "embedding_model": "...",
  "embedding_dimension": 0,
  "embedding_version": "...",
  "evidence_ledger_offsets": {},
  "memory_count": 0,
  "created_at": "..."
}
```

If any of these change, the grid should be considered rebuildable/stale.

### Quantization

Product quantization or other compression methods can be future options for large cells. This should be configuration, not rule.

Potential config:

```json
{
  "vector_backend": "lancedb",
  "quantization": {
    "enabled": true,
    "method": "pq",
    "target_recall": 0.99
  }
}
```

Avoid absolute latency promises. Performance depends on hardware, index backend, embedding dimension, filters, cache state, and workload.

### Acceptance criteria

- Vector retrieval uses a `VectorIndex` protocol/interface.
- Index metadata records embedding model/version and backend.
- Rebuild can wipe and recreate the vector index from ledgers.
- Tests remain dependency-free with deterministic embeddings.
- LanceDB or other heavy adapters are optional extras.

## Suggested implementation sequencing

### Near-term sequence

1. Expand models for memory kind/status, pack item role, retrieval IDs, and feedback miss fields.
2. Update pack assembly to support `guidance`, `caution`, `background`, and `conflict` roles.
3. Add negative-space retrieval/reranking using failure and anti-pattern memories.
4. Expand feedback recording to capture applied/ignored/contradicted/missed IDs.
5. Add Sweep dry-run report and proposal ledgers.
6. Add review-gated acceptance of confidence/retrieval-affinity proposals.
7. Add Challenger audit pass and Audit candidates.
8. Add disk-backed grid adapter interface metadata.
9. Add optional LanceDB adapter after the MVP is stable.

### Tranche migration candidates

Potential changes to existing plan:

- Tranche 1: add memory kind/status fields and pack role fields.
- Tranche 2: seed `confidence_events.jsonl`, `retrieval_affinity_events.jsonl`, `audit_candidates.jsonl`, and `audit_reviews.jsonl`.
- Tranche 9: add negative-space score components and caution scoring.
- Tranche 10: split pack into guidance/caution/background/conflict roles.
- Tranche 11: record pack Misses and richer feedback fields.
- Tranche 14: expand hygiene/decay/audit into Sweep and Challenger commands.
- Post-MVP: add disk-backed vector adapter implementation.

## CLI surface proposal

Near-term commands:

```text
shyftr pack --cell <path> --query <text> --task-id <id>
shyftr feedback --cell <path> --pack-id <id> --result success|failure|partial|unknown
shyftr hygiene --cell <path>
shyftr sweep --cell <path> --dry-run
shyftr challenge --cell <path> --dry-run
```

Later commands:

```text
shyftr audit review --cell <path> --audit-id <id> --accept|--reject
shyftr confidence apply --cell <path> --event-id <id>
shyftr grid rebuild --cell <path> --backend sqlite-vec|lancedb
shyftr grid status --cell <path>
```

## Open review questions

1. Should `confidence_events.jsonl` and `retrieval_affinity_events.jsonl` be separate ledgers, or should both be represented as generic audit/proposal events?
2. Should pack Misses be recorded directly in feedback, derived from pack plus applied IDs, or both?
3. Should `caution_items` count against the same token budget as guidance items, or have a reserved caution budget?
4. Should challenged memories appear in normal packs by default with warnings, or be excluded until resolved?
5. What is the first automatic action allowed for Sweep: reports only, retrieval-affinity proposals, or small confidence events?
6. Should LanceDB be named in early docs as a future adapter, or kept as an internal implementation option until needed?

## Recommended default answers

1. Separate ledgers are clearer for early review and tests.
2. Record explicit miss fields in feedback and also allow derived miss computation.
3. Reserve a small caution budget so warnings do not crowd out all guidance.
4. Include low/medium challenged memories with warnings; exclude high/critical quarantine candidates by default.
5. Start with reports and proposals only. Allow low-risk retrieval-affinity events after tests prove determinism.
6. Name LanceDB only as an optional future adapter, not as the core architecture.

## Final recommendation

These features are usable and strongly aligned with ShyftR if implemented with the right authority regulator.

Recommended priority:

1. Negative-space packs.
2. pack Miss logging.
3. Sweep maintenance pass.
4. Challenger audit loop.
5. Disk-backed grid adapters.

The strongest near-term product differentiator is negative-space memory: ShyftR should retrieve what the agent should do alongside what it should avoid.

The strongest long-term quality feature is the Challenger audit loop: high-confidence memory should be able to face counter-evidence without losing provenance.

The strongest scaling principle is rebuildability: the grid can become more sophisticated without ever replacing the cell ledgers as truth.
