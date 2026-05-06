# ShyftR Implementation Plan

> For Hermes: Use subagent-driven-development skill to implement this plan task-by-task.

Goal: Build ShyftR, a general-purpose, file-backed, auditable memory-cell system that converts conversations, tasks, artifacts, tool runs, and pulseback loops into durable intelligence. ShyftR provides attachable recursive memory cells for AI agents across users, projects, teams, domains, applications, and integrations.

Architecture: ShyftR uses isolated Cells with append-only JSONL ledgers as canonical truth, SQLite for metadata/querying, rebuildable vector indexes for semantic retrieval, manager-reviewed promotion gates, and recursive distillation jobs that propose playbook/policy updates. Vector stores are indexes only; durable operational and memory truth remains file-backed and replayable.

Tech Stack: Python 3.11+, Typer CLI, Pydantic models, JSONL ledgers, SQLite, sqlite-vec or LanceDB, BM25/sparse retrieval, sentence-transformers-compatible embedding adapters, pytest.

The three Rs: Recursive learning, Recall packs, and Retrieval infrastructure.

---

## Phase 0: Repository, product regulator, and rail foundation

### Task 0.0: Define the Cell product regulator

Objective: Ensure ShyftR is designed as a reusable memory-cell substrate for users, agents, projects, teams, domains, and applications.

Files:
- Modify: `README.md`
- Modify: `docs/plans/2026-04-24-shyftr-phased-plan.md`
- Create: `docs/concepts/cells.md`

Steps:
1. Define `Cell` as the primary abstraction.
2. Document that users, teams, agents, projects, domains, applications, and global rail can all be Cells.
3. Define `core` or `personal` as the default user memory Cell.
4. Explain that integration-specific scopes should be modeled as Cells through adapters or metadata.
5. Commit: `docs: define ShyftR Cell abstraction`.

Acceptance criteria:
- README describes ShyftR as a general-purpose memory-cell system.
- Plan contains explicit support for user, project, team, agent, domain, and application Cells.
- Cell abstraction is documented before integration-adapter tasks.

### Task 0.1: Establish repository scaffold

Objective: Create a minimal Python project and documentation skeleton.

Files:
- Create: `README.md`
- Create: `docs/plans/2026-04-24-shyftr-phased-plan.md`
- Create: `pyproject.toml`
- Create: `src/shyftr/__init__.py`
- Create: `tests/test_import.py`

Steps:
1. Create project directories.
2. Add project metadata in `pyproject.toml`.
3. Add a smoke import test.
4. Run `python -m pytest`.
5. Commit: `chore: scaffold shyftr repository`.

Acceptance criteria:
- Repository imports `shyftr`.
- Tests run locally.
- README contains architecture rail.

### Task 0.2: Capture memory regulator rail

Objective: Encode what may and may not become durable memory.

Files:
- Create: `docs/memory-regulator-rail.md`
- Create: `src/shyftr/policy.py`
- Test: `tests/test_memory_regulator_policy.py`

Steps:
1. Write rail doc with allowed and rejected memory examples.
2. Implement a simple operational-pollution detector with explicit patterns.
3. Test rejection of queue state, worktree state, branch names, completion logs, and transient test-pass claims.
4. Test acceptance of durable lessons and heuristics.
5. Commit: `feat: add memory regulator rail`.

Acceptance criteria:
- Operational-state examples are rejected.
- Durable lesson examples are accepted.

---

## Phase 1: Canonical ledger and schema

Canonical lifecycle for implementation:

```text
Spark -> Charge -> Coil -> Rail
```

- Pulses are raw evidence.
- Sparks are extracted candidate memory pieces.
- Charges are reviewed durable memories.
- Coils are recursive distillations from related Charges.
- Rail proposals are shared promoted rules.


### Task 1.1: Define core schemas

Objective: Add typed models for pulses, closeouts, Sparks, reviews, promotions, Charges, Coils, Rail proposals, and retrieval logs.

Files:
- Create: `src/shyftr/models.py`
- Test: `tests/test_models.py`

Steps:
1. Define Pydantic models or dataclasses for:
   - `MemoryEvent`
   - `CloseoutRecord`
   - `MemorySpark`
   - `ReviewRecord`
   - `PromotionRecord`
   - `Charge`
   - `Coil`
   - `RailProposal`
   - `RetrievalLog`
2. Include provenance fields: Pulse path, artifact hash, packet id, domain, timestamps.
3. Include memory lifecycle fields.
4. Add serialization tests.
5. Commit: `feat: define shyftr memory schemas`.

Acceptance criteria:
- Models serialize to stable JSON.
- Required provenance fields cannot be omitted.

### Task 1.2: Implement append-only JSONL ledger writer

Objective: Create durable append-only ledgers with hash-aware deduplication.

Files:
- Create: `src/shyftr/ledger.py`
- Test: `tests/test_ledger.py`

Steps:
1. Implement `append_jsonl(path, record)`.
2. Implement `read_jsonl(path)`.
3. Implement Spark dedupe by `pulse_artifact` plus `artifact_sha256`.
4. Ensure writes create parent directories.
5. Test append-only behavior.
6. Test duplicate rejection where required.
7. Commit: `feat: add append-only memory ledger`.

Acceptance criteria:
- Ledger records are newline-delimited JSON.
- Existing records are never rewritten.
- Deduplication prevents duplicate Spark ingestion from the same artifact hash.

### Task 1.3: Add memory Cell layout initializer

Objective: Create the standard Cell-local memory directory structure for users, agents, projects, teams, domains, applications, and global rail.

Files:
- Create: `src/shyftr/layout.py`
- Test: `tests/test_layout.py`

Steps:
1. Implement `init_cell_memory(root, cell_id, cell_type)`.
2. Create `ledger/`, `charges/`, `coils/`, `rail/`, `grid/`, `summaries/`, `reports/`, and `config/`.
3. Seed empty JSONL files where appropriate, including `ledger/pulses.jsonl`, `ledger/sparks.jsonl`, `charges/approved.jsonl`, `coils/proposed.jsonl`, and `rail/proposed.jsonl`.
4. Test idempotent initialization for `core`, `personal`, `project`, `agent`, and `domain` Cell types.
5. Commit: `feat: initialize Cell memory layout`.

Acceptance criteria:
- Running initialization twice is safe.
- Expected paths exist for generic Cell types.

---

## Phase 2: Spark extraction and review gate

### Task 2.1: Parse closeout memory checklists

Objective: Extract memory checklist fields from worker closeout artifacts.

Files:
- Create: `src/shyftr/closeout_parser.py`
- Test: `tests/test_closeout_parser.py`
- Fixture: `tests/fixtures/closeouts/valid_closeout.md`
- Fixture: `tests/fixtures/closeouts/missing_checklist.md`
- Fixture: `tests/fixtures/closeouts/fallback_closeout.md`

Steps:
1. Parse required fields:
   - `memory_spark_status`
   - `memory_spark_text`
   - `memory_regulator_check`
2. Recover metadata from closeout headers where possible.
3. Classify missing checklist as `skipped_missing_checklist`.
4. Classify explicit no-lesson as `skipped_no_lesson`.
5. Classify fallback synthesized closeouts as `review-required`.
6. Commit: `feat: parse closeout memory checklists`.

Acceptance criteria:
- Parser is whitespace-tolerant.
- Missing checklist does not become a fake “no lesson.”

### Task 2.2: Implement Spark extraction

Objective: Convert parsed Pulses/closeouts into Spark ledger rows. A Spark is a bounded, typed, provenance-linked candidate memory piece awaiting review before trust.

Files:
- Create: `src/shyftr/extract.py`
- Test: `tests/test_extract.py`

Steps:
1. Hash the Pulse artifact.
2. Run regulator-policy checks.
3. Emit Spark rows with status, reason, pulse excerpt, kind, tags, and confidence.
4. Reject operational-state pollution.
5. Preserve Pulse artifact and hash.
6. Commit: `feat: extract memory sparks from pulses`.

Acceptance criteria:
- Spark extraction is deterministic.
- Operational pollution is rejected before promotion.

### Task 2.3: Implement Spark review commands

Objective: Support approve/reject/split/merge review records without mutating Spark rows.

Files:
- Create: `src/shyftr/review.py`
- Test: `tests/test_review.py`

Steps:
1. Implement `approve_spark(spark_id, notes, reviewer)`.
2. Implement `reject_spark(spark_id, reason, notes, reviewer)`.
3. Append review rows to `reviews.jsonl`.
4. Implement Spark history lookup.
5. Test append-only review behavior, including split/merge review rows.
6. Commit: `feat: add spark review gate`.

Acceptance criteria:
- Reviews are append-only.
- Every approval/rejection requires notes.

---

## Phase 3: Promotion into durable Charges

### Task 3.1: Promote approved Sparks

Objective: Convert reviewed Sparks into durable approved Charges.

Files:
- Create: `src/shyftr/promote.py`
- Test: `tests/test_promote.py`

Steps:
1. Require latest Spark review to be approved.
2. Reject direct promotion from `new`.
3. Convert Spark text into a durable `Charge`.
4. Append to `charges/approved.jsonl`.
5. Append promotion record to `ledger/promotions.jsonl`.
6. Commit: `feat: promote reviewed sparks to charges`.

Acceptance criteria:
- Unapproved Sparks cannot be promoted.
- Promotion preserves Pulse and Spark provenance.

### Task 3.2: Add memory lifecycle transitions

Objective: Support deprecated, superseded, Isolationd, and audit-required statuses.

Files:
- Create: `src/shyftr/lifecycle.py`
- Test: `tests/test_lifecycle.py`

Steps:
1. Implement lifecycle transition records as append-only events.
2. Support supersession links.
3. Support Isolation with reason.
4. Compute latest effective state from event history.
5. Commit: `feat: add memory lifecycle state machine`.

Acceptance criteria:
- Effective memory state is derived from history.
- Original memory records are not rewritten.

---

## Phase 4: Retrieval foundation

### Task 4.1: Add sparse retrieval

Objective: Implement basic keyword/BM25-style retrieval over approved Charges.

Files:
- Create: `src/shyftr/retrieval/sparse.py`
- Test: `tests/test_sparse_retrieval.py`

Steps:
1. Tokenize approved memory statements and tags.
2. Implement simple BM25 or use a small dependency.
3. Return scored matches with memory ids.
4. Exclude deprecated/Isolationd memories by default.
5. Commit: `feat: add sparse memory retrieval`.

Acceptance criteria:
- Keyword queries find relevant approved Charges.
- Deprecated memories are excluded unless explicitly requested.

### Task 4.2: Add embedding adapter interface

Objective: Define a provider-neutral embedding interface.

Files:
- Create: `src/shyftr/retrieval/embeddings.py`
- Test: `tests/test_embedding_adapter.py`

Steps:
1. Define `EmbeddingProvider` protocol.
2. Implement a deterministic test embedding provider.
3. Add placeholder local sentence-transformers provider.
4. Avoid hard dependency on any paid API.
5. Commit: `feat: add embedding provider interface`.

Acceptance criteria:
- Tests run without network access.
- Real embedding providers can be plugged in later.

### Task 4.3: Add vector index abstraction

Objective: Store and query embeddings through a rebuildable index abstraction.

Files:
- Create: `src/shyftr/retrieval/vector.py`
- Test: `tests/test_vector_index.py`

Steps:
1. Define `VectorIndex` protocol.
2. Implement a simple in-memory cosine index for tests.
3. Add planned adapters for sqlite-vec or LanceDB.
4. Support full rebuild from `charges/approved.jsonl`.
5. Commit: `feat: add rebuildable vector index abstraction`.

Acceptance criteria:
- Vector index can be rebuilt from file-backed Charge ledgers.
- Canonical truth stays in the Charge ledger, not the vector index.

### Task 4.4: Implement hybrid retrieval scoring

Objective: Combine vector similarity, sparse score, tags, failure mode, confidence, reuse success, decay, and deprecation penalties.

Files:
- Create: `src/shyftr/retrieval/hybrid.py`
- Test: `tests/test_hybrid_retrieval.py`

Steps:
1. Implement weighted scoring formula.
2. Make weights configurable.
3. Return chargeable score components.
4. Add tests for deprecation penalty and confidence boost.
5. Commit: `feat: add hybrid memory retrieval scoring`.

Acceptance criteria:
- Retrieval results explain their score.
- Deprecated memories are penalized or excluded.

---

## Phase 5: Memory context bundles

### Task 5.1: Build packet classification input schema

Objective: Define the packet summary required for memory retrieval.

Files:
- Create: `src/shyftr/packet.py`
- Test: `tests/test_packet.py`

Steps:
1. Define packet fields: domain, packet kind, task summary, failure mode, tags, lane, worker role.
2. Support reading packet summary from JSON.
3. Validate required fields.
4. Commit: `feat: define packet memory input schema`.

Acceptance criteria:
- Packet summaries are validated before retrieval.

### Task 5.2: Generate bounded memory bundles

Objective: Create structured memory bundles for domain managers and workers.

Files:
- Create: `src/shyftr/bundle.py`
- Test: `tests/test_bundle.py`

Steps:
1. Retrieve approved Charges.
2. Retrieve failure signatures.
3. Retrieve relevant playbook sections.
4. Include similar prior packet summaries only as summaries.
5. Emit a bounded structured bundle.
6. Commit: `feat: generate bounded memory context bundles`.

Acceptance criteria:
- Bundles do not include raw operational state.
- Bundles distinguish approved Charges from background summaries.

### Task 5.3: Log retrieval usage

Objective: Track what memories were retrieved and whether they were later useful.

Files:
- Create: `src/shyftr/usage.py`
- Test: `tests/test_usage.py`

Steps:
1. Append retrieval logs to `retrieval_logs.jsonl`.
2. Record packet id, query, retrieved memory ids, and score charges.
3. Add later signal update events.
4. Compute usage counts and success/failure counts from logs.
5. Commit: `feat: log memory retrieval usage and signal`.

Acceptance criteria:
- Memory effectiveness can be evaluated from append-only logs.

---

## Phase 6: CLI

### Task 6.1: Add Typer CLI skeleton

Objective: Expose ShyftR commands through a local CLI.

Files:
- Create: `src/shyftr/cli.py`
- Modify: `pyproject.toml`
- Test: `tests/test_cli.py`

Steps:
1. Add `shyftr` console script.
2. Add commands:
   - `init-domain`
   - `ingest`
   - `sparks`
   - `show`
   - `approve`
   - `reject`
   - `promote`
   - `search`
   - `bundle`
   - `hygiene`
3. Add CLI smoke tests.
4. Commit: `feat: add shyftr cli skeleton`.

Acceptance criteria:
- `shyftr --help` works.
- Each command has help text.

### Task 6.2: Wire ingest/review/promote CLI commands

Objective: Make the core memory write flow usable from the command line.

Files:
- Modify: `src/shyftr/cli.py`
- Test: `tests/test_cli_ingest_review_promote.py`

Steps:
1. Implement `shyftr ingest --cell domain-development --Pulse path`.
2. Implement `shyftr sparks --cell domain-development`.
3. Implement `shyftr approve` and `shyftr reject` for Sparks.
4. Implement `shyftr promote` from approved Spark to Charge.
5. Test a full closeout-to-memory flow.
6. Commit: `feat: wire shyftr write-flow cli`.

Acceptance criteria:
- A Pulse can produce Sparks, and an approved Spark can become a durable Charge through CLI review gates.

### Task 6.3: Wire search and bundle CLI commands

Objective: Make retrieval usable from the command line.

Files:
- Modify: `src/shyftr/cli.py`
- Test: `tests/test_cli_retrieval.py`

Steps:
1. Implement `shyftr search`.
2. Implement `shyftr bundle --packet packet.json`.
3. Include score charges in verbose mode.
4. Commit: `feat: wire shyftr retrieval cli`.

Acceptance criteria:
- Search returns relevant approved Charges.
- Bundle command emits bounded context.

---

## Phase 7: Hygiene, audit, and compliance reporting

### Task 7.1: Add hygiene report

Objective: Report Cell memory health truthfully.

Files:
- Create: `src/shyftr/reports/hygiene.py`
- Test: `tests/test_hygiene_report.py`

Steps:
1. Count canonical live-Pulse Sparks.
2. Count missing-Pulse legacy rows.
3. Count noncanonical-Pulse rows.
4. Report latest status counts.
5. Sample problematic rows.
6. Commit: `feat: add memory hygiene report`.

Acceptance criteria:
- Hygiene distinguishes live canonical pulses from historical debt.

### Task 7.2: Add compliance hotspot report

Objective: Identify where closeout checklist failures originate.

Files:
- Create: `src/shyftr/reports/compliance.py`
- Test: `tests/test_compliance_report.py`

Steps:
1. Normalize report kinds.
2. Recover worker role and queue item metadata from artifacts where possible.
3. Exclude escalation artifacts from closeout checklist hotspot counts.
4. Report top worker roles, report kinds, and queue items with missing checklists.
5. Commit: `feat: add closeout memory compliance report`.

Acceptance criteria:
- Escalations do not pollute closeout checklist hotspot analysis.

### Task 7.3: Add append-only audit reclassification

Objective: Reclassify stale or misclassified rows without rewriting history.

Files:
- Create: `src/shyftr/audit.py`
- Test: `tests/test_audit.py`

Steps:
1. Load existing Spark history.
2. Re-run extraction under current policy.
3. Append audit row with Pulse ledger line and result.
4. Add bulk audit with limit and status filters.
5. Commit: `feat: add append-only audit reclassification`.

Acceptance criteria:
- Audit writes corrective rows only.
- Historical rows are not mutated.

---

## Phase 8: Recursive distillation

### Task 8.1: Cluster related Charges into Coil proposals

Objective: Group approved Charges into Coil proposals for review.

Files:
- Create: `src/shyftr/distill/cluster.py`
- Test: `tests/test_cluster.py`

Steps:
1. Cluster by embedding similarity and tags.
2. Produce cluster summaries with Pulse memory ids.
3. Identify duplicate Sparks.
4. Commit: `feat: cluster approved Charges for distillation`.

Acceptance criteria:
- Similar memories are grouped with provenance.

### Task 8.2: Detect conflicts and supersession proposals

Objective: Find memories that disagree or should supersede each other.

Files:
- Create: `src/shyftr/distill/conflicts.py`
- Test: `tests/test_conflicts.py`

Steps:
1. Compare memories within clusters.
2. Flag contradictory statements.
3. Flag weaker memories superseded by stronger memories.
4. Emit review proposals, not automatic mutations.
5. Commit: `feat: propose memory conflicts and supersessions`.

Acceptance criteria:
- Conflicts are review proposals only.

### Task 8.3: Propose playbook updates from Coils

Objective: Convert repeated validated lessons into domain playbook proposals.

Files:
- Create: `src/shyftr/distill/playbook.py`
- Test: `tests/test_playbook_proposals.py`

Steps:
1. Identify validated repeated lessons.
2. Generate proposed playbook sections.
3. Preserve Pulse memory ids.
4. Require manager approval before writing to `domain_playbook.md`.
5. Commit: `feat: propose domain playbook updates`.

Acceptance criteria:
- Playbook updates are generated as proposals with provenance.

### Task 8.4: Add cross-domain rail proposals

Objective: Propose global integration rail only from approved domain-level patterns.

Files:
- Create: `src/shyftr/distill/cross_domain.py`
- Test: `tests/test_cross_domain_distill.py`

Steps:
1. Compare high-confidence lessons across domains.
2. Identify generalized Rail proposals.
3. Require explicit promotion to global rail.
4. Commit: `feat: propose cross-domain memory rail`.

Acceptance criteria:
- Domain memory does not silently mutate global policy.

---

## Phase 9: Integration adapters

### Task 9.1: Add generic pulse adapters

Objective: Support non-integration memory Pulses such as direct notes, chat summaries, task closeouts, issue comments, and tool logs.

Files:
- Create: `src/shyftr/adapters/pulses.py`
- Test: `tests/test_pulse_adapters.py`

Steps:
1. Define a `MemoryPulseAdapter` protocol.
2. Implement adapters for markdown note, chat summary JSON, task closeout markdown, and raw text.
3. Normalize all Pulses into Spark extraction input.
4. Preserve provenance and pulse hashes.
5. Commit: `feat: add generic memory pulse adapters`.

Acceptance criteria:
- Non-domain user memory can be ingested without integration-specific concepts.
- All adapters preserve provenance.

### Task 9.2: Add domain/task closeout adapter

Objective: Attach ShyftR ingestion to generic domain/task closeout flows as one adapter among many.

Files:
- To be determined by target integration after runtime inspection.

Steps:
1. Identify domain/task closeout attachment point.
2. Call ShyftR ingestion after closeout artifact creation.
3. Ensure ingestion failures do not corrupt packet completion state.
4. Add tests.
5. Commit integration.

Acceptance criteria:
- Closeouts produce memory Spark ledger rows.

### Task 9.3: Integrate retrieval bundles with generic clients

Objective: Pulse bounded approved memory context into assistants, agents, project tools, and routing/execution decisions.

Files:
- To be determined by target integration after runtime inspection.

Steps:
1. Identify client task classification path.
2. Generate memory bundle for packet.
3. Provide only bounded approved/relevant context.
4. Log retrieval usage.
5. Add tests proving no raw operational state leaks.
6. Commit integration.

Acceptance criteria:
- Packet routing can consume approved domain memories.
- Retrieval logs record memory usage.

---

## Phase 10: Evaluation and hardening

### Task 10.1: Build memory effectiveness metrics

Objective: Measure whether retrieved memories help future packets.

Files:
- Create: `src/shyftr/metrics.py`
- Test: `tests/test_metrics.py`

Steps:
1. Compute retrieval usage count.
2. Compute successful reuse count.
3. Compute failed reuse count.
4. Compute memory confidence adjustments.
5. Commit: `feat: add memory effectiveness metrics`.

Acceptance criteria:
- Memory confidence can be updated from signal evidence.

### Task 10.2: Add decay scoring

Objective: Reduce influence of stale or harmful memories.

Files:
- Create: `src/shyftr/decay.py`
- Test: `tests/test_decay.py`

Steps:
1. Score age, failed reuse, supersession, and low confidence.
2. Penalize decayed memories in retrieval.
3. Produce decay report.
4. Commit: `feat: add memory decay scoring`.

Acceptance criteria:
- Stale/harmful memories are down-ranked or proposed for deprecation.

### Task 10.3: Add proof-of-work demonstration

Objective: Provide a reproducible demo showing closeout-to-memory-to-bundle flow.

Files:
- Create: `examples/closeout.md`
- Create: `examples/packet.json`
- Create: `docs/demo.md`
- Test: `tests/test_demo_flow.py`

Steps:
1. Add sample closeout with durable lesson.
2. Ingest Pulse and extract Spark.
3. Approve and promote it.
4. Search and generate memory bundle.
5. Document commands.
6. Commit: `docs: add shyftr proof-of-work demo`.

Acceptance criteria:
- New users can run the demo locally.

---

## Phase 11: Release and operating discipline

### Task 11.1: Add CI

Objective: Validate tests on GitHub for public proof-of-work.

Files:
- Create: `.github/workflows/ci.yml`

Steps:
1. Run tests on Python 3.11 and 3.12.
2. Cache dependencies.
3. Commit: `ci: add pytest workflow`.

Acceptance criteria:
- GitHub Actions runs tests on push and pull requests.

### Task 11.2: Add contribution and review policy

Objective: Preserve memory safety as the project evolves.

Files:
- Create: `CONTRIBUTING.md`
- Create: `docs/review-policy.md`

Steps:
1. Require tests for regulator policy changes.
2. Require migration notes for schema changes.
3. Require provenance-preserving behavior for memory writes.
4. Commit: `docs: add contribution and review policy`.

Acceptance criteria:
- Contributors understand memory safety requirements.

### Task 11.3: Tag first planning release

Objective: Mark the initial proof-of-work planning baseline.

Commands:
```bash
git tag v0.0.0-planning
git push origin v0.0.0-planning
```

Acceptance criteria:
- GitHub contains a tagged planning baseline.

---

## MVP cut line

The first usable MVP is complete at the end of Phase 6 if it supports:

1. generic Cell memory layout initialization
2. closeout checklist parsing
3. Spark extraction
4. append-only review gate
5. approved Spark-to-Charge promotion
6. sparse/vector-ready retrieval
7. bounded memory bundle generation for generic Cells
8. CLI use for ingest, approve, promote, search, and bundle

Phases 7-11 harden the system into a recursive, auditable, proof-of-work-ready memory-cell substrate.
