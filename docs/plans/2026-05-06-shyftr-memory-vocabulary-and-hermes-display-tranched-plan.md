# ShyftR Memory Vocabulary and Hermes Display Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Make current ShyftR memory vocabulary the only user-facing/output vocabulary, show the Hermes tool activity as `ShyftR`, and keep older memory identifier wording only as hidden compatibility reads until a separately approved migration removes it.

**Architecture:** Add explicit terminology gates before code changes, then modernize ShyftR serializers/CLI/API/UI and the Hermes ShyftR plugin display/output layer. Preserve ledger read compatibility behind internal aliases while guaranteeing new writes, public docs, tool output, CLI output, API responses, and console UI use canonical `memory` / `memory_id` wording.

**Tech Stack:** Python 3.11, pytest, ShyftR JSONL ledgers, SQLite/FTS projections, FastAPI adapter surfaces, React console, Hermes plugin tool registry/display layer.

**Human Input Requirement:** None for Tranches 0-8. Final Tranche 9 is human-gated only if the operator wants destructive removal of older compatibility readers or migration of existing local/private cells. Do not remove compatibility readers before that final gate.

---

## Non-negotiable terminology policy

1. New public/user-facing wording must use:
   - `memory`
   - `memory_id`
   - `memory record`
   - `ledger entry`
   - `ShyftR`
2. Older memory identifier wording is forbidden in:
   - new ShyftR public docs except the compatibility table;
   - CLI output;
   - server/API response primary fields;
   - React console labels;
   - Hermes tool activity labels;
   - Hermes ShyftR plugin user-facing results;
   - newly written ShyftR ledgers unless an explicit compatibility-export mode is later approved.
3. Older memory identifier wording may remain only in:
   - compatibility deserializers/readers;
   - tests that prove old cells can still be read;
   - migration fixtures;
   - one public compatibility document section that marks the terms deprecated;
   - comments whose purpose is compatibility explanation.
4. Any user-facing output that must expose an existing internal id must expose it as `memory_id`. If the backing ledger still stores an older internal field, map it at the boundary.
5. Hermes activity display should render `ShyftR`, not the raw tool function name. Keep raw function identifiers stable until alias coverage and tests prove migration safety.

---

## Tranche 0: Baseline audit and scope ledger

**Objective:** Produce a machine-readable inventory of every remaining older memory identifier occurrence, classified as user-facing, compatibility-read, fixture/test, docs-compatibility, or generated/vendor.

**Stop boundary:** Do not edit code yet. This tranche only creates audit tooling/output.

**Files:**
- Create: `scripts/audit_memory_vocabulary.py`
- Create: `docs/status/memory-vocabulary-modernization-ledger.md`
- Read: `docs/concepts/terminology-compatibility.md`
- Read: `scripts/terminology_inventory.py`

**Steps:**
1. Create `scripts/audit_memory_vocabulary.py`.
2. Make it scan tracked text files only, excluding generated/vendor paths:
   - `.git/`
   - `node_modules/`
   - `apps/console/package-lock.json`
   - build/dist/cache outputs
3. Detect forbidden older memory identifier tokens and legacy field names.
4. Classify each match by path and context:
   - `must_fix_user_facing`
   - `allowed_compatibility_reader`
   - `allowed_compatibility_test`
   - `allowed_compatibility_doc`
   - `generated_or_vendor_skip`
5. Write a markdown ledger at `docs/status/memory-vocabulary-modernization-ledger.md` with counts, file list, and tranche assignment.
6. Ensure the script exits non-zero only when `--fail-on-user-facing` is passed and unapproved user-facing matches remain.

**Verification:**
```bash
cd <repo-root>
python scripts/audit_memory_vocabulary.py
python scripts/audit_memory_vocabulary.py --fail-on-user-facing || true
```

**Expected evidence:**
- Ledger exists.
- Every match is classified.
- User-facing matches are explicitly listed for later tranches.

---

## Tranche 1: Guardrail tests for no user-facing older memory wording

**Objective:** Add failing tests that enforce canonical memory vocabulary before implementation starts.

**Stop boundary:** Tests may fail at this tranche; do not change production code yet.

**Files:**
- Create: `tests/test_memory_vocabulary_guard.py`
- Modify: `scripts/audit_memory_vocabulary.py`

**Steps:**
1. Add pytest coverage that imports and runs the audit classifier.
2. Assert no `must_fix_user_facing` matches exist after implementation.
3. Add allowlists only for:
   - `docs/concepts/terminology-compatibility.md` deprecated alias table;
   - compatibility reader tests/fixtures;
   - internal deserializer branches.
4. Add a focused test for serializer output shape using existing public APIs/fixtures:
   - promoted memory returns `memory_id`;
   - no older memory identifier primary field appears in the returned user-facing dict.
5. Add a focused test for CLI/help text if the current CLI exposes memory records.

**Verification:**
```bash
cd <repo-root>
PYTHONPATH=src python -m pytest -q tests/test_memory_vocabulary_guard.py
```

**Expected evidence:**
- Tests exist.
- At least one guard fails before implementation if user-facing older wording remains.

---

## Tranche 2: Canonical id mapping layer

**Objective:** Centralize id normalization so user-facing code can request `memory_id` regardless of legacy storage fields.

**Stop boundary:** Do not remove older readers. Only add mapping helpers and tests.

**Files:**
- Modify: `src/shyftr/models.py`
- Modify or create: `src/shyftr/compat.py` if an existing compatibility module is preferable
- Test: `tests/test_models.py`
- Test: `tests/test_memory_vocabulary_guard.py`

**Steps:**
1. Add a helper such as:
   - `canonical_memory_id(record: Mapping[str, Any]) -> str | None`
   - `with_canonical_memory_id(record: Mapping[str, Any]) -> dict[str, Any]`
2. Helper behavior:
   - prefer `memory_id` when present;
   - read older stored id fields only as fallback;
   - emit `memory_id` in returned dict;
   - omit older id fields by default unless `include_compat=True` is explicitly passed.
3. Update existing model serializers to call the helper where memory records leave core storage.
4. Add tests for:
   - canonical-only input;
   - older-field-only input;
   - both fields present, canonical wins;
   - `include_compat=False` strips older id names from public dicts;
   - `include_compat=True` is internal-only and explicitly tested.

**Verification:**
```bash
cd <repo-root>
PYTHONPATH=src python -m pytest -q tests/test_models.py tests/test_memory_vocabulary_guard.py
```

**Expected evidence:**
- Public serializer helpers always emit `memory_id`.
- Compatibility reads still pass.

---

## Tranche 3: ShyftR CLI/API/pack/provider output modernization

**Objective:** Ensure ShyftR runtime outputs use `memory_id` and canonical memory wording.

**Stop boundary:** Keep input compatibility. Do not migrate existing ledgers yet.

**Files likely to modify after Tranche 0 audit confirms exact lines:**
- `src/shyftr/cli.py`
- `src/shyftr/promote.py`
- `src/shyftr/profile.py`
- `src/shyftr/pack.py`
- `src/shyftr/provider/memory.py`
- `src/shyftr/provider/trusted.py`
- `src/shyftr/console_api.py`
- `src/shyftr/server.py`
- `src/shyftr/integrations/pack_api.py`
- `src/shyftr/integrations/feedback_api.py`
- Tests: `tests/test_cli.py`, `tests/test_pack.py`, `tests/test_pack_api.py`, `tests/test_memory_provider.py`, `tests/test_server.py`, `tests/test_console_api.py`

**Steps:**
1. Read the Tranche 0 ledger and patch only files classified as user-facing output.
2. Replace primary output keys with `memory_id`.
3. Replace CLI/output prose with `memory`, `memory record`, or `memory id`.
4. Ensure provider pack/profile payloads do not expose older id names except in explicitly internal compatibility payloads.
5. Add regression tests that serialize representative CLI/API/provider results and assert:
   - `memory_id` exists where an id is needed;
   - older id field names do not exist in user-facing payloads;
   - old stored fields still deserialize.

**Verification:**
```bash
cd <repo-root>
PYTHONPATH=src python -m pytest -q \
  tests/test_cli.py \
  tests/test_pack.py \
  tests/test_pack_api.py \
  tests/test_memory_provider.py \
  tests/test_server.py \
  tests/test_console_api.py \
  tests/test_memory_vocabulary_guard.py
```

**Expected evidence:**
- All public output tests pass.
- Guard no longer reports ShyftR runtime user-facing older memory wording.

---

## Tranche 4: React console and local UI labels

**Objective:** Ensure the local console displays current memory vocabulary only.

**Stop boundary:** Do not change API behavior in this tranche except to consume canonical fields from prior tranches.

**Files likely to modify after audit confirms exact lines:**
- `apps/console/src/main.tsx`
- Additional `apps/console/src/**` files if discovered by audit
- Tests/build config as available

**Steps:**
1. Search `apps/console/src` for older memory identifier labels and fields.
2. Replace UI labels with `Memory`, `Memory id`, or `Memory record`.
3. Update client parsing to prefer `memory_id`.
4. Keep fallback parsing internal if older API fixtures still exist.
5. Run console build or the narrowest available frontend check.

**Verification:**
```bash
cd <repo-root>
python scripts/audit_memory_vocabulary.py --fail-on-user-facing
npm --prefix apps/console run build
```

**Expected evidence:**
- Console source has no user-facing older memory wording.
- Build passes.

---

## Tranche 5: Hermes ShyftR plugin display/output polish

**Objective:** Make Hermes show `ShyftR` in tool activity while preserving raw tool compatibility, and make ShyftR plugin results expose `memory_id` as primary output.

**Stop boundary:** Do not rename/remove the raw Hermes tool function without an alias and tests. No global Hermes config mutation.

**Files:**
- Modify canonical local plugin source if present: `<local-hermes-root>/plugins/shyftr/__init__.py`
- Inspect/patch symlinked profile plugin copies only if they are not symlinks:
  - `<local-hermes-root>/profiles/antaeus-terminal/plugins/shyftr/__init__.py`
  - `<local-hermes-root>/profiles/antaeus-terminal-side/plugins/shyftr/__init__.py`
  - `<local-hermes-root>/profiles/eva/plugins/shyftr/__init__.py`
- Modify Hermes display code only if necessary after inspection:
  - `<local-hermes-root>/hermes-agent/agent/display.py`
  - `<local-hermes-root>/hermes-agent/cli.py`
  - `<local-hermes-root>/hermes-agent/tools/registry.py`
- Add or modify tests in Hermes checkout if display-label mapping belongs in core.

**Steps:**
1. Inspect plugin registration and Hermes display rendering to find where raw tool names are converted into activity labels.
2. Prefer a display-label map over raw tool renaming:
   - raw function remains stable for compatibility;
   - display label is `ShyftR`.
3. Add a schema/display metadata field if Hermes supports one, for example `display_name: ShyftR`; otherwise add a central map in the display layer.
4. Update plugin `remember` action result to return `memory_id` as the primary id field.
5. If compatibility requires the old internal id in result JSON, expose it only as `legacy_internal_id` or omit it from normal success output. Prefer omission unless a current caller breaks.
6. Add smoke test or script proving:
   - action `remember` returns `memory_id`;
   - action `search` returns `memory_id` for each result when ids are included;
   - activity display resolves raw function name to `ShyftR`.
7. Do not edit `~/.hermes/config.yaml` or start/stop gateways in this tranche.

**Verification:**
```bash
cd <local-hermes-root>/hermes-agent
python -m pytest -q tests/tools tests/agent -k 'shyftr or display or tool' || true
python - <<'PY'
# Import/plugin smoke should be adapted to the final plugin API.
# Expected: printed JSON uses memory_id as primary id and display metadata is ShyftR.
PY
```

**Expected evidence:**
- Hermes activity label can render as `ShyftR`.
- Raw compatibility name remains callable.
- Plugin result JSON no longer uses older memory id wording as primary output.

---

## Tranche 6: Public docs and status cleanup

**Objective:** Update ShyftR public docs so current wording is primary and older memory terms appear only in the compatibility section.

**Stop boundary:** Do not delete compatibility documentation.

**Files likely to modify:**
- `README.md`
- `docs/status/current-implementation-status.md`
- `docs/status/alpha-readiness.md`
- `docs/concepts/terminology-compatibility.md`
- `docs/concepts/storage-retrieval-learning.md`
- Any public docs flagged by Tranche 0 as user-facing

**Steps:**
1. Read Tranche 0 ledger for docs flagged as user-facing.
2. Replace old memory terminology in public docs with canonical memory wording.
3. In `docs/concepts/terminology-compatibility.md`, keep exactly one compatibility table entry for older names, clearly marked deprecated/read-only compatibility.
4. Update `docs/status/current-implementation-status.md` caveats so they say compatibility readers exist, but public outputs/write paths use `memory_id`.
5. Run public terminology checks.

**Verification:**
```bash
cd <repo-root>
python scripts/terminology_inventory.py --fail-on-public-stale
python scripts/terminology_inventory.py --fail-on-capitalized-prose
python scripts/public_readiness_check.py
python scripts/audit_memory_vocabulary.py --fail-on-user-facing
```

**Expected evidence:**
- Public docs pass terminology guards.
- Only compatibility doc/table contains deprecated memory identifier wording.

---

## Tranche 7: Full ShyftR regression and alpha gate

**Objective:** Prove the modernization did not break ShyftR public alpha behavior.

**Stop boundary:** No new features. Only fixes required by failed verification.

**Files:**
- No planned files unless tests fail.

**Steps:**
1. Run full Python test suite.
2. Run terminology inventory.
3. Run public readiness check.
4. Run alpha gate.
5. Update `docs/status/memory-vocabulary-modernization-ledger.md` with final counts, commands, and outcomes.

**Verification:**
```bash
cd <repo-root>
PYTHONPATH=src python -m pytest -q
python scripts/terminology_inventory.py --fail-on-public-stale
python scripts/terminology_inventory.py --fail-on-capitalized-prose
python scripts/public_readiness_check.py
bash scripts/alpha_gate.sh
python scripts/audit_memory_vocabulary.py --fail-on-user-facing
```

**Expected evidence:**
- Full tests pass.
- Public readiness passes.
- Alpha gate prints `ALPHA_GATE_READY`.
- Audit reports zero unapproved user-facing older memory terminology.

---

## Tranche 8: Hermes runtime smoke and profile-safe verification

**Objective:** Verify the Hermes-side polish works in an isolated/profile-safe way without mutating real runtime state unexpectedly.

**Stop boundary:** Do not restart production gateways. Do not write to real user memory except with a disposable smoke marker that is immediately deprecated/removed through supported tooling if available.

**Files:**
- Create if useful: `<local-hermes-root>/scripts/smoke_shyftr_display_and_memory_id.py`
- Read: `<local-hermes-root>/plugins/shyftr/__init__.py`
- Read: active profile `shyftr.json` files

**Steps:**
1. Use a temporary Hermes profile or direct plugin invocation where possible.
2. Call ShyftR status/search against a known harmless query.
3. If a write smoke is necessary, write a disposable memory with a unique marker and then immediately supersede/deprecate it using the supported ledger/status event path.
4. Capture evidence that visible/display label is `ShyftR`.
5. Capture evidence that result payload uses `memory_id` as primary id.
6. Record commands and output snippets in a local evidence note outside public ShyftR if they include local profile paths.

**Verification:**
```bash
python <local-hermes-root>/scripts/smoke_shyftr_display_and_memory_id.py
```

**Expected evidence:**
- Display label is `ShyftR`.
- Result payload primary id is `memory_id`.
- No lasting disposable memory remains active unless intentionally retained as a test marker.

---

## Tranche 9: Final human-gated destructive migration decision

**Objective:** Decide whether to remove compatibility readers and migrate existing cells, or keep them indefinitely as hidden compatibility.

**Human gate:** Required. Stop here unless the operator explicitly approves one of the options below.

**Decision recorded 2026-05-06:** Option A selected. Keep hidden compatibility readers indefinitely. No destructive migration, local/private cell rewrite, or compatibility reader removal is approved by this tranche.

**Option A: Keep hidden compatibility readers**
- Recommended default.
- No destructive migration.
- Public/user-facing outputs remain canonical.
- Existing cells remain readable.

**Option B: Migrate local/private cells**
- Requires backup first.
- Requires ledger verification before and after.
- Requires a reversible migration script.
- Requires operator approval of target cell paths.

**Option C: Remove compatibility readers**
- Highest risk.
- Requires public release note, migration tool, fixture coverage, and explicit approval.
- Not recommended until operator review confirms compatibility can be safely narrowed.

**Verification for any approved destructive option:**
```bash
cd <repo-root>
shyftr backup --cell <approved-cell-path> --out <approved-backup-path>
shyftr verify-ledger <approved-cell-path>
PYTHONPATH=src python -m pytest -q
bash scripts/alpha_gate.sh
```

**Expected evidence:**
- Human approval recorded in a local/private status note.
- Backup exists before migration.
- Verification passes after migration.

---

## Completion checklist

- [x] Audit script exists and classifies all older memory vocabulary occurrences.
- [x] Tests enforce no user-facing older memory identifier wording.
- [x] ShyftR public/runtime outputs use `memory_id`.
- [x] Hermes visible activity label uses `ShyftR`.
- [x] Raw Hermes tool compatibility is preserved until alias migration is proven.
- [x] Public docs use current vocabulary, with older terms only in compatibility documentation.
- [x] Full ShyftR tests pass.
- [x] Public readiness passes.
- [x] Alpha gate passes.
- [x] Hermes smoke verifies display and payload wording.
- [x] Destructive compatibility removal is closed as Option A: keep hidden compatibility readers indefinitely.
