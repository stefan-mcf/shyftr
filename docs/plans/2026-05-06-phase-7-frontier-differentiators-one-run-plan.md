# Phase 7 frontier differentiators one-run implementation plan

> **For Hermes:** Use `subagent-driven-development` for implementation after this plan is approved. Execute tranche-by-tranche with a single controller/integration owner, independent review lanes, and bridge landing. Do not skip public/private classification before code changes. Do not put private scoring, ranking, compaction, commercial strategy, real memory data, or private operator workflow into public `main`.

**Goal:** Complete Phase 7 in one coordinated run by first defining the 7A public/private split, then landing public-safe frontier memory foundations with tests, docs, and exact-SHA gates.

**Architecture:** Phase 7 is implemented as transparent, append-only, review-gated public primitives plus private-core extension seams. Public `main` receives schemas, ledgers, conservative baseline algorithms, CLI/API/UI review surfaces, synthetic fixtures, and deterministic tests. Any moat-bearing calibration, ranking, optimization, or real-runtime/private-memory evidence stays private unless explicitly approved later.

**Tech Stack:** Python 3.11+, append-only JSONL ledgers, existing ShyftR CLI/API/server/console surfaces, pytest, TypeScript console build, GitHub CI.

**Execution Shape:** phased-assembly + twin-inspection + bridge landing.

**Mutating Owner:** controller/integration owner only. Helper lanes may inspect or implement isolated chunks, but the controller verifies, lands, tests, commits, pushes, and checks CI.

**Human Input Requirement:** none for planning, public-safe implementation, synthetic fixtures, tests, local gates, commits, pushes, and CI checks. Human approval is required only for moving private-core logic into public `main`, using real/private memory data, changing package/release posture, or starting Checkpoint E/F/stable-release cleanup.

---

## Non-negotiable invariants

- Keep ShyftR local-first and controlled-pilot in public claims.
- Preserve scalar `confidence` compatibility while adding richer belief fields.
- Keep ledgers append-only and rebuildable.
- All mutation of memory, rule, regulator, import, reputation, or policy state remains review-gated.
- Imported/federated/cross-cell data never silently becomes local truth.
- Simulation is read-only by default.
- Reputation may prioritize review/proposals; it must never bypass review gates.
- Public baselines must be transparent and boring. Private-core seams may exist, but private algorithms do not land in public `main`.
- Use lowercase lifecycle vocabulary in prose unless writing code/schema/type names.
- Run terminology/public-readiness guards before public-facing commits.

---

## Tranche 7A: public/private split and executable run packet

**Objective:** Convert Phase 7 from frontier ideas into an executable, public-safe run with clear private-core seams.

**Files:**
- Read: `docs/plans/2026-04-24-shyftr-implementation-tranches.md`
- Read: `docs/status/current-implementation-status.md`
- Read: `docs/status/tranched-plan-status.md`
- Read: `docs/concepts/storage-retrieval-learning.md`
- Create: `docs/status/phase-7-public-private-split.md`
- Modify: `docs/status/tranched-plan-status.md`
- Optional modify: `docs/status/current-implementation-status.md`

**Steps:**
1. Read Phase 7 source sections 7.1 through 7.7.
2. Create `docs/status/phase-7-public-private-split.md` with a table for every Phase 7 tranche:
   - public-safe contract/skeleton;
   - public-safe baseline implementation;
   - private-core reserved logic;
   - deferred/non-goal items;
   - tests required;
   - docs required.
3. Update status docs only where stale after the Phase 6 landing. Do not overclaim Phase 7 as implemented.
4. Add a one-run gate checklist to the split doc:
   - public/private classification complete;
   - scalar compatibility preserved;
   - review gates preserved;
   - full local gates green;
   - GitHub CI green for exact SHA.
5. Verify the split doc does not contain local absolute paths, private strategy, or implementation secrets.

**Verification:**
```bash
git diff --check
python scripts/terminology_inventory.py --fail-on-public-stale
python scripts/terminology_inventory.py --fail-on-capitalized-prose
python scripts/public_readiness_check.py
```

**Closeout evidence:** `docs/status/phase-7-public-private-split.md` exists and status docs truthfully identify Phase 7 as planned/in progress, not complete.

---

## Tranche 7.1: Bayesian confidence baseline

**Objective:** Add transparent confidence belief fields while preserving existing scalar confidence behavior.

**Files:**
- Inspect: `src/shyftr/models.py`
- Inspect: `src/shyftr/ledger.py`
- Inspect: `src/shyftr/pack.py`
- Inspect: `src/shyftr/loadout.py`
- Inspect: `src/shyftr/console_api.py`
- Inspect: `apps/console/src/main.tsx`
- Create or modify: `src/shyftr/confidence.py`
- Modify as needed: model serialization and pack projection code
- Test: `tests/test_confidence_model.py`

**Public baseline:** Beta-binomial style counts and uncertainty intervals are allowed if implemented transparently and deterministically. Advanced calibration, learned weights, private evaluator data, or proprietary ranking use stays private.

**Steps:**
1. Write tests for a new memory with little evidence showing high uncertainty.
2. Write tests for positive feedback increasing expected confidence and reducing uncertainty.
3. Write tests for negative feedback decreasing expected confidence and preserving auditability.
4. Write tests proving legacy scalar `confidence` still reads and serializes.
5. Implement `ConfidenceState` or equivalent helpers:
   - `prior`;
   - `positive_evidence_count`;
   - `negative_evidence_count`;
   - `expected_confidence`;
   - `uncertainty`;
   - optional `lower_bound` / `upper_bound` if kept deterministic and simple.
6. Wire the helper into memory projection without changing append-only ledger truth unexpectedly.
7. Expose the belief state in CLI/API/console only as display metadata; do not let it silently mutate memory without feedback/review.
8. Keep pack selection behavior compatible unless an explicit retrieval mode later opts in.

**Verification:**
```bash
python -m pytest -q tests/test_confidence_model.py
python -m pytest -q tests/test_pack.py tests/test_policy.py tests/test_privacy_sensitivity.py
```

**Closeout evidence:** confidence fields are tested, scalar compatibility is tested, and no private scoring logic is introduced.

---

## Tranche 7.2: causal memory graph foundation

**Objective:** Add an append-only, rebuildable graph ledger that explains why memory helped, failed, contradicted, or depended on other memory.

**Files:**
- Inspect: `src/shyftr/layout.py`
- Inspect: `src/shyftr/feedback.py` or current feedback handling modules
- Inspect: `src/shyftr/pack.py`
- Create: `src/shyftr/graph.py`
- Modify: `src/shyftr/layout.py`
- Modify as needed: CLI/API read surfaces
- Test: `tests/test_memory_graph.py`

**Allowed edge types:**
- `caused_success`
- `contributed_to_failure`
- `contradicted_by`
- `supersedes`
- `depends_on`
- `applies_under`
- `invalid_under`
- `co_retrieved_with`
- `ignored_with`

**Steps:**
1. Add seed ledger path such as `ledger/graph_edges.jsonl`.
2. Write tests for appending graph edges with provenance and reviewer metadata.
3. Write tests for invalid edge type rejection.
4. Write tests proving graph reads are rebuildable from ledger rows.
5. Implement graph edge model/helper functions.
6. Add conservative derivation helpers from explicit feedback/review only; do not infer hidden causality.
7. Add pack explainability hooks that can include graph context labels without changing pack selection yet.
8. Add CLI/API list/read endpoints if consistent with existing project surfaces.

**Verification:**
```bash
python -m pytest -q tests/test_memory_graph.py
python -m pytest -q tests/test_pack.py tests/test_console_api.py tests/test_server.py
```

**Closeout evidence:** graph ledger is append-only, edge semantics are explicit, and pack explainability remains review/provenance linked.

---

## Tranche 7.3: read-only policy simulation sandbox

**Objective:** Let operators replay historical pack requests under proposed public-safe retrieval settings before applying changes.

**Files:**
- Inspect: `src/shyftr/pack.py`
- Inspect: `src/shyftr/loadout.py`
- Inspect: `src/shyftr/ledger.py`
- Create: `src/shyftr/simulation.py`
- Modify as needed: `src/shyftr/cli.py`, `src/shyftr/console_api.py`, `src/shyftr/server.py`, console API/UI
- Test: `tests/test_policy_simulation.py`

**Steps:**
1. Write tests proving simulation does not append to production ledgers except optional explicit simulation report ledgers.
2. Write tests comparing current policy vs proposed policy:
   - selected IDs;
   - missed IDs;
   - caution labels;
   - estimated token usage;
   - changed ranking/order where public-safe weights differ.
3. Implement a simulation request schema with explicit cell path, historical pack request reference or inline query, and proposed settings.
4. Implement read-only replay using existing pack/read helpers.
5. Add a simulation report object with deterministic diff fields.
6. Add CLI/API/console surfaces for dry-run simulation.
7. Require explicit operator action for any future policy application; do not implement auto-apply in this tranche.

**Verification:**
```bash
python -m pytest -q tests/test_policy_simulation.py
python -m pytest -q tests/test_pack.py tests/test_console_api.py tests/test_server.py
```

**Closeout evidence:** simulation is read-only, deterministic, and usable as a gate before retrieval or regulator changes.

---

## Tranche 7.4: adaptive retrieval modes

**Objective:** Add explicit retrieval modes that make pack behavior predictable for different mission-risk profiles.

**Files:**
- Inspect: `src/shyftr/pack.py`
- Inspect: `src/shyftr/loadout.py`
- Inspect: `src/shyftr/cli.py`
- Inspect: `src/shyftr/console_api.py`
- Create or modify: `src/shyftr/retrieval_modes.py`
- Test: `tests/test_retrieval_modes.py`

**Modes:**
- `conservative`
- `balanced`
- `exploratory`
- `risk_averse`
- `audit`
- `rule_only`
- `low_latency`

**Steps:**
1. Write tests proving the default mode preserves current behavior.
2. Write tests proving conservative/risk-averse modes exclude weak or caution-heavy memory more aggressively.
3. Write tests proving audit mode can include challenged/quarantined records only with labels and never as unlabeled normal memory.
4. Write tests proving rule-only mode returns rules without ordinary memory when requested.
5. Implement a small mode config table with transparent public-safe weights/filters.
6. Add pack request field for retrieval mode with validation.
7. Add CLI/API/console selectors.
8. Run simulation tests to ensure mode changes can be previewed.

**Verification:**
```bash
python -m pytest -q tests/test_retrieval_modes.py tests/test_policy_simulation.py
python -m pytest -q tests/test_pack.py tests/test_loadout.py tests/test_console_api.py tests/test_server.py
```

**Closeout evidence:** modes produce expected differences, default compatibility is preserved, and risky modes remain labeled/review-aware.

---

## Tranche 7.5: reputation baseline

**Objective:** Track reliability of memory sources, agents, reviewers, cells, runtimes, and imported-memory origins without bypassing review gates.

**Files:**
- Inspect: `src/shyftr/review.py`
- Inspect: `src/shyftr/federation.py`
- Inspect: `src/shyftr/registry.py`
- Inspect: feedback modules
- Create: `src/shyftr/reputation.py`
- Modify: `src/shyftr/layout.py`
- Modify as needed: CLI/API/console read surfaces
- Test: `tests/test_reputation.py`

**Metrics:**
- approval rate
- rejection rate
- useful feedback rate
- harmful feedback rate
- contradiction rate
- stale memory rate where existing data supports it

**Steps:**
1. Add append-only reputation event ledger, for example `ledger/reputation/events.jsonl`.
2. Write tests for computing reputation summaries from events.
3. Write tests proving reputation can prioritize review queue ordering.
4. Write tests proving reputation cannot auto-approve, auto-import, or bypass regulator decisions.
5. Implement event recording helpers for approval/rejection/feedback/import review where data is already available.
6. Implement summary projection helpers.
7. Add read-only CLI/API/console surfaces.
8. Keep any advanced reputation weighting private-core reserved.

**Verification:**
```bash
python -m pytest -q tests/test_reputation.py
python -m pytest -q tests/test_cell_federation_import.py tests/test_cross_cell_rule_workflow.py tests/test_console_api.py tests/test_server.py
```

**Closeout evidence:** reputation is measurable, append-only, and never becomes an automatic trust bypass.

---

## Tranche 7.6: self-modifying regulator proposals

**Objective:** Let ShyftR propose regulator/rule improvements from repeated review or feedback patterns, while requiring human review and simulation before acceptance.

**Files:**
- Inspect: `src/shyftr/review.py`
- Inspect: `src/shyftr/distill/rules.py`
- Inspect: `src/shyftr/simulation.py`
- Create or modify: `src/shyftr/regulator_proposals.py`
- Modify as needed: CLI/API/console proposal queues
- Test: `tests/test_regulator_proposals.py`

**Steps:**
1. Write tests for detecting repeated false approvals or repeated false rejections from synthetic events.
2. Write tests for proposal shape:
   - proposal id;
   - examples;
   - counterexamples;
   - impacted rule/regulator area;
   - required simulation report reference;
   - reviewer decision state.
3. Write tests proving proposals do not mutate policy automatically.
4. Implement proposal generation from explicit ledgers only.
5. Require a simulation report before approval when a proposal affects retrieval or regulator behavior.
6. Add approve/reject/defer review functions.
7. Add CLI/API/console review queue surfaces.

**Verification:**
```bash
python -m pytest -q tests/test_regulator_proposals.py tests/test_policy_simulation.py
python -m pytest -q tests/test_console_api.py tests/test_server.py
```

**Closeout evidence:** ShyftR can propose policy improvements, but policy updates remain explicit, reviewed, and simulation-backed.

---

## Tranche 7.7: synthetic training and eval generator

**Objective:** Generate public-safe regression/evaluation tasks from synthetic or operator-approved ledgers so agents can be tested against expected pack use.

**Files:**
- Inspect: existing examples under `examples/`
- Inspect: existing tests and fixture style
- Create: `src/shyftr/evalgen.py`
- Create: `examples/evals/README.md`
- Create: synthetic fixture files under `examples/evals/` if useful
- Modify as needed: CLI/API read/export surfaces
- Test: `tests/test_eval_generator.py`

**Steps:**
1. Write tests for generating deterministic tasks from repeated failures, missing memory notes, contradictions, and high-value memories using synthetic fixtures.
2. Write tests for expected pack item IDs and expected agent behavior text.
3. Write tests proving generated tasks include provenance and no private/local absolute paths.
4. Implement eval task generation helpers.
5. Add CLI export command for JSON/JSONL eval fixtures.
6. Add docs explaining synthetic/default data use and prohibited real/private data use.
7. Ensure generated tasks are stable enough for CI regression tests.

**Verification:**
```bash
python -m pytest -q tests/test_eval_generator.py
python -m pytest -q tests/test_runtime_integration_demo.py tests/test_multi_cell_demo.py
```

**Closeout evidence:** eval generation is deterministic, provenance-linked, and public-safe.

---

## Tranche 7B: integrated console/API/CLI coherence pass

**Objective:** Ensure all Phase 7 public surfaces are coherent, review-gated, and discoverable without overclaiming.

**Files:**
- Inspect/modify: `src/shyftr/cli.py`
- Inspect/modify: `src/shyftr/console_api.py`
- Inspect/modify: `src/shyftr/server.py`
- Inspect/modify: `apps/console/src/api.ts`
- Inspect/modify: `apps/console/src/main.tsx`
- Test: existing console/server/API tests plus any new tests from earlier tranches

**Steps:**
1. Audit CLI help for new commands and consistent vocabulary.
2. Audit API routes for explicit dry-run/review labels where applicable.
3. Audit console UI copy for local-first, review-gated wording.
4. Add missing smoke tests for new endpoints or CLI commands.
5. Ensure no command implies auto-approval, auto-policy mutation, or production-readiness.

**Verification:**
```bash
python -m pytest -q tests/test_console_api.py tests/test_server.py
python -m shyftr.cli --help >/tmp/shyftr-cli-help.txt
python -m shyftr.cli pack --help >/tmp/shyftr-pack-help.txt || true
cd apps/console && npm install && npm run build && npm audit --omit=dev
```

**Closeout evidence:** CLI/API/console provide consistent public-safe access to Phase 7 features.

---

## Tranche 7C: public docs, examples, and status update

**Objective:** Document implemented Phase 7 behavior without exposing private-core details or overclaiming alpha status.

**Files:**
- Modify: `docs/status/current-implementation-status.md`
- Modify: `docs/status/tranched-plan-status.md`
- Create: `docs/concepts/confidence-and-simulation.md`
- Create: `docs/concepts/memory-graph-and-reputation.md`
- Create: `docs/phase-7-example.md` or equivalent public-safe example
- Optional modify: `README.md` only if strictly needed and public-readiness wording stays clean

**Steps:**
1. Document confidence baseline and scalar compatibility.
2. Document graph edge semantics and append-only behavior.
3. Document read-only simulation and retrieval modes.
4. Document reputation baseline and review-gate limitations.
5. Document regulator proposals as proposal-only.
6. Document eval generator using synthetic examples only.
7. Update status docs with evidence-backed claims only.
8. Avoid internal/private strategy, local absolute paths, and stable-release claims.

**Verification:**
```bash
python scripts/terminology_inventory.py --fail-on-public-stale
python scripts/terminology_inventory.py --fail-on-capitalized-prose
python scripts/public_readiness_check.py
git diff --check
```

**Closeout evidence:** public docs match implemented behavior and pass terminology/readiness guards.

---

## Tranche 7D: full bridge landing and exact-SHA proof

**Objective:** Land Phase 7 as one verified run with local and remote proof.

**Files:**
- All changed Phase 7 source, tests, docs, examples, and console files.

**Steps:**
1. Run focused tests from all Phase 7 tranches.
2. Run full Python test suite.
3. Run terminology inventory gates.
4. Run public readiness.
5. Run alpha gate.
6. Run `git diff --check`.
7. Review `git diff --stat` and changed file classification.
8. Commit with a clear message, for example `Implement public-safe Phase 7 frontier foundations`.
9. Push `main`.
10. Fetch and verify `HEAD == origin/main`.
11. Watch GitHub CI for the exact SHA.
12. Record closeout evidence in a status doc only after exact-SHA CI is green.

**Verification:**
```bash
python -m pytest -q
python scripts/terminology_inventory.py --fail-on-public-stale
python scripts/terminology_inventory.py --fail-on-capitalized-prose
python scripts/public_readiness_check.py
git diff --check
bash scripts/alpha_gate.sh
git status --short --branch
git push origin main
git fetch origin main
test "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)"
gh run list --repo stefan-mcf/shyftr --branch main --commit "$(git rev-parse HEAD)" --limit 5
gh run watch <run-id> --repo stefan-mcf/shyftr --exit-status
```

**Closeout evidence:** local gates pass, GitHub CI passes for the exact Phase 7 SHA, worktree is clean, and status docs identify any deferred private-core or future work honestly.

---

## Suggested worker/run routing

Use controller-only for 7A and bridge landing. Use helper lanes only after 7A exists and collision domains are clear.

Recommended lanes after 7A:

| Lane | Scope | Mutability | Notes |
| --- | --- | --- | --- |
| controller/integration | repo state, tranche sequencing, commits, push, CI | mutating | only final owner of `main` |
| confidence lane | 7.1 tests/code | bounded mutating or temp worktree | avoid pack ranking scope creep |
| graph/simulation lane | 7.2 and 7.3 | bounded mutating or temp worktree | graph before simulation where dependencies matter |
| retrieval/reputation lane | 7.4 and 7.5 | bounded mutating or temp worktree | preserve review gates |
| regulator/eval lane | 7.6 and 7.7 | bounded mutating or temp worktree | proposal-only and synthetic-only |
| docs/status lane | 7C | mutating only after implementation facts are verified | public-safe wording |
| review lane | spec/quality/security/public-private split | read-only | independent from builders |

If using persistent Hermes swarm or Factory Droid lanes, launch real named processes with bounded prompts and verify their outputs before landing. If not launched, do not claim swarm/Droid coverage.

---

## Final success criteria

Phase 7 is complete in this one run only when:

- 7A split exists and was followed;
- 7.1 through 7.7 public-safe features are implemented or explicitly deferred with reasons;
- all public ledgers and schemas are append-only/rebuildable;
- scalar confidence compatibility remains tested;
- graph, simulation, retrieval modes, reputation, regulator proposals, and eval generation have focused tests;
- CLI/API/console surfaces are coherent and review-gated;
- public docs and status files are truthful;
- `python -m pytest -q` passes;
- both terminology inventory gates pass;
- public readiness passes;
- `bash scripts/alpha_gate.sh` ends with `ALPHA_GATE_READY`;
- GitHub CI is green for the exact pushed SHA.
