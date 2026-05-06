# Phase 8 Readiness Reconnaissance — File-Backed Recommendations

Date: 2026-05-06 | Repo: public ShyftR checkout | Mode: pre-implementation reconnaissance

## 1. Executive Summary

The repo is in strong shape for controlled-pilot alpha. Phase 7 and 7.8 (regulated autonomous memory evolution) are implemented as public-safe foundations. Phase 8 productisation had not been started before this reconnaissance. The codebase has substantial infrastructure (adapters, API, console, tests, docs) but has concrete, surgically-targeted gaps in landing docs, versioned API, adapter examples, desktop shell, and external tester evidence.

**Key finding:** Phase 8 can begin safely from current `main` (SHA 0f53948). The gaps are additive documentation and surface-level API/package work — they do NOT require core refactoring.

---

## 2. Tranche-by-Tranche Readiness Assessment

### 2.1 Tranche 8.1: Product Landing Docs

**Plan requirement:** 10 docs (Why ShyftR, Architecture, Quickstart, Concepts, CLI guide, HTTP API guide, Frontend guide, Integration guide, Safety model, Roadmap)

| # | Doc | Status | Existing material |
|---|-----|--------|-------------------|
| 1 | Why ShyftR | **MISSING** | README "Why it matters" (lines 33-44) is good but brief. `docs/concepts/differentiation-and-positioning.md` covers positioning but not end-user "why." |
| 2 | Architecture | **PARTIAL** | README "Architecture" (lines 208-260) diagrams cells/ledger/regulator/grid. No standalone `docs/architecture.md`. |
| 3 | Quickstart | **PARTIAL** | README "Quickstart" (lines 141-176) and `docs/example-lifecycle.md` exist. No standalone quickstart doc. |
| 4 | Concepts | **EXISTS** | `docs/concepts/` has 14 well-written files: cells, storage-retrieval-learning, runtime-integration-contract, differentiation, implementation-guardrails, memory-provider-contract, terminology-compatibility, etc. |
| 5 | CLI guide | **MISSING** | No standalone CLI reference. CLI surface is documented inline in `src/shyftr/cli.py` (1488 lines, comprehensive subcommands). |
| 6 | HTTP API guide | **EXISTS** | `docs/api.md` covers all endpoints with safety boundaries. |
| 7 | Frontend guide | **EXISTS** | `docs/console.md` covers React console setup and capabilities. |
| 8 | Integration guide | **EXISTS** | `docs/concepts/runtime-integration-contract.md` (326 lines, thorough). `docs/runtime-integration-example.md` exists. |
| 9 | Safety model | **PARTIAL** | README "Safety model" (lines 278-315), `SECURITY.md`, `docs/status/alpha-readiness.md` exist. No consolidated `docs/safety-model.md`. |
| 10 | Roadmap | **MISSING** | No roadmap file. `docs/status/tranched-plan-status.md` is plan reconciliation, not a user-facing roadmap. |

**Gap severity:** LOW. Most content already exists scattered across README and docs/. The work is consolidation and formatting, not research or new content.

**Safe implementation targets (files to CREATE):**
- `docs/why-shyftr.md` — extract/expand from README lines 33-56 and `docs/concepts/differentiation-and-positioning.md`
- `docs/architecture.md` — extract/expand from README lines 208-260 and `docs/concepts/cells.md`
- `docs/quickstart.md` — consolidate README lines 141-176 + `docs/example-lifecycle.md`
- `docs/cli-guide.md` — reference-driven from `src/shyftr/cli.py` docstrings (1488 lines of subcommand documentation)
- `docs/safety-model.md` — consolidate README lines 278-315 + `SECURITY.md` + `docs/status/alpha-readiness.md`
- `docs/roadmap.md` — extract from `docs/plans/2026-04-24-shyftr-implementation-tranches.md` + `docs/status/tranched-plan-status.md`

**Tests to add:** None required (docs-only).

**Public/private risk:** LOW. All input material is already public. Consolidation involves no new claims.

---

### 2.2 Tranche 8.2: Plugin/Adapter SDK

**Plan requirement:** Define adapter interface, add template adapter, add adapter test harness, add docs, add examples (markdown folder, JSONL runtime logs, GitHub issue export, chat transcript export).

| Item | Status | Existing material |
|------|--------|-------------------|
| Adapter interface | **EXISTS** | `src/shyftr/integrations/protocols.py` — `InputAdapter` and `OutcomeAdapter` protocols (210 lines), `ExternalInputRef`, `InputPayload` dataclasses. |
| Template adapter | **EXISTS** | `src/shyftr/integrations/file_adapter.py` — `FileInputAdapter` class (627 lines) implementing the full `InputAdapter` protocol with file/glob/jsonl/directory discovery. |
| Adapter config model | **EXISTS** | `src/shyftr/integrations/config.py` — `RuntimeAdapterConfig`, `InputDefinition` (415 lines). |
| Plugin discovery | **EXISTS** | `src/shyftr/integrations/plugins.py` — `AdapterPluginMeta`, entry-point group `shyftr.adapters` (195 lines). Registered in `pyproject.toml` line 35-36. |
| Adapter test harness | **EXISTS** | `tests/test_file_adapter.py`, `tests/test_integration_config.py`, `tests/test_integration_protocols.py`, `tests/test_integration_plugins.py`, `tests/test_runtime_integration_demo.py`, `tests/test_sync_state.py` |
| Adapter docs | **EXISTS** | `docs/concepts/runtime-integration-contract.md`, adapter YAML examples in `examples/integrations/` |
| Markdown folder example | **MISSING** | No standalone adapter example for a markdown folder |
| JSONL runtime logs example | **PARTIAL** | `examples/integrations/worker-runtime/feedback-log.jsonl` exists (1 row). No full JSONL runtime log example. |
| GitHub issue export example | **MISSING** | No GitHub-issues-to-ShyftR adapter example |
| Chat transcript export example | **MISSING** | No chat-transcript-to-ShyftR adapter example |

**Gap severity:** LOW-MEDIUM. Core adapter infrastructure is mature. Missing items are example YAML configs and synthetic fixture data.

**Safe implementation targets (files to CREATE):**
- `examples/integrations/markdown-folder/adapter.yaml` — adapter config pointing at a directory of .md files
- `examples/integrations/markdown-folder/example-note.md` — synthetic markdown note fixture
- `examples/integrations/jsonl-runtime-logs/adapter.yaml` — adapter config for JSONL runtime log ingestion
- `examples/integrations/jsonl-runtime-logs/runtime-logs.jsonl` — synthetic multi-line JSONL fixture
- `examples/integrations/github-issue-export/adapter.yaml` — adapter config for GitHub issue JSON export
- `examples/integrations/github-issue-export/issues.json` — synthetic GitHub issues fixture
- `examples/integrations/chat-transcript/adapter.yaml` — adapter config for chat transcript export
- `examples/integrations/chat-transcript/transcript.jsonl` — synthetic chat transcript fixture

**Files to EDIT (minor):**
- `examples/README.md` — add rows for new adapter examples in the table

**Tests to add:**
- `tests/test_adapter_examples.py` — validate that each new example adapter config loads and passes `validate_config()`

**Public/private risk:** LOW. All examples are synthetic. No real data.

---

### 2.3 Tranche 8.3: Versioned Public API

**Plan requirement:** Add `/v1/` API namespace, freeze v1 schemas, generate OpenAPI spec, add API contract tests, add deprecation policy.

| Item | Status | Existing material |
|------|--------|-------------------|
| `/v1/` namespace | **MISSING** | All endpoints are unversioned: `/health`, `/validate`, `/ingest`, `/pack`, `/feedback` compatibility route, `/frontier`, `/cells`, `/cell/{id}/...`, etc. in `src/shyftr/server.py`. |
| Frozen v1 schemas | **MISSING** | Request/response shapes are defined in code but not frozen as versioned OpenAPI schemas. |
| OpenAPI spec | **MISSING** | No OpenAPI generation. FastAPI can auto-generate but it's not wired up. |
| API contract tests | **MISSING** | `tests/test_server.py` tests endpoint behavior but does not validate against a frozen schema. |
| Deprecation policy | **MISSING** | No deprecation policy document. |

**Gap severity:** MEDIUM. This is the highest-impact Phase 8 gap. External runtimes cannot depend on a stable `/v1/` contract today.

**Safe implementation targets (files to EDIT):**
- `src/shyftr/server.py` — add `/v1/` route prefix via sub-application mount:
  - Create `v1_app = FastAPI(title="ShyftR API v1", version="1.0.0")` in `_get_app()`
  - Register all current routes on `v1_app`
  - Mount via `app.mount("/v1", v1_app)`
  - Keep unversioned routes for transitional backward compat
- `src/shyftr/server.py` — OpenAPI JSON at `/v1/openapi.json` (FastAPI auto-generates)
- `src/shyftr/server.py` — add GET `/openapi.json` that redirects or serves v1 spec
- `docs/api.md` — add `/v1/` endpoint table and deprecation policy link

**Files to CREATE:**
- `docs/api-deprecation-policy.md` — policy: v1 is stable, breaking changes require v2, v0/unversioned is transitional, deprecated endpoints get 6-month notice
- `tests/test_api_contract.py` — contract tests that validate `/v1/` endpoints return shapes matching frozen JSON schemas

**Tests to add:**
- `tests/test_api_contract.py` — validate `/v1/openapi.json` returns valid OpenAPI 3.x
- `tests/test_api_contract.py` — validate each `/v1/` endpoint against a frozen response schema
- `tests/test_api_contract.py` — validate unversioned routes still work (backward compat smoke)
- `tests/test_server.py` (extend) — add `/v1/` variants of existing endpoint tests

**Public/private risk:** LOW. Adding `/v1/` is additive. Existing unversioned routes preserved. No core logic changes.

---

### 2.4 Tranche 8.4: Desktop Shell

**Plan requirement:** Tauri wrapper, start/stop local ShyftR service, select cell directory, open console, local logs, bundle install docs.

| Item | Status | Existing material |
|------|--------|-------------------|
| Tauri wrapper | **MISSING** | No Tauri project. Console is a standalone Vite/React app at `apps/console/`. |
| Start/stop service | **MISSING** | Server start is `shyftr serve` or `python -m shyftr.server`. Tauri would spawn/manage this process. |
| Select cell directory | **MISSING** | Console uses `VITE_SHYFTR_CELL_ROOT` env var or query param. Tauri needs native directory picker. |
| Open console | **MISSING** | Console is a web app. Tauri would embed it in a webview. |
| Local logs | **MISSING** | No log viewer. Server logs go to stdout via uvicorn. |
| Bundle install docs | **MISSING** | No desktop install documentation. |

**Gap severity:** HIGH (effort). This is a significant new project. Plan line 2097: "Use Tauri only after web console is stable" — web console IS stable (`npm run build` succeeds, `apps/console/dist/` exists).

**Prerequisite verification:**
- Console builds: `apps/console/dist/index.html` + bundled JS/CSS exist
- Console API client: `apps/console/src/api.ts` (66 lines) consuming local service
- Console is developer preview per `docs/console.md`

**Safe implementation targets — new `apps/desktop/` directory:**
- `apps/desktop/package.json` — Tauri + Vite configuration
- `apps/desktop/src-tauri/Cargo.toml` — Rust dependencies
- `apps/desktop/src-tauri/tauri.conf.json` — window config, process commands
- `apps/desktop/src-tauri/src/main.rs` — spawn `shyftr serve`, directory picker, log capture
- `apps/desktop/src/` — React/Vite frontend (reuses console components)
- `apps/desktop/README.md` — build and install instructions
- `docs/desktop.md` — desktop shell documentation

**Files to EDIT (minor):**
- `README.md` — add desktop shell mention under local service section
- `docs/development.md` — add Tauri prerequisites (Rust, `cargo`, system deps)

**Tests to add:**
- `tests/test_server.py` already covers server start/stop. Tauri-specific tests would need the Rust toolchain; scope as manual smoke test.

**Public/private risk:** MEDIUM. Tauri adds Rust toolchain. Desktop shell is explicitly optional (plan: "Desktop app does not replace API/CLI", "Web console remains portable").

**Recommendation:** Defer 8.4 until after 8.1-8.3. Console is already usable as a web app.

---

### 2.5 Tranche 8.5: Public Alpha

**Plan requirement:** CI green, docs complete, demo works, backup/restore works, UI usable, local API stable, at least one real runtime integration proven, clear warning: local-first alpha.

| Item | Status | Evidence |
|------|--------|----------|
| CI green | **EXISTS** | CI badge in README links to GitHub Actions. |
| Docs complete | **PARTIAL** | See 8.1 gaps above. |
| Demo works | **EXISTS** | `examples/run-local-lifecycle.sh`, `docs/example-lifecycle.md` |
| Backup/restore works | **EXISTS** | `src/shyftr/backup.py`, `tests/test_backup_restore.py` |
| UI usable | **EXISTS** | Console builds, `docs/console.md` |
| Local API stable | **NEEDS 8.3** | API works but is unversioned. |
| Real runtime integration | **MISSING** | Only synthetic examples. Plan line 2127: "At least one real runtime integration proven." |
| Clear alpha warning | **EXISTS** | README explicit: "local-first alpha", "controlled-pilot developer preview", `docs/status/alpha-readiness.md` |

**Gap severity:** MEDIUM. Major gap is real runtime integration evidence. `docs/status/tranched-plan-status.md` acknowledges: "prove at least one real or replayable pilot loop before closing 8.5."

**Safe implementation targets:**
- No new files needed directly — 8.5 is a gate/evaluation tranche.
- Runtime pilot proof is the critical blocker. Options:
  - Run existing file/JSONL adapter as replayable pilot harness
  - Capture evidence in `docs/status/` without private data
  - Or mark 8.5 partial and scope alpha wave to clone/install/synthetic-demo only

**Tests to add:** None new. Existing suite must stay green.

**Public/private risk:** LOW for the tranche. External tester evidence must NOT include private/customer/production data (per Wave 1 scope in `docs/status/tranched-plan-status.md`).

---

## 3. Summary of Concrete Edits

### 3.1 Files to CREATE (17 new files)

| # | File | Tranche | Content |
|---|------|---------|---------|
| 1 | `docs/why-shyftr.md` | 8.1 | End-user "why" doc |
| 2 | `docs/architecture.md` | 8.1 | Architecture overview |
| 3 | `docs/quickstart.md` | 8.1 | Consolidated quickstart |
| 4 | `docs/cli-guide.md` | 8.1 | CLI reference |
| 5 | `docs/safety-model.md` | 8.1 | Consolidated safety model |
| 6 | `docs/roadmap.md` | 8.1 | User-facing roadmap |
| 7 | `docs/api-deprecation-policy.md` | 8.3 | API versioning/deprecation policy |
| 8 | `tests/test_api_contract.py` | 8.3 | Versioned API contract tests |
| 9 | `tests/test_adapter_examples.py` | 8.2 | Adapter example validation tests |
| 10 | `examples/integrations/markdown-folder/adapter.yaml` | 8.2 | Markdown folder adapter example |
| 11 | `examples/integrations/markdown-folder/example-note.md` | 8.2 | Synthetic markdown fixture |
| 12 | `examples/integrations/jsonl-runtime-logs/adapter.yaml` | 8.2 | JSONL runtime logs adapter |
| 13 | `examples/integrations/jsonl-runtime-logs/runtime-logs.jsonl` | 8.2 | Multi-line JSONL fixture |
| 14 | `examples/integrations/github-issue-export/adapter.yaml` | 8.2 | GitHub issue adapter example |
| 15 | `examples/integrations/github-issue-export/issues.json` | 8.2 | Synthetic GitHub issues fixture |
| 16 | `examples/integrations/chat-transcript/adapter.yaml` | 8.2 | Chat transcript adapter example |
| 17 | `examples/integrations/chat-transcript/transcript.jsonl` | 8.2 | Synthetic transcript fixture |

### 3.2 Files to EDIT (5 files)

| # | File | Tranche | Change |
|---|------|---------|--------|
| 1 | `src/shyftr/server.py` | 8.3 | Add `/v1/` sub-application mount, OpenAPI endpoint |
| 2 | `README.md` | 8.1 | Add links to new docs, desktop shell mention |
| 3 | `examples/README.md` | 8.2 | Add rows for new adapter examples |
| 4 | `docs/api.md` | 8.3 | Add `/v1/` endpoint table, deprecation policy link |
| 5 | `docs/development.md` | 8.4 | Add Tauri prerequisites (if desktop pursued) |

### 3.3 Tests to ADD (3 test files)

| # | File | Tests |
|---|------|-------|
| 1 | `tests/test_api_contract.py` | `/v1/openapi.json` valid, `/v1/*` endpoints match schemas, backward compat for unversioned routes |
| 2 | `tests/test_adapter_examples.py` | Each example YAML loads, validates config, discovers inputs |
| 3 | `tests/test_server.py` (extend existing) | Add `/v1/` variants of existing endpoint tests |

### 3.4 Tests to RUN (regression)

```bash
python -m pytest -q
bash examples/run-local-lifecycle.sh
python scripts/public_readiness_check.py
python scripts/terminology_inventory.py --fail-on-public-stale
bash scripts/alpha_gate.sh
git diff --check
```

### 3.5 Desktop Shell (separate project — 8.4)

If pursued, new directory structure:
```
apps/desktop/
  package.json
  src-tauri/
    Cargo.toml
    tauri.conf.json
    src/main.rs          # Window, process spawn, directory picker
  src/
    App.tsx              # Reuse console components
    index.html
  README.md
docs/desktop.md
```

**Recommendation:** Defer 8.4 until after 8.1-8.3 done. Console is already a usable web app; Tauri wrapping is packaging/UX improvement, not functional blocker.

---

## 4. Risk Review

### 4.1 Public-Facing Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Versioned API `/v1/` may change after freeze | LOW | Freeze only schemas already stable in tests. Mark newer evolution/frontier endpoints as `v1-experimental`. |
| New docs overclaim | LOW | Derive all claims from `docs/status/current-implementation-status.md` capability matrix. Present tense only for "implemented" rows. |
| Adapter examples look production-ready | LOW | Label all as "synthetic fixtures for demonstration." |
| Desktop shell implies SaaS product | LOW | Keep explicit "local-first only" language. |

### 4.2 Private-Core Separation Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Versioned API exposes private-core surfaces | LOW | Phase 7 private-core algorithms (scoring, ranking, compaction) already segregated. `/v1/` routes delegate to same public modules. |
| New docs reference private data | LOW | All new docs use synthetic examples and public paths. |
| Desktop shell captures real cell paths | LOW | Default to temp/synthetic cells. Add warning in desktop docs. |

### 4.3 Implementation Order Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| 8.3 `/v1/` could break unversioned routes | LOW | Sub-application mount means existing routes untouched. |
| 8.4 Tauri adds build complexity | MEDIUM | Keep as separate optional `apps/desktop/` dir. Do not make CI depend on Tauri build. |
| 8.5 external tester evidence blocked by missing docs | LOW | 8.1 docs can be written first to unblock 8.5. |

---

## 5. Recommended Implementation Order

1. **8.1 first** — landing docs are lowest-risk, highest-visibility. Docs-only. Unblocks 8.5 tester clarity.
2. **8.2 second** — adapter examples are self-contained in `examples/`. Add synthetic fixtures, validate they work.
3. **8.3 third** — versioned API is the most impactful code change. `/v1/` sub-app mount + contract tests.
4. **8.5 pre-flight** — run Wave 0 checks, then proceed to tester outreach.
5. **8.4 last** — desktop shell explicitly optional. Defer until after external tester feedback on web console.

---

## 6. Stop limit

Per task instructions: **stop before external tester evidence gate. Do not start Checkpoint E or Phase 9.**

Phase 8 implementation (tranches 8.1-8.4) can be executed. Phase 8.5's Wave 1-4 (external tester outreach, evidence collection) is the hard stop — documentation and code can be prepared but tester instructions should not be sent until explicitly approved.

Note: `docs/status/tranched-plan-status.md` line 31 says "do not begin Phase 8 from this planning update." That status doc may need updating before Phase 8 work begins.
