# ShyftR Active Learning Follow-up Plan

> For Hermes: implement this only after the main MVP tranche plan is complete and pushed. Use subagent-driven-development for implementation, and keep each tranche small, tested, and committed.

Status: follow-up implementation plan. This plan extends `docs/plans/2026-04-24-shyftr-implementation-tranches.md` after the MVP and public proof-of-work tranches.

Pulse material: `docs/pulses/2026-04-24-active-learning-cell-implementation-pulse.md`.

Goal: evolve ShyftR from a signal-aware file-backed memory Cell into an active recall-and-learning Cell that retrieves what to do, warns what not to do, learns from non-application, audits high-confidence memory, and can scale the rebuildable Grid without compromising Cell Ledger authority.

Architecture: canonical truth remains the append-only Cell Ledger under each Cell. The Regulator remains the review and policy layer for admission, promotion, retrieval, and export. Background maintenance jobs append evidence and proposals. Review-gated events alter durable authority. The Grid remains rebuildable acceleration. Loadouts/Packs become role-labeled application packages. Outcome/Signal records become the learning signal.

Canonical system vocabulary:

- ShyftR Cell: a bounded attachable memory unit.
- Regulator: the review and policy layer controlling admission, promotion, retrieval, and export.
- Cell Ledger: the append-only canonical truth inside a Cell.
- Charge: a reviewed durable memory item.
- Grid: the rebuildable retrieval and index layer.
- Pack: the bounded memory bundle supplied to an agent or runtime.
- Signal: the pulseback record that tells ShyftR whether retrieved memory helped or harmed.

Current implementation naming note:

This plan uses the public power vocabulary above, but implementation tranches must target the names that exist in the repo today. Current Python modules and primary classes are:

- `Source` / `Fragment` / `Trace` / `Alloy` / `DoctrineProposal` in `src/shyftr/models.py`.
- Power aliases already exist in `models.py`: `Feed = Source`, `Spark = Fragment`, `Charge = Trace`, `Coil = Alloy`, `RailProposal = DoctrineProposal`, `Pack = Loadout`, and `Signal = Outcome`.
- Loadout/Pack code lives in `src/shyftr/loadout.py`, with tests in `tests/test_loadout.py`.
- Outcome/Signal code lives in `src/shyftr/outcomes.py`, with tests in `tests/test_outcomes.py`.
- Runtime JSON API surfaces live under `src/shyftr/integrations/loadout_api.py` and `src/shyftr/integrations/outcome_api.py`.

When a tranche says Charge, Pack, Signal, Spark, Coil, or Rail, implement against the corresponding current class/module names unless that tranche explicitly performs a naming migration. Do not invent `pack.py`, `signal.py`, `Charge`, `Pack`, or `Signal`-only modules while the current codebase still uses `loadout.py`, `outcomes.py`, `Trace`, `Loadout`, and `Outcome` as primary implementation names.

Core rails remains:

```text
Cell ledgers are truth.
The Regulator controls admission, promotion, retrieval, and export.
The Grid is acceleration.
The Loadout/Pack is application.
Outcome/Signal is learning.
Trace/Charge confidence is evolution.
```

---

## Relationship to the main plan

This is a follow-up plan, not a replacement for the MVP plan.

Main plan:

- `docs/plans/2026-04-24-shyftr-implementation-tranches.md`
- MVP cut line ends after Tranche 11.
- Tranches 12-16 harden distillation, multi-Cell evolution, hygiene, CLI, demo, and CI.

This follow-up should begin only after:

1. The full local lifecycle works from CLI.
2. Loadout/Pack and Outcome/Signal records exist.
3. Hybrid retrieval and confidence evolution exist.
4. CI/demo proof-of-work exists.
5. The repo is clean and synced.

Recommended sequencing:

```text
Main plan Tranches 0-16
  -> Active Learning Follow-up Tranches AL-0 through AL-8
```

---

## Follow-up feature set

This plan adds five capability groups:

1. Negative-space retrieval: retrieve relevant failure signatures and anti-patterns as Caution items.
2. Loadout/Pack Miss learning: record when loaded Traces/Charges were not applied and learn from over-retrieval.
3. Sweep maintenance pass: asynchronously propose confidence and retrieval-affinity changes.
4. Challenger audit loop: search for counter-evidence against high-impact Traces/Charges and create Audit Fragments/Sparks.
5. Disk-backed Grid scale path: define and later implement optional larger vector index adapters.

Authority regulator:

- Background jobs may append proposals, reports, and derived events.
- Background jobs must not silently delete, rewrite, isolate, or deprecate durable memory in the first implementation.
- Review acceptance creates durable authority changes.

---

## Tranche AL-0: Active-learning schema expansion

Objective: add the schema fields needed for role-labeled Loadouts/Packs, explicit Outcome/Signal misses, audit findings, and future Grid metadata, using the current implementation modules and class names.

Files:

- Modify: `src/shyftr/models.py`
- Modify: `src/shyftr/loadout.py`
- Modify: `src/shyftr/outcomes.py`
- Modify: `tests/test_models.py`
- Modify: `tests/test_loadout.py`
- Modify: `tests/test_outcomes.py`

Tasks:

1. Add or lock Trace/Charge kind values, preserving current `Trace` serialization:
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
   - `rail_candidate`
   - `supersession`
   - `scope_exception`
   - `audit_finding`
2. Add Trace/Charge status values, preserving current `Trace.status` compatibility:
   - `approved`
   - `challenged`
   - `isolation_candidate`
   - `isolated`
   - `superseded`
   - `deprecated`
3. Add `loadout_role` (or a backward-compatible `pack_role` alias if needed) to `LoadoutItem` records:
   - `guidance`
   - `caution`
   - `background`
   - `conflict`
4. Add `retrieval_id` to retrieval logs and link retrieval logs to `loadout_id`.
5. Expand Outcome/Signal records with current `Outcome` ledger compatibility:
   - `ignored_charge_ids`
   - `ignored_caution_ids`
   - `contradicted_charge_ids`
   - `over_retrieved_charge_ids`
   - `pack_misses`
6. Add deterministic JSON serialization tests for all new fields.
7. Preserve backward compatibility for existing fixture records where possible.
8. Commit: `feat: expand active learning schemas`.

Acceptance criteria:

- Existing tests still pass.
- New Trace/Charge kinds and statuses serialize deterministically.
- Loadout/Pack items can be role-labeled without changing canonical provenance.
- Outcome/Signal records can explicitly represent non-application and contradiction.

---

## Tranche AL-1: Active-learning ledgers and layout

Objective: seed append-only proposal and audit ledgers required by Sweep and Challenger passes.

Files:

- Modify: `src/shyftr/layout.py`
- Modify: `src/shyftr/ledger.py`
- Modify: `src/shyftr/store/sqlite.py`
- Modify: `tests/test_layout.py`
- Modify: `tests/test_ledger.py`
- Modify: `tests/test_sqlite_store.py`

Tasks:

1. Seed additional ledgers in every Cell:
   - `ledger/confidence_events.jsonl`
   - `ledger/retrieval_affinity_events.jsonl`
   - `ledger/audit_sparks.jsonl`
   - `ledger/audit_reviews.jsonl`
2. Add reader helpers for each new ledger.
3. Add idempotent initialization tests for new ledgers.
4. Update SQLite rebuild/materialization to include these ledgers as audit/proposal views.
5. Ensure all new ledgers are append-only and replayable.
6. Commit: `feat: add active learning ledgers`.

Acceptance criteria:

- Re-running Cell initialization creates no duplicate or destructive changes.
- SQLite remains rebuildable from JSONL.
- Empty proposal ledgers do not break existing CLI flows.

---

## Tranche AL-2: Negative-space retrieval scoring

Objective: make retrieval aware of failure signatures, anti-patterns, challenged Traces/Charges, and risk signals.

Files:

- Modify: `src/shyftr/retrieval/hybrid.py`
- Modify: `src/shyftr/loadout.py`
- Modify: `tests/test_hybrid_retrieval.py`
- Modify: `tests/test_loadout.py`

Tasks:

1. Add positive and negative scoring components to hybrid retrieval:
   - positive similarity
   - negative similarity
   - confidence weight
   - proven signal weight
   - symbolic match weight
   - risk penalty
   - final score
2. Define a configurable Caution Coefficient for negative signals.
3. Treat these Trace/Charge kinds as negative-space candidates:
   - `failure_signature`
   - `anti_pattern`
   - `supersession`
4. Penalize or label these statuses:
   - `challenged`
   - `isolation_candidate`
5. Exclude these statuses from normal guidance by default:
   - `isolated`
   - `superseded`
   - `deprecated`
6. Return explainable score traces including `selection_reason`:
   - `positive_guidance`
   - `caution`
   - `suppressed`
   - `filtered`
   - `conflict`
7. Test that a valid task can retrieve both a positive guidance Trace/Charge and a related Caution Trace/Charge.
8. Test that a high-risk anti-pattern can suppress or demote weak positive guidance.
9. Commit: `feat: add negative-space retrieval scoring`.

Acceptance criteria:

- A `failure_signature` Trace/Charge can appear as a Caution item.
- An `anti_pattern` Trace/Charge can reduce the score of related positive guidance.
- Negative-space score components are visible in `score_trace` / `score_traces`.
- Related failures do not block positive work by default.

---

## Tranche AL-3: Role-labeled Loadout/Pack assembly

Objective: split Loadouts/Packs into guidance, caution, background, and conflict roles while keeping token and item limits bounded.

Files:

- Modify: `src/shyftr/loadout.py`
- Modify: `tests/test_loadout.py`
- Modify: `docs/concepts/storage-retrieval-learning.md`

Tasks:

1. Update Loadout/Pack assembly to produce role-labeled items.
2. Add helper accessors or serialization fields for:
   - `guidance_items`
   - `caution_items`
   - `background_items`
   - `conflict_items`
3. Reserve a small caution budget so warnings do not crowd out all guidance.
4. Preserve a total token cap across all roles.
5. Append retrieval logs with:
   - `candidate_ids`
   - `selected_ids`
   - `caution_ids`
   - `suppressed_ids`
   - expanded `score_traces`
6. Ensure operational-state pollution checks apply to all Loadout/Pack roles.
7. Test that Caution items are clearly labeled and provenance-linked.
8. Test that Loadouts/Packs remain deterministic under item/token caps.
9. Commit: `feat: assemble role-labeled Loadouts`.

Acceptance criteria:

- Loadouts/Packs separate action guidance from warnings.
- Caution items carry trust tier, kind, confidence, score, and provenance.
- Operational state does not leak into any Loadout/Pack role.
- Retrieval logs are rich enough for later Sweep analysis.

---

## Tranche AL-4: Loadout/Pack Miss signal learning

Objective: record and report when retrieved Traces/Charges were not applied, without incorrectly treating every miss as false memory.

Files:

- Modify: `src/shyftr/outcomes.py`
- Modify: `src/shyftr/confidence.py`
- Modify: `src/shyftr/reports/hygiene.py`
- Modify: `tests/test_outcomes.py`
- Modify: `tests/test_confidence.py`
- Modify: `tests/test_hygiene.py`

Tasks:

1. Compare each Signal against its linked Pack/retrieval log.
2. Derive `pack_miss_ids` from selected guidance items not applied, useful, harmful, or explicitly contradicted.
3. Allow explicit `pack_misses` with miss types:
   - `not_relevant`
   - `not_actionable`
   - `contradicted`
   - `duplicative`
   - `unknown`
4. Record ignored Caution items separately from ignored guidance items.
5. Ensure a single miss does not lower global Trace/Charge confidence by itself.
6. Add hygiene summaries for:
   - most missed Traces/Charges
   - most over-retrieved Traces/Charges
   - Traces/Charges with high miss rate but high confidence
   - Traces/Charges with mixed useful/harmful signal
7. Test miss derivation and explicit miss preservation.
8. Commit: `feat: record Loadout/Pack Miss signal`.

Acceptance criteria:

- Outcome/Signal recording captures loaded-but-unused Traces/Charges.
- Loadout/Pack Misses are visible in reports.
- Confidence changes distinguish harmful application from non-application.
- Misses are available for retrieval-affinity proposals in later tranches.

---

## Tranche AL-5: Sweep dry-run reports

Objective: add a safe maintenance pass that analyzes retrieval and Signal history without mutating durable authority.

Files:

- Create: `src/shyftr/sweep.py`
- Modify: `src/shyftr/reports/hygiene.py`
- Modify: `src/shyftr/cli.py`
- Create: `tests/test_sweep.py`
- Modify: `tests/test_cli.py`

Tasks:

1. Implement `shyftr sweep --cell <path> --dry-run`.
2. Read:
   - retrieval logs
   - Signal
   - audit sparks
   - confidence events
   - retrieval-affinity events
   - approved/deprecated/isolated Trace/Charge ledgers
3. Compute per-Trace/Charge metrics:
   - retrieval count
   - application count
   - useful count
   - harmful count
   - miss count
   - application rate
   - useful rate
   - harmful rate
   - miss rate
4. Compute per-query-tag or per-query-cluster summaries where available.
5. Emit a deterministic report containing proposed actions:
   - `retrieval_affinity_decrease`
   - `confidence_decrease`
   - `confidence_increase`
   - `manual_review`
   - `split_charge`
   - `supersession_candidate`
6. Ensure dry-run writes no ledger records unless an explicit output path is requested.
7. Test deterministic report output from fixtures.
8. Commit: `feat: add Sweep dry-run analysis`.

Acceptance criteria:

- Sweep runs without network access.
- Sweep never rewrites history.
- Repeated fixture runs produce stable reports.
- Repeated misses produce affinity proposals, not deprecation.
- Harmful applied Traces/Charges produce confidence-decrease proposals.

---

## Tranche AL-6: Sweep proposal events

Objective: allow the Sweep to append low-authority proposal events to active-learning ledgers.

Files:

- Modify: `src/shyftr/sweep.py`
- Modify: `src/shyftr/confidence.py`
- Modify: `src/shyftr/cli.py`
- Modify: `tests/test_sweep.py`
- Modify: `tests/test_confidence.py`
- Modify: `tests/test_cli.py`

Tasks:

1. Implement `shyftr sweep --cell <path> --propose`.
2. Append proposal records to:
   - `ledger/confidence_events.jsonl`
   - `ledger/retrieval_affinity_events.jsonl`
3. Deduplicate open proposals using stable proposal keys.
4. Keep proposal records separate from accepted confidence changes.
5. Add optional `--apply-low-risk` for retrieval-affinity events only.
6. Do not allow Sweep to isolate, deprecate, or delete Traces/Charges.
7. Add report output that lists written proposal IDs.
8. Commit: `feat: let Sweep append active learning proposals`.

Acceptance criteria:

- Proposal writes are append-only.
- Re-running Sweep does not duplicate identical open proposals.
- `--apply-low-risk` cannot alter Charge status or destructive authority.
- Confidence-event proposals remain reviewable.

---

## Tranche AL-7: Challenger audit loop

Objective: add an audit pass that challenges high-impact Traces/Charges by searching for counter-evidence and creating Audit Fragments/Sparks.

Files:

- Create: `src/shyftr/audit/challenger.py`
- Modify: `src/shyftr/audit.py`
- Modify: `src/shyftr/cli.py`
- Create: `tests/test_challenger.py`
- Modify: `tests/test_audit.py`
- Modify: `tests/test_cli.py`

Tasks:

1. Implement `shyftr challenge --cell <path> --dry-run`.
2. Implement optional target selection:
   - `--charge-id <id>`
   - `--top-impact N`
3. Rank target Traces/Charges by:
   - confidence
   - retrieval frequency
   - application frequency
   - Rail promotion readiness
   - old age with recent continued use
   - recent harmful signal
   - unresolved miss/contradiction signals
4. Search counter-evidence in:
   - Pulses
   - Sparks
   - Signal
   - audit records
   - newer Traces/Charges
   - deprecated/superseded Traces/Charges
5. Classify findings as:
   - `direct_contradiction`
   - `supersession`
   - `scope_exception`
   - `environment_specific`
   - `temporal_update`
   - `ambiguous_counterevidence`
   - `policy_conflict`
   - `implementation_drift`
6. Emit Audit Fragments/Sparks to `ledger/audit_sparks.jsonl` when run with `--propose`.
7. Keep Isolation and deprecation review-gated.
8. Test contradiction, supersession, and scope-exception fixtures.
9. Commit: `feat: add Challenger audit loop`.

Acceptance criteria:

- Challenger can identify high-impact Traces/Charges for audit.
- Challenger emits Audit Fragments/Sparks with counter-evidence IDs.
- Challenger distinguishes contradiction from scope exception and supersession.
- No Charge is deleted or silently demoted by Challenger.

---

## Tranche AL-8: Audit review and Isolation workflow

Objective: add explicit review commands for Audit Fragments/Sparks and wire challenged/Isolation status into retrieval behavior.

Files:

- Modify: `src/shyftr/audit.py`
- Modify: `src/shyftr/retrieval/hybrid.py`
- Modify: `src/shyftr/loadout.py`
- Modify: `src/shyftr/cli.py`
- Modify: `tests/test_audit.py`
- Modify: `tests/test_hybrid_retrieval.py`
- Modify: `tests/test_loadout.py`
- Modify: `tests/test_cli.py`

Tasks:

1. Implement audit review records in `ledger/audit_reviews.jsonl`.
2. Add CLI commands:
   - `shyftr audit list --cell <path>`
   - `shyftr audit review --cell <path> --audit-id <id> --accept|--reject`
   - `shyftr audit resolve --cell <path> --audit-id <id>`
3. On accepted audit findings, allow reviewed actions:
   - mark Charge challenged
   - propose Isolation
   - propose supersession
   - propose confidence decrease
   - request rewrite or split
4. Keep final Isolation/deprecation status changes explicit and review-gated.
5. Update retrieval behavior:
   - low/medium challenged Traces/Charges may appear with warning labels.
   - high/critical isolation candidates are excluded from normal guidance by default.
   - audit/debug mode can include all statuses with labels.
6. Test that challenged Traces/Charges are labeled or penalized.
7. Test that isolation candidates do not appear as ordinary guidance.
8. Commit: `feat: add audit review workflow`.

Acceptance criteria:

- Audit findings are reviewable and replayable.
- Retrieval behavior respects challenged/Isolation status.
- Review actions append events instead of rewriting past records.
- High-risk memory can be contained without losing provenance.

---

## Tranche AL-9: Disk-backed Grid adapter metadata

Objective: prepare the Grid abstraction for optional disk-backed vector indexes without adding heavy dependencies by default.

Files:

- Modify: `src/shyftr/retrieval/vector.py`
- Modify: `src/shyftr/retrieval/embeddings.py`
- Modify: `src/shyftr/store/sqlite.py`
- Modify: `src/shyftr/cli.py`
- Modify: `tests/test_vector_retrieval.py`
- Create: `tests/test_grid_metadata.py`

Tasks:

1. Define or refine a `VectorIndex` protocol that supports:
   - rebuild
   - query
   - clear
   - status
   - metadata export
2. Record index metadata:
   - `index_id`
   - `cell_id`
   - `backend`
   - `embedding_model`
   - `embedding_dimension`
   - `embedding_version`
   - Pulse ledger offsets or hashes
   - charge count
   - created timestamp
3. Add CLI commands:
   - `shyftr grid status --cell <path>`
   - `shyftr grid rebuild --cell <path>`
4. Detect stale indexes when embedding metadata or ledger offsets change.
5. Keep tests dependency-free with deterministic embeddings and local indexes.
6. Commit: `feat: add Grid adapter metadata`.

Acceptance criteria:

- Vector index metadata is inspectable.
- Rebuild can wipe and recreate the local vector index from ledgers.
- The Grid remains an acceleration layer, not canonical truth.
- No LanceDB/Qdrant dependency is required for default tests.

---

## Tranche AL-10: Optional LanceDB adapter spike

Objective: add an optional disk-backed vector adapter only after the local Grid interface is stable.

Files:

- Create: `src/shyftr/retrieval/lancedb_adapter.py`
- Modify: `pyproject.toml`
- Modify: `src/shyftr/retrieval/vector.py`
- Modify: `src/shyftr/cli.py`
- Create: `tests/test_lancedb_adapter.py`

Tasks:

1. Add LanceDB as an optional extra, not a default dependency.
2. Implement a LanceDB-backed `VectorIndex` adapter behind the same protocol.
3. Store LanceDB files under the Cell `grid/` directory.
4. Record backend metadata as `lancedb`.
5. Add skip-if-missing tests for the optional extra.
6. Add benchmark or smoke command for local comparison against the default vector adapter.
7. Avoid absolute performance claims in docs and CLI output.
8. Commit: `feat: add optional LanceDB Grid adapter`.

Acceptance criteria:

- Default test suite passes without LanceDB installed.
- Optional LanceDB tests pass when extras are installed.
- The adapter is rebuildable from Cell ledgers.
- LanceDB is clearly documented as optional acceleration, not durable truth.

---

## Final verification before completing the follow-up plan

Run from `/Users/stefan/shyftr-lab`:

```bash
python3 -m pytest -q
# Run the project stale-terminology scan from the ShyftR rail skill against README.md and docs/.
git status --short
git push origin main
git fetch origin main
git rev-parse HEAD
git rev-parse origin/main
```

Expected:

- tests pass
- stale-term scan has no public-doc matches
- only intended files are committed
- local `HEAD` matches `origin/main` after push

---

## Follow-up cut line

The first active-learning cut is complete after AL-6:

1. active-learning schemas
2. active-learning ledgers
3. negative-space retrieval
4. role-labeled Loadouts/Packs
5. Loadout/Pack Miss Outcome/Signal
6. Sweep dry-run and proposal events

AL-7 and AL-8 add self-audit and Isolation workflows.

AL-9 and AL-10 prepare and optionally implement larger disk-backed Grid adapters.
