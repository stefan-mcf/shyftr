# Phase 6 multi-cell intelligence tranched implementation plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task. Start with Tranche 6.0 and stop at every tranche closeout gate until the named checks pass. Do not begin Phase 7 from this plan.

**Goal:** Move ShyftR from single-cell local memory to explicit, review-gated multi-cell memory intelligence without accidental cross-cell leakage or silent local-truth mutation.

**Architecture:** Keep each cell ledger as canonical truth. Add a registry projection for discovering cells, explicit cross-cell read operations for resonance, review-gated rule proposals, and selective federation import/export where imported records never become local truth without regulator review. All cross-cell behavior must be explicit, provenance-linked, scoped, and testable.

**Tech stack:** Python 3.11+, dataclass models, append-only JSONL ledgers, existing CLI/FastAPI/console surfaces, pytest, local React console build, existing `scripts/alpha_gate.sh`.

**Plan status:** ready for Phase 6 kickoff planning. This is a planning artifact only; it does not implement Phase 6.

---

## Operator authorization and scope boundary

The operator explicitly rescoped the external tester threshold on 2026-05-06. External tester reports remain deferred and tracked separately, but they do not block continued pre-Phase-6 planning. This plan records that distinction:

- local gates plus operator usability acceptance are enough to plan Phase 6;
- external alpha validation is still not claimed;
- Checkpoint E, Checkpoint F, stable-release wording, hosted SaaS behavior, and Phase 7 are outside this plan;
- Phase 6 implementation must still begin from a clean exact-SHA preflight and tranche-by-tranche review.

## Existing evidence and current repo truth

Read these before implementation:

- `docs/status/current-implementation-status.md`
- `docs/status/tranched-plan-status.md`
- `docs/status/public-alpha-wave-0-4-evidence.md`
- `docs/concepts/storage-retrieval-learning.md`
- `docs/concepts/terminology-compatibility.md`
- `docs/runtime-integration-example.md`
- `docs/plans/2026-04-24-shyftr-implementation-tranches.md`

Current implementation truth to preserve:

- single-cell lifecycle is implemented and locally gated;
- `src/shyftr/resonance.py` already has read-only cross-cell scoring, but uses legacy compatibility models and is not wired to registry, CLI, API, or console surfaces;
- `src/shyftr/distill/patterns.py` and `src/shyftr/distill/rules.py` already provide pattern/rule-like logic, but public paths and review surfaces need reconciliation;
- `src/shyftr/layout.py` seeds public ledgers such as `ledger/patterns/*.jsonl` and `ledger/rules/*.jsonl`, but existing pattern/rule code still leans on compatibility paths;
- `src/shyftr/pack.py` must remain explicit about what scopes and trust labels are allowed into a pack;
- `src/shyftr/privacy.py` and `src/shyftr/policy.py` already provide important local policy primitives that Phase 6 must reuse instead of bypassing.

## External research incorporated

This plan uses the following public design references as robustness inputs:

- W3C PROV overview, `https://www.w3.org/TR/prov-overview/`: provenance should record entities, activities, agents, and derivation relationships. Phase 6 applies this by requiring source cell IDs, source record IDs, export/import activity IDs, timestamps, and reviewer decisions on cross-cell proposals.
- RFC 9334 Remote ATtestation procedureS architecture, `https://www.rfc-editor.org/rfc/rfc9334.txt`: even though Phase 6 is local-first, its separation of attester/evidence/verifier/relying-party roles is useful for later trusted federation. Phase 6 should keep export package metadata and trust labels explicit so stronger attestation can be added later without changing ledger truth.
- RFC 8725 JSON Web Token best current practices, `https://www.rfc-editor.org/rfc/rfc8725.txt`, and RFC 7519 JWT, `https://www.rfc-editor.org/rfc/rfc7519.txt`: if signed export packages are added later, the plan must avoid algorithm confusion, weak claims, and implicit trust from signatures alone. Signatures can authenticate package origin; they must not bypass import review by default.

Public-safe planning principles derived from those references:

1. Provenance is first-class data, not a comment.
2. Cross-cell operations require explicit source and target scope.
3. Authentication, when present, is not authorization.
4. Imports are proposals until reviewed.
5. Rebuildable projections may cache cross-cell metadata, but ledgers remain canonical.
6. A remote or federated source never gains local-truth status silently.
7. The weakest safe default is deny-by-default for export, import, retrieval, and pack inclusion.

## Non-goals

- No hosted control plane.
- No remote network synchronization.
- No production data.
- No private-core ranking, compaction, commercial strategy, or operator workflow leakage.
- No Phase 7 Bayesian confidence, causal graph, simulation sandbox, or advanced private-core differentiators.
- No broad external-alpha or stable-release claims.

## Global invariants

Every Phase 6 tranche must preserve these invariants:

1. **Cell ledger authority:** a cell ledger remains canonical only for its own cell.
2. **Explicit cross-cell scope:** every cross-cell read/write/proposal requires named source and target cells or named registry selection.
3. **No accidental leakage:** default pack/search/retrieval behavior remains single-cell unless an explicit cross-cell flag/scope is provided.
4. **No silent mutation:** resonance, import, and rule proposal do not rewrite source cell ledgers.
5. **Review-gated promotion:** shared rules and imported memory require regulator review before local-truth treatment.
6. **Provenance required:** cross-cell records store source cell ID, source record IDs, derivation kind, activity ID, timestamp, and review status.
7. **Trust labels are bounded:** allowed labels are `local`, `imported`, `federated`, and `verified`; anything else fails validation.
8. **Public terminology:** public docs and surfaces use evidence, candidate, memory, pattern, rule, cell, ledger, regulator, grid, pack, feedback, quarantine.
9. **Compatibility preserved:** legacy aliases/readers remain compatibility only; do not delete them without a migration proof.
10. **Public/private split:** public repo may contain safe contracts, synthetic fixtures, tests, and local-first implementation; private scoring/ranking/compaction remains out of public main.

## Worker-pattern route

Recommended shape: phased-assembly with twin-inspection overlay.

- Controller/integration: owns the canonical repo and final commits.
- Registry lane: `src/shyftr/registry.py`, registry tests, CLI/API list surfaces.
- Resonance lane: read-only cross-cell scoring, public model support, provenance.
- Rule lane: review-gated shared rule proposals, pack scoping, rule ledgers.
- Federation lane: export/import package schema, import review queue, trust labels.
- UI/API lane: console selector/review surfaces and local service routes.
- Review lane: independent spec/security review before each tranche closeout.

Persistent Hermes swarm profiles are not required for the plan itself. Use persistent profiles only if execution becomes multi-day or the operator explicitly requests named profile lanes.

## Preflight before any Phase 6 implementation

Run from repo root:

```bash
git fetch origin main
git status --short --branch
test "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)"
python scripts/public_readiness_check.py
python scripts/terminology_inventory.py --fail-on-public-stale
python scripts/terminology_inventory.py --fail-on-capitalized-prose
git diff --check
bash scripts/alpha_gate.sh
```

Pass condition:

- worktree clean;
- local HEAD equals `origin/main`;
- public readiness PASS;
- terminology guards PASS;
- diff check PASS;
- alpha gate ends with `ALPHA_GATE_READY`;
- GitHub CI green for exact SHA if a planning/status commit was pushed.

Failure behavior:

- repair the failing gate before implementation;
- do not begin Tranche 6.0 while repo health is ambiguous.

---

## Tranche 6.0: public-model and path reconciliation planlet

**Objective:** Remove ambiguity before new behavior by documenting how existing compatibility code maps to current public model names and ledger paths.

**Files:**

- Create: `docs/status/phase-6-kickoff-reconciliation.md`
- Modify if needed after review: `docs/status/current-implementation-status.md`
- Read: `src/shyftr/models.py`, `src/shyftr/resonance.py`, `src/shyftr/distill/patterns.py`, `src/shyftr/distill/rules.py`, `src/shyftr/pack.py`, `src/shyftr/layout.py`

**Implementation steps:**

1. Create a kickoff reconciliation doc with a table mapping:
   - `Fragment` compatibility model to public candidate/evidence usage;
   - `Trace` compatibility model to public memory usage;
   - `Alloy` compatibility model to public pattern usage;
   - `DoctrineProposal` compatibility model to public rule proposal usage;
   - compatibility ledgers to public ledgers.
2. State that Phase 6 implementation must add or use public model surfaces without deleting compatibility readers.
3. State the public ledger write targets:
   - patterns: `ledger/patterns/proposed.jsonl`, `ledger/patterns/approved.jsonl`;
   - rules: `ledger/rules/proposed.jsonl`, `ledger/rules/approved.jsonl`;
   - registry: `ledger/cell_registry.jsonl` or an equivalent root-level registry ledger selected in Tranche 6.1;
   - federation: `ledger/federation_events.jsonl` plus an import review queue ledger selected in Tranche 6.4.
4. Add a stop note that no Phase 6 code should be written until the reconciliation doc exists and public terminology guards pass.

**Tests/checks:**

```bash
python scripts/terminology_inventory.py --fail-on-public-stale
python scripts/terminology_inventory.py --fail-on-capitalized-prose
python scripts/public_readiness_check.py
git diff --check
```

**Acceptance criteria:**

- implementation team has an explicit compatibility-to-public mapping;
- no public doc claims Phase 6 is implemented;
- no stale primary vocabulary is introduced;
- no compatibility deletion is planned without proof.

**Commit:**

```bash
git add docs/status/phase-6-kickoff-reconciliation.md docs/status/current-implementation-status.md
git commit -m "docs: reconcile phase 6 public model surfaces"
```

---

## Tranche 6.1: cell registry core

**Objective:** Track multiple cells and their relationships through an append-only registry projection while preserving single-cell ledger authority.

**Files:**

- Create: `src/shyftr/registry.py`
- Create: `tests/test_cell_registry.py`
- Modify: `src/shyftr/layout.py`
- Modify: `src/shyftr/models.py` if a `CellRegistryEntry` model is preferred
- Modify: `src/shyftr/cli.py`
- Modify: `src/shyftr/server.py`
- Modify: `src/shyftr/console_api.py`
- Modify: `apps/console/src/**` only for a minimal selector/list view

**Data model:**

Registry entries must include:

- `cell_id`
- `cell_type`
- `path`
- `owner`
- `tags`
- `domain`
- `trust_boundary`
- `registered_at`
- `status`
- optional `relationship_edges`
- optional `metadata`

Use append-only events, with a folded projection for list/detail queries.

Suggested event kinds:

- `registered`
- `updated`
- `unregistered`
- `relationship_added`
- `relationship_removed`

**Safety defaults:**

- missing `trust_boundary` fails validation;
- duplicate active `cell_id` fails validation;
- cell ID uses existing safe path segment validation;
- registry path must be local and explicit;
- registry listing is metadata only and never grants pack/search access by itself.

**Test-first tasks:**

1. Add `test_register_cell_appends_to_registry`.
2. Add `test_register_cell_without_required_fields_raises`.
3. Add `test_register_cell_rejects_duplicate_cell_id`.
4. Add `test_list_cells_returns_all_registered_cells`.
5. Add `test_list_cells_by_type_filters_correctly`.
6. Add `test_list_cells_by_tag_filters_correctly`.
7. Add `test_list_cells_on_empty_registry_returns_empty_list`.
8. Add `test_unregister_cell_removes_from_active_projection`.
9. Add `test_unregister_nonexistent_cell_raises`.
10. Add `test_registry_file_is_append_only_not_overwritten`.
11. Add `test_cell_discovery_returns_initialized_cells_only`.
12. Add `test_no_accidental_cross_cell_leakage_when_cells_not_selected`.
13. Add `test_cell_registry_persists_across_sessions`.
14. Add `test_cell_registry_rejects_invalid_cell_id_format`.
15. Add `test_cell_registry_round_trip_to_jsonl`.

**Implementation tasks:**

1. Implement a `CellRegistryEntry` dataclass or equivalent validation helper.
2. Implement `register_cell(registry_path, entry)`.
3. Implement `list_cells(registry_path, *, cell_type=None, tags=None, status="active")`.
4. Implement `get_cell(registry_path, cell_id)`.
5. Implement `unregister_cell(registry_path, cell_id, reason)`.
6. Implement folded projection from append-only events.
7. Add CLI commands:
   - `shyftr cell register`
   - `shyftr cell list`
   - `shyftr cell info`
   - `shyftr cell unregister`
8. Add local service endpoints:
   - `GET /cells`
   - `GET /cells/{cell_id}`
   - `POST /cells/register`
9. Add console API list/detail helpers.
10. Add minimal console cell selector/list; keep it metadata-only.

**Gate:**

```bash
python -m pytest tests/test_cell_registry.py -q
python -m pytest tests/test_cli.py tests/test_server.py tests/test_console_api.py -q
python scripts/terminology_inventory.py --fail-on-public-stale
python scripts/terminology_inventory.py --fail-on-capitalized-prose
git diff --check
```

**Acceptance criteria:**

- multiple cells are discoverable;
- registry is append-only or event-sourced with deterministic projection;
- cross-cell operations remain explicit;
- no default single-cell pack/search behavior changes;
- no accidental cross-cell leakage.

**Commit:**

```bash
git add src/shyftr/registry.py src/shyftr/layout.py src/shyftr/models.py src/shyftr/cli.py src/shyftr/server.py src/shyftr/console_api.py apps/console/src tests/test_cell_registry.py tests/test_cli.py tests/test_server.py tests/test_console_api.py
git commit -m "feat: add explicit cell registry"
```

---

## Tranche 6.2: registry-scoped cross-cell resonance

**Objective:** Make cross-cell resonance operate over explicit registry-selected cells, public model surfaces, and provenance-rich read-only results.

**Files:**

- Modify: `src/shyftr/resonance.py`
- Modify: `src/shyftr/registry.py`
- Modify: `src/shyftr/cli.py`
- Modify: `src/shyftr/server.py`
- Create: `tests/test_resonance_registry.py`
- Extend: `tests/test_resonance.py`

**Data model:**

A resonance result must include:

- `resonance_id`
- `source_cell_ids`
- `source_record_ids`
- `source_record_kinds`
- `similarity_method`
- `threshold`
- `score`
- `provenance`
- `created_at`
- `proposal_status`, default `advisory`

**Safety defaults:**

- resonance is read-only;
- missing registry entries fail clearly;
- source and target cells must be explicit;
- results are advisory and cannot create rules directly;
- single-cell input returns no cross-cell result unless explicitly allowed for diagnostics.

**Test-first tasks:**

1. Add `test_resonance_filters_by_registry_cells_only`.
2. Add `test_resonance_provenance_tracks_all_source_cell_ids`.
3. Add `test_resonance_requires_cross_cell_by_default`.
4. Add `test_cross_cell_resonance_does_not_mutate_local_memories`.
5. Add `test_resonance_score_includes_cell_diversity_factor`.
6. Add `test_resonance_with_one_cell_returns_empty_when_cross_cell_required`.
7. Add `test_resonance_output_is_deterministic`.
8. Add `test_resonance_rejects_nonexistent_cell_ids_in_registry`.
9. Add public model tests for `Memory` and `Pattern` in addition to compatibility models.

**Implementation tasks:**

1. Add public-model resonance helpers such as `detect_similar_memories` and `detect_similar_patterns` without removing compatibility helpers.
2. Add registry-scoped loader that accepts explicit `cell_id` selection.
3. Add deterministic provenance payload to resonance results.
4. Add CLI command:
   - `shyftr resonance scan --registry <path> --cell <id> --cell <id> --dry-run`
5. Add local service endpoint:
   - `POST /resonance/scan`
6. Ensure dry-run is the default for new surfaces until rule proposal wiring exists.
7. Document in help text that resonance does not mutate ledgers.

**Gate:**

```bash
python -m pytest tests/test_resonance.py tests/test_resonance_registry.py tests/test_cell_registry.py -q
python -m pytest tests/test_cli.py tests/test_server.py -q
git diff --check
```

**Acceptance criteria:**

- repeated memories/patterns can be detected across registered cells;
- resonance has provenance;
- resonance is deterministic and read-only;
- source cell ledgers are unchanged after scan;
- no rule is promoted silently.

**Commit:**

```bash
git add src/shyftr/resonance.py src/shyftr/registry.py src/shyftr/cli.py src/shyftr/server.py tests/test_resonance.py tests/test_resonance_registry.py tests/test_cell_registry.py tests/test_cli.py tests/test_server.py
git commit -m "feat: add registry-scoped cross-cell resonance"
```

---

## Tranche 6.3: shared rule proposal queue

**Objective:** Convert high-resonance cross-cell findings into review-gated, scoped rule proposals without making global policy from weak evidence.

**Files:**

- Modify: `src/shyftr/distill/rules.py`
- Modify: `src/shyftr/models.py`
- Modify: `src/shyftr/ledger.py` if append helpers are needed
- Modify: `src/shyftr/policy.py`
- Modify: `src/shyftr/cli.py`
- Modify: `src/shyftr/server.py`
- Modify: `src/shyftr/console_api.py`
- Modify: `apps/console/src/**` for the minimal rule review UI, or explicitly defer UI work to Tranche 6.6 and remove console files from the commit.
- Create: `tests/test_cross_cell_rule_workflow.py`

**Rule proposal requirements:**

- source resonance IDs;
- source pattern IDs or memory IDs;
- source cell IDs;
- proposed scope;
- minimum cell diversity evidence;
- confidence summary;
- reviewer status;
- reviewer ID or public-safe label if available;
- decision timestamp;
- provenance chain.

**Safety defaults:**

- low-confidence single-source proposals cannot become global rules;
- every rule has a scope;
- unreviewed rules are excluded from packs;
- rejected proposals are deduplicated by fingerprint;
- approved shared rules do not mutate source cell ledgers;
- pack inclusion obeys scope constraints.

**Test-first tasks:**

1. Add `test_rule_proposal_from_high_resonance_pattern`.
2. Add `test_rule_proposal_requires_review_before_promotion`.
3. Add `test_rule_proposal_review_writes_append_only_event`.
4. Add `test_approved_rule_is_retrievable_in_packs_for_scoped_cells`.
5. Add `test_rule_scope_constrains_retrieval`.
6. Add `test_rule_promotion_does_not_mutate_local_cell_memories`.
7. Add `test_rule_promotion_records_provenance_with_source_pattern_ids`.
8. Add `test_rule_from_single_weak_source_cannot_create_global_policy`.
9. Add `test_rule_proposals_are_deduplicated`.
10. Add `test_rejected_rule_proposal_blocks_duplicate_from_same_evidence`.
11. Add `test_rule_promotion_provenance_includes_source_cell_ids`.
12. Add `test_global_rule_requires_minimum_cell_diversity`.

**Implementation tasks:**

1. Add a public `RuleProposal` workflow if the existing model is insufficient.
2. Write proposals to `ledger/rules/proposed.jsonl` while preserving compatibility outputs where required.
3. Add approval/rejection event writing.
4. Add rule scope validation.
5. Add pack retrieval support for approved public rules in `ledger/rules/approved.jsonl`.
6. Add CLI commands:
   - `shyftr rule propose-from-resonance`
   - `shyftr rule list`
   - `shyftr rule approve`
   - `shyftr rule reject`
7. Add local service endpoints:
   - `GET /rules/proposed`
   - `POST /rules/{rule_id}/approve`
   - `POST /rules/{rule_id}/reject`
8. Add console API route and minimal review UI for proposed rules.

**Gate:**

```bash
python -m pytest tests/test_cross_cell_rule_workflow.py tests/test_resonance_registry.py tests/test_cell_registry.py -q
python -m pytest tests/test_pack.py tests/test_policy.py tests/test_console_api.py tests/test_server.py -q
git diff --check
```

**Acceptance criteria:**

- rules are reviewed, scoped, and provenance-linked;
- global policy cannot be created from one weak source;
- approved rules appear only in allowed packs;
- source cell ledgers are not rewritten;
- rejected proposals cannot churn endlessly.

**Commit:**

```bash
git add src/shyftr/distill/rules.py src/shyftr/models.py src/shyftr/ledger.py src/shyftr/policy.py src/shyftr/pack.py src/shyftr/cli.py src/shyftr/server.py src/shyftr/console_api.py apps/console/src tests/test_cross_cell_rule_workflow.py tests/test_pack.py tests/test_policy.py tests/test_console_api.py tests/test_server.py
git commit -m "feat: add review-gated shared rule workflow"
```

---

## Tranche 6.4: federation package schema and export

**Objective:** Define a selective, public-safe export package for approved memory, pattern, and rule projections without exposing private/transient data.

**Files:**

- Create: `src/shyftr/federation.py`
- Create: `tests/test_cell_federation_export.py`
- Modify: `src/shyftr/privacy.py`
- Modify: `src/shyftr/cli.py`
- Modify: `src/shyftr/server.py`
- Create: `docs/concepts/federation-protocol.md`

**Export package fields:**

- `schema_version`
- `export_id`
- `source_cell_id`
- `source_cell_type`
- `created_at`
- `records`
- `redaction_summary`
- `provenance`
- `policy_summary`
- optional `package_signature` reserved for future use

**Records may include only:**

- approved memories;
- approved patterns;
- approved rules;
- summary statistics that do not reveal private local paths or sensitive data.

**Records must exclude:**

- pending/rejected candidates;
- unreviewed imports;
- raw evidence unless explicitly approved by policy;
- feedback/event logs unless explicitly needed and redacted;
- grid/index files;
- local absolute paths;
- secrets and environment files.

**Test-first tasks:**

1. Add `test_export_cell_approved_memories_creates_export_file`.
2. Add `test_export_excludes_pending_and_rejected_candidates`.
3. Add `test_export_redacts_sensitive_memories_based_on_policy`.
4. Add `test_export_excludes_feedback_and_confidence_events`.
5. Add `test_export_round_trip_schema_validates`.
6. Add `test_export_records_source_cell_id_and_record_ids`.
7. Add `test_export_does_not_include_grid_files`.
8. Add `test_export_rejects_unknown_record_kind`.

**Implementation tasks:**

1. Define federation export schema and validator.
2. Implement `export_cell(cell_path, output_path, policy)`.
3. Reuse existing privacy/access policy helpers for redaction decisions.
4. Add CLI command:
   - `shyftr cell export --cell-path <path> --output <path>`
5. Add local service endpoint:
   - `POST /cells/{cell_id}/export`
6. Write `docs/concepts/federation-protocol.md` with package schema and non-goals.
7. Keep signatures deferred unless a clean public-safe local implementation is added with tests.

**Gate:**

```bash
python -m pytest tests/test_cell_federation_export.py tests/test_privacy_sensitivity.py -q
python scripts/public_readiness_check.py
python scripts/terminology_inventory.py --fail-on-public-stale
python scripts/terminology_inventory.py --fail-on-capitalized-prose
git diff --check
```

**Acceptance criteria:**

- export is selective and auditable;
- sensitive or unapproved records are excluded/redacted;
- grid/projection data is not exported as truth;
- provenance is present;
- no private local paths are emitted.

**Commit:**

```bash
git add src/shyftr/federation.py src/shyftr/privacy.py src/shyftr/cli.py src/shyftr/server.py docs/concepts/federation-protocol.md tests/test_cell_federation_export.py tests/test_privacy_sensitivity.py
git commit -m "feat: add selective cell federation export"
```

---

## Tranche 6.5: federation import and review queue

**Objective:** Import federation packages as review-gated non-local records that require regulator approval before local-truth treatment.

**Files:**

- Modify: `src/shyftr/federation.py`
- Modify: `src/shyftr/layout.py`
- Modify: `src/shyftr/models.py`
- Modify: `src/shyftr/review.py`
- Modify: `src/shyftr/pack.py`
- Modify: `src/shyftr/cli.py`
- Modify: `src/shyftr/server.py`
- Modify: `src/shyftr/console_api.py`
- Modify: `apps/console/src/**` for the import review queue, or explicitly defer UI work to Tranche 6.6 and remove console files from the commit.
- Create: `tests/test_cell_federation_import.py`
- Extend: `tests/test_review.py`

**Import ledgers:**

Select explicit public paths during implementation. Recommended:

- `ledger/federation_events.jsonl`
- `ledger/import_candidates.jsonl`
- `ledger/import_reviews.jsonl`

**Trust labels:**

- `local`: originated and approved in this cell;
- `imported`: received from another cell, not yet local truth;
- `federated`: received from an allowed federation source but still non-local unless policy says otherwise;
- `verified`: reviewed and approved for local use.

**Safety defaults:**

- imported records start as `imported` unless source policy explicitly maps them to `federated`;
- neither `imported` nor `federated` records enter default packs until reviewed or explicitly requested by scope;
- import writes append-only events and review candidates, never directly rewrites approved local ledgers;
- rejection prevents local pack inclusion;
- source provenance chain is preserved.

**Test-first tasks:**

1. Add `test_import_into_cell_starts_with_imported_trust_label`.
2. Add `test_imported_memory_requires_review_before_local_truth_treatment`.
3. Add `test_import_review_approval_changes_trust_label_to_verified`.
4. Add `test_import_review_rejection_excludes_import_from_packs`.
5. Add `test_import_without_review_is_not_discoverable_via_default_search`.
6. Add `test_federated_trust_label_does_not_bypass_policy_by_default`.
7. Add `test_federation_provenance_includes_source_cell_id`.
8. Add `test_federation_is_selective_cell_can_import_single_memories_not_entire_cell`.
9. Add `test_federation_audit_log_records_all_imports`.
10. Add `test_no_silent_local_truth_mutation_on_import`.
11. Add `test_import_provenance_chain_is_preserved`.
12. Add `test_import_from_untrusted_cell_starts_as_imported_not_verified`.
13. Add `test_federation_with_nonexistent_source_cell_raises`.

**Implementation tasks:**

1. Implement federation package validation.
2. Implement `import_package(target_cell_path, package_path, review_mode="required")`.
3. Write import events to append-only federation event ledger.
4. Create import review candidates instead of approved local memory.
5. Add review approval/rejection functions.
6. Integrate reviewed imports into pack/search only through explicit trust-label and scope handling.
7. Add CLI commands:
   - `shyftr cell import --cell-path <path> --package <path>`
   - `shyftr import list`
   - `shyftr import approve`
   - `shyftr import reject`
8. Add local service endpoints:
   - `POST /cells/{cell_id}/import`
   - `GET /imports/pending`
   - `POST /imports/{import_id}/approve`
   - `POST /imports/{import_id}/reject`
9. Add console review queue for imports.

**Gate:**

```bash
python -m pytest tests/test_cell_federation_import.py tests/test_cell_federation_export.py -q
python -m pytest tests/test_pack.py tests/test_review.py tests/test_privacy_sensitivity.py -q
git diff --check
```

**Acceptance criteria:**

- imported memory starts with non-local trust label;
- unreviewed import is excluded from default packs/search;
- import review is append-only and auditable;
- local truth is not silently mutated;
- provenance chain survives export/import/review.

**Commit:**

```bash
git add src/shyftr/federation.py src/shyftr/layout.py src/shyftr/models.py src/shyftr/review.py src/shyftr/pack.py src/shyftr/cli.py src/shyftr/server.py src/shyftr/console_api.py apps/console/src tests/test_cell_federation_import.py tests/test_cell_federation_export.py tests/test_pack.py tests/test_review.py
git commit -m "feat: add review-gated federation import"
```

---

## Tranche 6.6: console and local service hardening

**Objective:** Make multi-cell behavior operator-visible through local UI/API surfaces without widening claims or creating implicit cross-cell behavior.

**Files:**

- Modify: `src/shyftr/server.py`
- Modify: `src/shyftr/console_api.py`
- Modify: `apps/console/src/**`
- Extend: `tests/test_server.py`
- Extend: `tests/test_console_api.py`
- Add or extend console tests if present

**UI/API surfaces:**

- cell selector/list;
- cell detail metadata;
- resonance scan results;
- rule proposal queue;
- import review queue;
- explicit trust label badges;
- provenance detail panels;
- warnings when cross-cell scope is active.

**Safety defaults:**

- local service remains bound to localhost by default;
- no hosted claims;
- UI cannot approve imports/rules without explicit operator action;
- UI labels distinguish local, imported, federated, verified;
- API rejects cross-cell operations missing explicit registry/cell selection.

**Test-first tasks:**

1. Add `test_server_lists_registered_cells`.
2. Add `test_server_rejects_cross_cell_scan_without_explicit_cells`.
3. Add `test_console_api_exposes_trust_labels`.
4. Add `test_console_api_import_queue_excludes_approved_local_memory`.
5. Add `test_console_api_rule_review_requires_decision`.
6. Add `test_console_build_includes_cell_selector_without_hosted_claims` if practical.

**Implementation tasks:**

1. Add/complete local service route wiring for registry, resonance, rules, and imports.
2. Add console API adapters.
3. Add minimal React components for operator visibility.
4. Add UI copy that says local-first and explicit cross-cell only.
5. Ensure console build passes.

**Gate:**

```bash
python -m pytest tests/test_server.py tests/test_console_api.py -q
cd apps/console && npm run build && npm audit --omit=dev
git diff --check
```

**Acceptance criteria:**

- operator can see registered cells;
- operator can see cross-cell provenance and trust labels;
- review queues are visible and explicit;
- no UI surface implies hosted SaaS or external validation;
- service/API reject ambiguous cross-cell operations.

**Commit:**

```bash
git add src/shyftr/server.py src/shyftr/console_api.py apps/console/src tests/test_server.py tests/test_console_api.py
git commit -m "feat: expose multi-cell review surfaces locally"
```

---

## Tranche 6.7: docs, examples, and public-safe demo

**Objective:** Add public-safe synthetic docs/examples that prove Phase 6 behavior without real data or private-core leakage.

**Files:**

- Create: `docs/status/phase-6-multi-cell-closeout-evidence.md`
- Create: `docs/multi-cell-example.md`
- Create: `examples/multi-cell/`
- Create: `tests/test_multi_cell_demo.py`
- Modify: `README.md` only if claims remain exact and evidence-backed
- Modify: `docs/status/current-implementation-status.md`

**Example scenario:**

- `project-alpha` cell has approved local memories about a synthetic workflow.
- `project-beta` cell has similar approved local memories.
- registry tracks both cells and their trust boundaries.
- resonance finds a repeated pattern across both cells.
- rule proposal is created but not approved automatically.
- operator approves a scoped rule.
- pack for allowed scope includes the approved rule.
- export/import demonstrates imported trust label and review before use.

**Test-first tasks:**

1. Add `test_multi_cell_demo_runs_end_to_end`.
2. Add `test_multi_cell_demo_requires_explicit_cross_cell_scope`.
3. Add `test_multi_cell_demo_import_requires_review`.
4. Add `test_multi_cell_demo_pack_excludes_unreviewed_imports`.

**Implementation tasks:**

1. Create synthetic fixture cells under `examples/multi-cell/`.
2. Add demo script or documented CLI sequence.
3. Add closeout evidence doc with exact commands and expected output.
4. Update current implementation status to mark distributed multi-cell intelligence as implemented/qualified only after gates pass.
5. Avoid external-alpha/stable-release language.

**Gate:**

```bash
python -m pytest tests/test_multi_cell_demo.py -q
python -m pytest -q
python scripts/public_readiness_check.py
python scripts/terminology_inventory.py --fail-on-public-stale
python scripts/terminology_inventory.py --fail-on-capitalized-prose
git diff --check
bash scripts/alpha_gate.sh
```

**Acceptance criteria:**

- public-safe demo proves registry, resonance, rule review, and federation review;
- docs explain explicit cross-cell scope and no silent local truth mutation;
- status docs accurately qualify Phase 6 as local-first controlled-pilot behavior;
- alpha gate remains ready.

**Commit:**

```bash
git add docs/status/phase-6-multi-cell-closeout-evidence.md docs/multi-cell-example.md docs/status/current-implementation-status.md examples/multi-cell tests/test_multi_cell_demo.py README.md
git commit -m "docs: add phase 6 multi-cell evidence"
```

---

## Phase 6 closeout gate

Run after all Phase 6 tranches land:

```bash
git fetch origin main
git status --short --branch
test "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)"
python -m pytest tests/test_cell_registry.py tests/test_resonance.py tests/test_resonance_registry.py tests/test_cross_cell_rule_workflow.py tests/test_cell_federation_export.py tests/test_cell_federation_import.py tests/test_multi_cell_demo.py -q
python -m pytest tests/test_console_api.py tests/test_server.py tests/test_pack.py tests/test_policy.py tests/test_privacy_sensitivity.py -q
python -m pytest -q
cd apps/console && npm run build && npm audit --omit=dev
cd ../..
python scripts/public_readiness_check.py
python scripts/terminology_inventory.py --fail-on-public-stale
python scripts/terminology_inventory.py --fail-on-capitalized-prose
git diff --check
bash scripts/alpha_gate.sh
```

Then push and verify exact-SHA GitHub CI:

```bash
git push origin main
git fetch origin main
test "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)"
gh run list --repo stefan-mcf/shyftr --commit "$(git rev-parse HEAD)" --limit 10
```

Closeout evidence must record:

- exact SHA;
- local gate results;
- GitHub CI URL and conclusion;
- files/tranches completed;
- remaining deferred external tester evidence, if still deferred;
- explicit statement that Phase 7 was not started.

## Stop boundary after Phase 6

Stop after Phase 6 closeout. Do not start Phase 7 from this plan.

Phase 7 includes private-core-adjacent differentiators such as richer confidence modeling, causal memory graph, simulation sandbox, and advanced adaptation. Those need a separate public/private boundary decision before implementation.

## Final review checklist

- [ ] Registry is explicit and append-only/event-sourced.
- [ ] Cross-cell reads require explicit scope.
- [ ] Resonance is read-only and provenance-rich.
- [ ] Rule proposals are review-gated and scoped.
- [ ] Imports begin as non-local trust labels.
- [ ] Federation is selective and auditable.
- [ ] Default pack/search behavior remains single-cell.
- [ ] Source ledgers are not silently mutated.
- [ ] Public docs do not claim external validation unless reports exist.
- [ ] Public docs do not expose private paths, private data, or private-core strategy.
- [ ] Phase 7 is not started.
