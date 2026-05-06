# Regulated Autonomous Memory Evolution Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task. Stop before Phase 8 productization unless the operator explicitly approves continuing into productization work.

**Goal:** Add a public-safe, review-gated memory evolution layer that can propose memory splitting, consolidation, supersession, deprecation, replacement, and logical forgetting from new evidence without silently rewriting canonical ledger truth.

**Architecture:** Build a deterministic proposal engine over existing ShyftR ledgers: evidence and feedback remain append-only; projections derive current state; automated checks create review-gated evolution proposals; accepted proposals append lifecycle/review events through existing regulator paths. Public `main` receives transparent heuristics, schemas, tests, CLI/API/UI/TUI surfaces, and synthetic fixtures; private-core scoring, proprietary ranking, real-data calibration, and unattended destructive authority remain out of scope.

**Tech Stack:** Python 3.11+, JSONL ledgers, SQLite/FTS projections where already used, existing `shyftr` CLI/FastAPI/React console surfaces, pytest, deterministic synthetic fixtures.

**Research basis:** Event sourcing, hierarchical agent memory systems such as MemGPT/Letta, semantic chunking and recursive text splitting patterns, duplicate/consolidation pipelines from retrieval-augmented systems, knowledge-graph provenance/supersession, and human-in-the-loop memory governance. These inform the public-safe design but do not require private algorithms or hosted services.

---

## Non-negotiable invariants

1. Cell ledgers remain canonical truth; no feature directly rewrites historical JSONL rows.
2. Physical deletion is not the normal behavior. `forget`, `redact`, `deprecate`, `replace`, and `supersede` append lifecycle events that exclude memory from retrieval/profile/pack projections as appropriate.
3. Autonomous means “detect and propose by default,” not “silently apply.”
4. Any operation that changes durable memory state must pass through the regulator/review path.
5. All public examples and tests use synthetic or operator-approved data only.
6. Every proposed split, merge, supersession, replacement, or forgetting action includes evidence IDs, rationale, confidence, affected memory IDs, expected projection delta, and rollback/review notes.
7. Evolution proposals must be simulated before acceptance whenever retrieval behavior changes.
8. Private scoring weights, proprietary consolidation heuristics, production traces, and commercial/runtime strategy stay outside public `main`.

## Human input requirement

None for safe implementation tranches. The implementation should create review queues and sample decisions with synthetic fixtures only. Real memory decisions, live private ledgers, hosted deployment, public release language, and any auto-apply mode require separate operator approval and are outside this plan.

---

## Public/private split

| Area | Public-safe implementation | Private-core reserved | Hard gate |
| --- | --- | --- | --- |
| Arrival splitting | deterministic size/topic heuristics and split proposal schema | proprietary semantic boundary scoring over real private data | proposals only until review |
| Duplicate consolidation | transparent lexical/embedding-adapter hooks with deterministic synthetic tests | tuned thresholds, domain-specific entity disambiguation, private embeddings | never merge without review |
| Supersession | graph/lifecycle proposal events with evidence refs | private contradiction ranking and confidence calibration | simulation plus review |
| Forget/deprecate/redact | logical lifecycle proposals and projection exclusion tests | private retention/legal policy automation | operator-approved policy only |
| Confidence evolution | public counters and beta-style metadata | advanced calibration/model-fit scoring | advisory, not authority |
| Evolution scheduler | dry-run planner and proposal emitter | private autonomous cadence over real cells | disabled by default |
| UI/TUI surfaces | operator-visible inbox and simulation controls | private operator workflows | no hidden mutations |

---

## Existing foundations to reuse

- `src/shyftr/review.py`: candidate approve/reject/split/merge review events.
- `src/shyftr/mutations.py`: forget, replace, deprecate, challenge, isolate, restore, conflict lifecycle events.
- `src/shyftr/confidence.py` and `src/shyftr/frontier.py`: confidence adjustments and frontier belief metadata.
- `src/shyftr/graph.py`: reviewed memory graph edges such as `supersedes`, `contradicted_by`, `depends_on`.
- `src/shyftr/sweep.py`, `src/shyftr/reports/hygiene.py`, and proposal modules: advisory report/proposal patterns.
- `src/shyftr/console_api.py`, `src/shyftr/server.py`, and `apps/console`: local operator surfaces.
- Existing tests around review, mutation, hygiene, sweep, graph, simulation, and regulator proposals.

---

# Tranche 7.8A: Public/private split and doctrine lock

**Objective:** Define the release boundary for autonomous memory evolution before implementation.

**Files:**
- Create: `docs/status/phase-7.8-public-private-split.md`
- Modify: `docs/status/current-implementation-status.md`
- Modify: `docs/status/tranched-plan-status.md`

**Steps:**
1. Create the split doc using the table in this plan as the starting point.
2. Add explicit wording that public behavior is proposal-first and review-gated.
3. Mark autonomous memory evolution as planned/not started in status docs until code lands.
4. Run terminology and public readiness guards.

**Verification:**
```bash
python scripts/terminology_inventory.py --fail-on-public-stale
python scripts/terminology_inventory.py --fail-on-capitalized-prose
python scripts/public_readiness_check.py
git diff --check
```

**Closeout evidence:** split doc exists; status docs make no implemented claim.

---

# Tranche 7.8.1: Evolution proposal schema and ledgers

**Objective:** Add canonical append-only proposal records for memory evolution actions.

**Files:**
- Create: `src/shyftr/evolution.py`
- Modify: `src/shyftr/layout.py`
- Test: `tests/test_memory_evolution_schema.py`

**Implementation outline:**
- Add `EvolutionProposal` dataclass with fields:
  - `proposal_id`
  - `proposal_type`: `split_candidate`, `merge_memories`, `supersede_memory`, `deprecate_memory`, `replace_memory`, `forget_memory`, `redact_memory`, `promote_missing_memory`
  - `target_ids`
  - `candidate_ids`
  - `evidence_refs`
  - `rationale`
  - `confidence`
  - `risk_level`
  - `projection_delta`
  - `requires_review=True`
  - `auto_apply=False`
  - `requires_simulation`
  - `created_at`
- Add append/read helpers for `ledger/evolution/proposals.jsonl` and `ledger/evolution/reviews.jsonl`.
- Add validation that every proposal has at least one evidence reference or explicit synthetic fixture reference.

**Test-first steps:**
1. Write tests for proposal serialization and validation.
2. Write tests proving invalid proposal types fail.
3. Write tests proving ledger append is append-only.
4. Implement minimal schema/helpers.
5. Run focused tests.

**Verification:**
```bash
python -m pytest tests/test_memory_evolution_schema.py -q
```

---

# Tranche 7.8.2: Arrival atomicity and split proposal engine

**Objective:** Detect oversized or multi-topic candidates on arrival and emit split proposals without auto-promoting child memories.

**Files:**
- Modify: `src/shyftr/evolution.py`
- Modify or wrap: `src/shyftr/extract.py`
- Test: `tests/test_memory_evolution_split.py`
- Docs: `docs/concepts/autonomous-memory-evolution.md`

**Public-safe algorithm:**
- Use deterministic token/character thresholds.
- Use paragraph and heading boundaries before sentence fallback.
- Add a simple topic-shift heuristic based on keyword overlap/FTS tokens.
- Emit proposed child texts with parent candidate ID, boundaries, rationale, and evidence refs.
- Do not write child candidates directly unless review accepts the split.

**Test-first steps:**
1. Add a synthetic long candidate fixture with two unrelated topics.
2. Assert `propose_candidate_split(...)` emits `split_candidate` with two or more child texts.
3. Assert short single-topic candidates emit no proposal.
4. Assert proposal references original candidate/evidence and has `auto_apply=False`.
5. Implement the engine.

**Verification:**
```bash
python -m pytest tests/test_memory_evolution_split.py tests/test_review.py -q
```

---

# Tranche 7.8.3: Duplicate and consolidation proposal engine

**Objective:** Detect likely duplicate or overlapping memories and propose consolidation without losing nuance.

**Files:**
- Modify: `src/shyftr/evolution.py`
- Reuse: `src/shyftr/reports/hygiene.py`
- Test: `tests/test_memory_evolution_consolidation.py`

**Public-safe algorithm:**
- Exact normalized statement matches are high-confidence duplicate proposals.
- Near-duplicate proposals use deterministic token-set overlap and optional existing embedding adapter hooks only when configured.
- Consolidation proposals include source memory IDs, proposed consolidated statement, kept distinctions, confidence, and counterexample notes.
- If entity names differ or risk labels differ, proposal risk is high and review cannot be bypassed.

**Test-first steps:**
1. Test exact duplicate memories generate one `merge_memories` proposal.
2. Test close but distinct memories generate either high-risk proposal or no proposal.
3. Test consolidation never writes to approved memory ledgers directly.
4. Implement and wire into a dry-run report helper.

**Verification:**
```bash
python -m pytest tests/test_memory_evolution_consolidation.py tests/test_hygiene.py -q
```

---

# Tranche 7.8.4: Contradiction, supersession, and replacement proposals

**Objective:** Use new evidence and graph context to propose supersession/replacement/challenge events for stale or contradicted memory.

**Files:**
- Modify: `src/shyftr/evolution.py`
- Reuse: `src/shyftr/graph.py`, `src/shyftr/mutations.py`, `src/shyftr/confidence.py`
- Test: `tests/test_memory_evolution_supersession.py`

**Public-safe algorithm:**
- Detect explicit contradiction markers from feedback: harmful, contradicted, false approval/rejection, stale memory, challenged state.
- Use transparent thresholds such as repeated contradiction count >= 2 for proposal emission.
- Emit `supersede_memory`, `replace_memory`, or `deprecate_memory` proposals with graph edge suggestions.
- Require simulation for proposals that affect retrieval inclusion.

**Test-first steps:**
1. Seed synthetic memory plus repeated contradictory feedback.
2. Assert a supersession/deprecation proposal appears with evidence refs.
3. Assert no lifecycle mutation is appended before review.
4. Assert accepted review path appends lifecycle event through `mutations.py` helpers.
5. Implement review application helper for accepted proposals.

**Verification:**
```bash
python -m pytest tests/test_memory_evolution_supersession.py tests/test_memory_mutations.py tests/test_memory_graph.py -q
```

---

# Tranche 7.8.5: Logical forgetting, redaction, and retention policy proposals

**Objective:** Support review-gated forgetting/redaction/deprecation proposals from policy and feedback signals.

**Files:**
- Modify: `src/shyftr/evolution.py`
- Modify: `src/shyftr/privacy.py` or policy integration only if needed
- Test: `tests/test_memory_evolution_forgetting.py`

**Public-safe algorithm:**
- Public code proposes only from explicit policy inputs or synthetic feedback signals.
- No silent physical deletion.
- Accepted proposals append lifecycle events and projection exclusions.
- Redaction proposals include affected fields and a review rationale; real legal/privacy automation remains private/operator policy.

**Test-first steps:**
1. Seed memory with synthetic sensitivity/retention marker.
2. Assert dry-run emits `forget_memory`/`redact_memory` proposal.
3. Assert active projections exclude memory only after accepted review event.
4. Assert ledger history remains readable for audit where policy allows.

**Verification:**
```bash
python -m pytest tests/test_memory_evolution_forgetting.py tests/test_privacy_sensitivity.py tests/test_memory_mutations.py -q
```

---

# Tranche 7.8.6: Evolution simulator and projection delta report

**Objective:** Let operators see what would change before accepting any evolution proposal.

**Files:**
- Modify: `src/shyftr/evolution.py`
- Modify: `src/shyftr/simulation.py`
- Test: `tests/test_memory_evolution_simulation.py`

**Implementation outline:**
- Add `simulate_evolution_proposal(cell_path, proposal_id)`.
- Report current active memory count, proposed active memory count, affected pack/query examples, retrieval inclusion changes, graph edge changes, and confidence/projection deltas.
- Confirm ledger line counts are unchanged in simulation.

**Test-first steps:**
1. Seed proposal and active memories.
2. Run simulation.
3. Assert `read_only=True` and line counts unchanged.
4. Assert report includes affected IDs and projection delta.

**Verification:**
```bash
python -m pytest tests/test_memory_evolution_simulation.py tests/test_policy_simulation.py -q
```

---

# Tranche 7.8.7: Evolution runner and dry-run scheduler surface

**Objective:** Add one explicit command that scans a cell and emits review-gated evolution proposals.

**Files:**
- Modify: `src/shyftr/cli.py`
- Modify: `src/shyftr/server.py`
- Modify: `src/shyftr/console_api.py`
- Test: `tests/test_memory_evolution_cli.py`, `tests/test_server.py`, `tests/test_console_api.py`

**CLI shape:**
```bash
shyftr evolve scan <cell_path> --dry-run
shyftr evolve scan <cell_path> --write-proposals
shyftr evolve proposals <cell_path>
shyftr evolve simulate <cell_path> <proposal_id>
shyftr evolve review <cell_path> <proposal_id> --decision accept|reject|defer --rationale "..."
```

**API shape:**
- `GET /evolution?cell_path=...`
- `POST /evolution/scan`
- `POST /evolution/{proposal_id}/simulate`
- `POST /evolution/{proposal_id}/review`

**Rules:**
- Default is dry-run.
- `--write-proposals` appends proposals only, not lifecycle mutations.
- Review apply path must require rationale and simulation ref for retrieval-affecting changes.

**Verification:**
```bash
python -m pytest tests/test_memory_evolution_cli.py tests/test_server.py tests/test_console_api.py -q
```

---

# Tranche 7.8.8: Operator UI and memory-control TUI integration

**Objective:** Make evolution proposals operator-visible in both browser console and future CLI/TUI operator surfaces.

**Files:**
- Modify: `apps/console/src/api.ts`
- Modify: `apps/console/src/main.tsx`
- Optional future create: `src/shyftr/memory_control_tui.py` or `apps/memory-control-tui/`
- Test: console build plus API read-model tests

**Browser console requirements:**
- Add “Evolution” surface under frontier/operator review area.
- Show proposal type, risk, target IDs, rationale, evidence refs, projection delta, simulation state, and review state.
- Provide dry-run scan and simulation buttons.
- Do not provide hidden auto-apply.

**TUI requirements:**
- Treat TUI as second operator console, not canonical truth.
- Reuse the same read models and review endpoints.
- Keyboard actions: inspect, simulate, accept, reject, defer, export review packet.

**Verification:**
```bash
npm run build --prefix apps/console
python -m pytest tests/test_console_api.py -q
```

---

# Tranche 7.8.9: Synthetic evals and adversarial safety tests

**Objective:** Prove evolution behavior with synthetic data and guard against over-consolidation, prompt injection, and runaway self-update loops.

**Files:**
- Modify: `src/shyftr/evalgen.py`
- Create: `tests/test_memory_evolution_evalgen.py`
- Create: `examples/evolution/README.md`

**Test scenarios:**
1. Oversized candidate split proposal.
2. Exact duplicate consolidation proposal.
3. Similar-but-not-same memory stays separate.
4. New evidence supersedes old memory only via proposal.
5. Forget/deprecate excludes memory after accepted review only.
6. Malicious evidence cannot force auto-apply.
7. Runner rate limit prevents proposal storms.

**Verification:**
```bash
python -m pytest tests/test_memory_evolution_*.py -q
python -m pytest -q
bash scripts/alpha_gate.sh
```

---

# Phase 7.8 Closeout Gate

**Objective:** Land regulated autonomous memory evolution as a public-safe foundation before Phase 8 productization.

**Required checks:**
```bash
python -m pytest -q
python scripts/terminology_inventory.py --fail-on-public-stale
python scripts/terminology_inventory.py --fail-on-capitalized-prose
python scripts/public_readiness_check.py
npm run build --prefix apps/console
git diff --check
bash scripts/alpha_gate.sh
```

**Acceptance criteria:**
- Evolution scan emits proposals only by default.
- Review-gated acceptance uses existing ledger/mutation paths.
- Simulation proves retrieval-affecting proposals before acceptance.
- Large memory splitting is proposed on arrival but not auto-promoted.
- Duplicate consolidation preserves evidence lineage and old memory auditability.
- Logical forgetting/deprecation/redaction is represented as lifecycle events, not physical deletion.
- Browser console and CLI/TUI operator surfaces can inspect and review proposals.
- Public docs do not claim private-core autonomous authority or production-grade deletion/compliance.

**Stop boundary:** After this closeout, stop before Phase 8 unless explicitly instructed to begin productization.
