# ShyftR README public overhaul plan

> For Hermes: this is a planning artifact for a professional public-facing README rewrite. Do not publish packages, change repository visibility, tag releases, or claim general availability while executing this plan. Keep advanced commercial-core details private. Public README claims must stay evidence-backed by `docs/status/current-implementation-status.md`, tests, examples, and alpha-gate output.

Goal: turn `README.md` into a comprehensive public landing page that sells ShyftR's eventual product direction while staying honest about the current local-first alpha.

Public product stance: ShyftR is attachable recursive memory cells for AI agents. It gives agents memory that can prove where it came from, whether it helped, and how it changed over time.

Current release stance: local-first alpha / controlled-pilot developer preview. The supported public path is clone, install, run synthetic local examples, inspect the ledgers, run the alpha gate, and test with operator-approved non-sensitive data.

End-state README promise: a developer should understand in one pass:

- the problem ShyftR solves;
- why cells, ledgers, regulators, packs, feedback, confidence, patterns, and rules matter;
- what works today;
- what is planned or gated;
- how to install and run a deterministic local proof;
- how an external runtime integrates through evidence, packs, and feedback;
- how ShyftR keeps durable memory inspectable, review-gated, and local-first;
- how to verify the repository before trusting a clone.

Execution rule: write the README as public product documentation, not a private roadmap. Use current-tense claims only for implemented capabilities. Use future-facing or gated language for pattern/rule distillation breadth, multi-cell intelligence, hosted operation, commercial integrations, benchmarks, and advanced ranking logic.

---

## Research and audit evidence summary

Repository state inspected on 2026-05-06:

- Branch: `main...origin/main`.
- Remote: `https://github.com/stefan-mcf/shyftr.git`.
- GitHub visibility: public.
- GitHub description: `Attachable recursive memory cells for AI agents`.
- GitHub topics: `agentic-ai`, `ai-agents`, `memory`, `rag`, `vector-search`, `agent-memory`, `ai-memory`, `recursive-memory`.
- Current README length: 178 lines.
- Public readiness guard: `python scripts/public_readiness_check.py` returned `PASS` before this plan was written.
- Terminology guards: `python scripts/terminology_inventory.py --fail-on-public-stale` and `--fail-on-capitalized-prose` returned exit 0 before this plan was written.

Internal evidence used:

- `README.md` — current public landing page.
- `docs/status/current-implementation-status.md` — current capability matrix and public wording rule.
- `docs/status/alpha-readiness.md` — tester audience, alpha gate, data boundary.
- `docs/concepts/differentiation-and-positioning.md` — strongest positioning thesis and feedback-aware memory narrative.
- `docs/concepts/cells.md` — cell, regulator, ledger, grid, pack, feedback definitions.
- `docs/concepts/storage-retrieval-learning.md` — canonical truth, trust tiers, pack roles, confidence loop.
- `docs/concepts/runtime-integration-contract.md` and `docs/runtime-integration-example.md` — runtime-neutral adapter story.
- `docs/api.md`, `docs/console.md`, `docs/development.md`, `examples/README.md`, `examples/run-local-lifecycle.sh` — install, local service, console, and example evidence.
- `pyproject.toml` — Python version, alpha classifier, package metadata, optional extras.

External README/research patterns surveyed:

- `https://github.com/mem0ai/mem0` — fast developer hook, quickstart, memory category clarity.
- `https://github.com/getzep/zep` — long-term memory positioning, API-first docs, trust-building product framing.
- `https://github.com/letta-ai/letta` — memory-management architecture and agent-memory narrative.
- `https://github.com/SciPhi-AI/R2R` — developer-facing retrieval/context infrastructure information architecture.
- `https://github.com/getzep/graphiti` — temporal/entity memory framing and visual explanation pattern.
- `https://python.langchain.com/docs/concepts/memory/` — framework-level memory taxonomy developers may already understand.
- `https://docs.llamaindex.ai/en/stable/module_guides/deploying/agents/memory/` — agent memory API and quickstart expectations.
- `https://www.anthropic.com/news/contextual-retrieval` — context engineering framing around better retrieval context.

Research takeaway: strong public README pages sell the category quickly, show a runnable path immediately, make architecture visual, explain safety and data boundaries, provide synthetic examples, and make verification easy. ShyftR's opportunity is to lead with verifiable feedback-aware memory rather than presenting as another local storage or retrieval utility.

---

## Audit findings

- **F-01: opening hook undersells the product**
  - Severity: high
  - Evidence: `README.md` line 3 says `Local-first, append-only memory control plane for AI agents.`
  - Public impact: accurate, but abstract. It fails to communicate the stronger thesis that ShyftR evolves agent behavior through attachable memory cells, provenance, feedback, and confidence.
  - Required remediation: rewrite the hero section around attachable recursive memory cells, feedback-aware memory, and auditable learning.
  - Plan mapping: Tranche 1.

- **F-02: cell abstraction lacks first-class explanation**
  - Severity: high
  - Evidence: `README.md` mentions local cell creation and cell ledgers, while `docs/concepts/cells.md` defines the cell as the primary abstraction.
  - Public impact: readers can miss the central architecture: scoped, portable, attachable memory namespaces.
  - Required remediation: add a concise `Why cells` section near the top.
  - Plan mapping: Tranche 1, Tranche 3.

- **F-03: feedback-aware memory is present but not sold**
  - Severity: high
  - Evidence: `README.md` lists feedback recording, while `docs/concepts/differentiation-and-positioning.md` frames the pack -> feedback -> confidence loop as the core differentiator.
  - Public impact: the README reads like a lifecycle checklist rather than a self-improving agent-memory substrate.
  - Required remediation: add a direct differentiator section explaining packs as accountable experiments and feedback as learning.
  - Plan mapping: Tranche 1, Tranche 3.

- **F-04: canonical lifecycle is incomplete in the README**
  - Severity: medium
  - Evidence: `README.md` shows `evidence -> candidate -> memory -> pack -> feedback`; canonical lifecycle is `evidence -> candidate -> memory -> pattern -> rule` with application loop `pack -> feedback -> confidence`.
  - Public impact: the public landing page omits the recursive/distillation end state that makes ShyftR more than a local recall tool.
  - Required remediation: rewrite lifecycle diagrams and prose to separate durable promotion from application/feedback.
  - Plan mapping: Tranche 3.

- **F-05: no agent-learning narrative demo**
  - Severity: medium
  - Evidence: `README.md` quickstart is command-oriented. `docs/concepts/differentiation-and-positioning.md` contains a stronger story about agents learning from run outcomes.
  - Public impact: developers can run commands without understanding the product reason.
  - Required remediation: add a short narrative before or inside the quickstart: first run creates evidence, review promotes memory, next run receives a pack, feedback updates confidence.
  - Plan mapping: Tranche 2.

- **F-06: alternatives/category positioning is missing**
  - Severity: medium
  - Evidence: `README.md` has no category section explaining ShyftR relative to vector indexes, framework memory helpers, managed memory services, or RAG pipelines.
  - Public impact: readers cannot quickly place ShyftR in the AI memory landscape.
  - Required remediation: add a category-positioning table using broad categories rather than competitor callouts.
  - Plan mapping: Tranche 1.

- **F-07: trust tiers and pack roles are absent**
  - Severity: medium
  - Evidence: `docs/concepts/storage-retrieval-learning.md` defines trust tiers and role-labeled packs; `README.md` does not mention them.
  - Public impact: the README misses a concrete technical differentiator: packs know whether content is evidence, candidate, memory, pattern, or rule.
  - Required remediation: add a `What a pack contains` section or architecture callout.
  - Plan mapping: Tranche 3.

- **F-08: regulator is under-explained**
  - Severity: medium
  - Evidence: `README.md` line 119 gives one sentence; `docs/concepts/cells.md` lines 7-17 explain the regulator as the review and policy layer.
  - Public impact: readers may see the regulator as vague branding instead of concrete admission, promotion, retrieval, sensitivity, and export control.
  - Required remediation: define regulator in plain operational terms and link to concept docs.
  - Plan mapping: Tranche 3.

- **F-09: current-state and eventual end-state boundaries need clearer separation**
  - Severity: high
  - Evidence: `docs/status/current-implementation-status.md` marks pattern/rule distillation partial/planned and multi-cell intelligence unimplemented; the desired README must still sell the eventual end state.
  - Public impact: overclaiming would damage credibility; underselling would waste the public repo.
  - Required remediation: add a `Current alpha boundary` section plus an `Where ShyftR is going` section that is clearly gated.
  - Plan mapping: Tranche 1, Tranche 6.

- **F-10: first-run path lacks a sharper thirty-second proof**
  - Severity: medium
  - Evidence: install and quickstart are correct, but the README splits install, alpha gate, scripted demo, and manual path across multiple sections.
  - Public impact: first-time developers must assemble the fastest successful path themselves.
  - Required remediation: create a concise `Try it locally` path with install, lifecycle demo, and expected proof outputs.
  - Plan mapping: Tranche 2.

- **F-11: visual/conceptual architecture is too procedural**
  - Severity: polish
  - Evidence: `README.md` architecture diagram shows command flow but not cell boundary, regulator gate, trust tiers, grid projection, pack application, feedback learning, and confidence evolution together.
  - Public impact: the README misses the fastest way to communicate the system.
  - Required remediation: replace or supplement the diagram with a professional text diagram and optional Mermaid diagram if repo tooling accepts it.
  - Plan mapping: Tranche 3.

- **F-12: docs navigation is flat**
  - Severity: polish
  - Evidence: `README.md` lines 143-157 list docs in one sequence.
  - Public impact: a public reader cannot immediately choose between getting started, concept docs, references, examples, status, and contributor docs.
  - Required remediation: restructure documentation links by reader intent.
  - Plan mapping: Tranche 4.

- **F-13: professional README metadata and badges are absent**
  - Severity: polish
  - Evidence: `README.md` has no CI, Python, license, status, or alpha badges.
  - Public impact: the repo looks less mature than its implementation and documentation surface.
  - Required remediation: add badges that are true today and stable for GitHub rendering.
  - Plan mapping: Tranche 4.

- **F-14: safety/privacy section can become stronger and more buyer-legible**
  - Severity: medium
  - Evidence: `README.md` has a safety model, while `SECURITY.md`, `docs/status/alpha-readiness.md`, and `docs/concepts/storage-retrieval-learning.md` provide richer data boundaries, review gates, local-first posture, and auditability.
  - Public impact: serious technical users need to know where data lives, what writes durable truth, and what remains synthetic or operator-approved.
  - Required remediation: add a stronger `Safety, privacy, and trust boundaries` section.
  - Plan mapping: Tranche 5.

- **F-15: integration story needs a clearer runtime-neutral landing**
  - Severity: medium
  - Evidence: `README.md` mentions runtime-neutral adapter examples; `docs/runtime-integration-example.md` and `docs/concepts/runtime-integration-contract.md` provide the full contract.
  - Public impact: ShyftR should sell as attachable to agent runtimes without tying itself to any private runtime.
  - Required remediation: add a concise integration flow: runtime sends evidence, requests a pack, reports feedback, receives proposals.
  - Plan mapping: Tranche 2, Tranche 5.

---

## Definition of done

This plan is complete when:

- `README.md` opens with a strong, accurate ShyftR positioning statement.
- the README sells feedback-aware memory, attachable cells, append-only ledgers, regulator review, trust-labeled packs, and confidence evolution.
- eventual end-state language is inspirational but clearly separated from current alpha capability.
- install and local demo paths are faster to understand than the current split flow.
- safety, privacy, alpha, and data boundaries are obvious before a user runs real data.
- docs navigation is grouped by reader intent.
- all README claims are backed by docs, examples, tests, or status files.
- terminology guards, public readiness check, alpha gate, and development checks pass.
- an independent review confirms no overclaims, stale vocabulary, private context leakage, or weak positioning phrases were introduced.

---

## Target README structure

Use this as the end-state README table of contents:

1. Hero
   - title, badges, one-line product claim, two-sentence hook.
2. What ShyftR does
   - attachable memory cells, evidence-backed ledgers, reviewed memories, packs, feedback, confidence.
3. Why it matters
   - agents need memory that can prove provenance, evaluate usefulness, and evolve across runs.
4. What makes ShyftR different
   - cells, ledgers as truth, regulator gates, trust-labeled packs, feedback learning, local-first auditability.
5. Current alpha boundary
   - current local-first status, what works today, what remains gated.
6. Try it locally
   - clone/install, run deterministic lifecycle, expected output, alpha gate.
7. Example lifecycle
   - short narrative plus commands.
8. Architecture
   - conceptual diagram and data-flow diagram.
9. Runtime integration
   - evidence -> pack -> feedback -> proposals contract.
10. Safety, privacy, and trust boundaries
    - synthetic data, operator-approved pilots, local ledgers, review gates, no silent durable rewrites.
11. Local service and console
    - optional localhost API/UI path.
12. Documentation map
    - grouped links.
13. Development and verification
    - tests, alpha gate, readiness guard, smoke install.
14. Project status and roadmap boundary
    - alpha, public proof surface, future direction link to status/plans.
15. Contributing, security, license.

---

## Tranche 1 — Positioning, hero, and product narrative

Findings addressed: F-01, F-02, F-03, F-06, F-09.

Objective: make the first screen sell ShyftR as feedback-aware, attachable recursive memory cells for AI agents while preserving the alpha boundary.

Files:

- Modify: `README.md`.
- Reference only: `docs/concepts/differentiation-and-positioning.md`, `docs/concepts/cells.md`, `docs/status/current-implementation-status.md`, `pyproject.toml`.

Tasks:

1. Add a badge block under `# ShyftR`:
   - CI status from `.github/workflows/ci.yml`.
   - Python 3.11+.
   - License MIT.
   - Status alpha / controlled-pilot developer preview.
2. Replace the current one-line description with a stronger public claim:
   - Candidate: `Attachable recursive memory cells for AI agents.`
   - Supporting line: `ShyftR gives agents memory that can prove where it came from, whether it helped, and how it changed over time.`
3. Add a compact `What ShyftR does` section near the top:
   - captures evidence in append-only cell ledgers;
   - extracts candidates;
   - review-promotes memories;
   - assembles trust-labeled packs for runtimes;
   - records feedback;
   - evolves confidence;
   - distills patterns and proposes rules as gated future-facing lifecycle work.
4. Add `Why cells`:
   - cell as isolated, attachable, durable memory namespace;
   - attach scopes: agent, user, project, team, application, domain;
   - regulator controls admission, promotion, retrieval, sensitivity, and export.
5. Add a category-positioning table using broad categories:
   - vector indexes: acceleration layer;
   - framework memory helpers: in-runtime convenience;
   - managed memory services: hosted persistence;
   - RAG pipelines: context retrieval;
   - ShyftR: local-first, evidence-backed, feedback-aware memory cells with review gates and provenance.
6. Keep status language explicit:
   - local-first alpha;
   - controlled-pilot developer preview;
   - synthetic or operator-approved data;
   - hosted operation and multi-tenant production are outside the current public release.

Acceptance criteria:

- A new reader can explain ShyftR's category and differentiators from the top third of the README.
- Current-state statements match `docs/status/current-implementation-status.md`.
- Eventual end-state statements are labeled as roadmap/gated when implementation status is partial or planned.
- No competitor-specific attack copy appears in the README.
- No weak contrast phrasing is introduced.

Verification:

```bash
python scripts/terminology_inventory.py --fail-on-public-stale
python scripts/terminology_inventory.py --fail-on-capitalized-prose
python3 - <<'PY'
from pathlib import Path
terms = ['not '+'just', 'not '+'only', 'not '+'simply', 'not '+'merely', 'is '+'not', 'is '+'not trying', 'another memory '+'bucket', 'just '+'context', 'just '+'a store']
for p in [Path('README.md')]:
    for i, line in enumerate(p.read_text(errors='ignore').splitlines(), 1):
        low = line.lower()
        if any(t in low for t in terms):
            print(f'{p}:{i}:{line}')
PY
```

Expected: terminology commands pass and the README-specific weak-phrase scan prints nothing.

---

## Tranche 2 — Quickstart, first-run proof, and demo story

Findings addressed: F-05, F-10, F-15.

Objective: make the README immediately runnable and explain what the run proves.

Files:

- Modify: `README.md`.
- Modify if needed: `examples/README.md`.
- Reference only: `examples/run-local-lifecycle.sh`, `docs/example-lifecycle.md`, `docs/runtime-integration-example.md`, `scripts/alpha_gate.sh`, `scripts/smoke-install.sh`.

Tasks:

1. Replace `Install from clone` and `Quickstart` with a single `Try it locally` section:
   - clone;
   - create Python 3.11+ venv;
   - install `.[dev,service]`;
   - run `bash examples/run-local-lifecycle.sh`;
   - run `bash scripts/alpha_gate.sh`.
2. Add expected output markers:
   - `ALPHA_GATE_READY` for alpha gate;
   - lifecycle script confirms temporary cell creation, evidence ingest, candidate extraction, memory promotion, pack assembly, feedback recording, diagnostics, ledger verification, and backup creation.
3. Add a short `What the demo proves` subsection:
   - evidence enters an append-only ledger;
   - a candidate is reviewed before becoming memory;
   - a pack supplies bounded context;
   - feedback records usefulness;
   - ledger verification and backup prove inspectability.
4. Add a concise manual CLI path under an expandable or secondary section, keeping the current commands but explaining placeholders.
5. Add a runtime-neutral adapter mini-story:
   - external runtime sends evidence;
   - ShyftR returns a pack;
   - runtime reports feedback;
   - ShyftR creates review-gated proposals.
6. Keep service and console setup separate from the first-run path so optional UI work does not slow the first proof.

Acceptance criteria:

- A developer can find the fastest successful path within 30 seconds of opening the README.
- The quickstart uses synthetic data by default.
- The demo story explains why the commands matter.
- Runtime integration remains generic and avoids private runtime examples.

Verification:

```bash
python3.11 -m venv /tmp/shyftr-readme-smoke-venv
. /tmp/shyftr-readme-smoke-venv/bin/activate
python -m pip install -U pip
python -m pip install -e '.[dev,service]'
bash examples/run-local-lifecycle.sh
bash scripts/alpha_gate.sh
```

Expected: lifecycle script completes and alpha gate final line is `ALPHA_GATE_READY`.

---

## Tranche 3 — Lifecycle, architecture, trust tiers, and regulator explanation

Findings addressed: F-02, F-03, F-04, F-07, F-08, F-11.

Objective: make the README communicate ShyftR's conceptual architecture at the same quality as its implementation.

Files:

- Modify: `README.md`.
- Modify if needed: `docs/concepts/cells.md`, `docs/concepts/storage-retrieval-learning.md` only to fix inconsistencies discovered while drafting.
- Reference only: `docs/concepts/runtime-integration-contract.md`, `docs/api.md`, `docs/console.md`.

Tasks:

1. Replace the safety model diagram with two explicit loops:

```text
Durable lifecycle:
evidence -> candidate -> memory -> pattern -> rule

Application loop:
pack -> feedback -> confidence
```

2. Add a conceptual architecture diagram:

```text
agent or runtime
      |
      v
  evidence intake
      |
      v
+--------------------------- cell ---------------------------+
| append-only ledger is truth                                |
| regulator gates admission, review, retrieval, and export   |
| grid indexes are rebuildable acceleration                  |
| reviewed memory, patterns, and rules carry provenance      |
+------------------------------------------------------------+
      |
      v
 trust-labeled pack -> agent run -> feedback -> confidence
```

3. Explain trust tiers in one short table:
   - rule: highest-confidence shared guidance;
   - memory: reviewed durable memory;
   - pattern: recurring structure distilled from related memories;
   - candidate: proposed memory awaiting review;
   - evidence: raw source material.
4. Explain pack roles:
   - guidance items;
   - caution items;
   - background items;
   - conflict items.
5. Define the regulator in operational terms:
   - admission checks;
   - candidate review;
   - memory promotion;
   - sensitivity and policy filtering;
   - export limits;
   - proposal review.
6. Align capitalization with house style:
   - lowercase lifecycle nouns in prose;
   - clear title-style labels only inside diagram labels or tables.

Acceptance criteria:

- Diagrams explain both durable memory evolution and runtime application.
- The README includes pattern and rule without implying broad production readiness.
- Trust tiers and regulator functions are understandable without opening concept docs.
- Architecture claims match current implementation or are explicitly future/gated.

Verification:

```bash
python scripts/terminology_inventory.py --fail-on-public-stale
python scripts/terminology_inventory.py --fail-on-capitalized-prose
python scripts/public_readiness_check.py
python -m pytest -q tests/test_pack.py tests/test_feedback.py tests/test_policy.py tests/test_privacy_sensitivity.py tests/test_runtime_integration_demo.py
```

Expected: all commands pass.

---

## Tranche 4 — Documentation map, metadata, and public polish

Findings addressed: F-12, F-13.

Objective: make the README feel like a professional public GitHub project.

Files:

- Modify: `README.md`.
- Modify if needed: `pyproject.toml` description and keywords, only if the README hero changes should be mirrored.
- Reference only: `.github/workflows/ci.yml`, `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md`, `LICENSE`.

Tasks:

1. Group documentation links by reader intent:
   - Start here: current status, alpha readiness, example lifecycle, examples.
   - Concepts: cells, storage/retrieval/learning, terminology compatibility, runtime integration contract.
   - Reference: API, console, development.
   - Governance: contributing, security, changelog, license.
   - Planning/history: plans, sources, feeds, runbooks with a clear historical/planning note.
2. Add or verify badges:
   - CI badge points at the current workflow on `main`.
   - Python badge matches `requires-python >=3.11`.
   - License badge matches MIT.
   - Alpha badge uses honest status wording.
3. Mirror the improved short description in `pyproject.toml` if appropriate.
4. Confirm repository topics and README keywords stay aligned.
5. Keep README length comprehensive but navigable. Target roughly 250-400 lines after overhaul, with deeper material linked out.

Acceptance criteria:

- Docs map is reader-intent based.
- Badges render on GitHub and are truthful.
- Package metadata and README positioning do not conflict.
- Historical/source/planning docs are clearly labeled as such.

Verification:

```bash
git diff -- README.md pyproject.toml
git diff --check
python scripts/public_readiness_check.py
```

Optional GitHub metadata verification:

```bash
gh repo view stefan-mcf/shyftr --json description,repositoryTopics,visibility,url
```

Expected: diffs are intentional, whitespace check passes, public readiness passes, and GitHub metadata remains aligned.

---

## Tranche 5 — Safety, privacy, data boundaries, and integration trust

Findings addressed: F-14, F-15.

Objective: make the README trustworthy for technical evaluators who care about data handling, auditability, local operation, and integration boundaries.

Files:

- Modify: `README.md`.
- Modify if needed: `SECURITY.md`, `docs/status/alpha-readiness.md`, `docs/concepts/runtime-integration-contract.md` only for consistency fixes discovered during drafting.
- Reference only: `docs/api.md`, `docs/console.md`, `docs/status/current-implementation-status.md`.

Tasks:

1. Expand `Safety, privacy, and trust boundaries`:
   - local-first cells;
   - synthetic data default;
   - operator-approved pilot data only;
   - append-only ledger truth;
   - rebuildable indexes;
   - explicit review before durable authority;
   - regulator controls retrieval and export;
   - no hosted service claim;
   - no multi-tenant production guarantee;
   - no silent durable rewrite.
2. Add `What writes truth`:
   - ledgers under cells;
   - review/promote/feedback commands;
   - local service delegates to same functions;
   - console is a local UI over the same boundaries.
3. Add `What stays projection`:
   - grid indexes;
   - API summaries;
   - console views;
   - profile/readiness reports.
4. Add a clear sensitive-data warning for alpha testers and link to `SECURITY.md` and `docs/status/alpha-readiness.md`.
5. Ensure integration examples describe external runtimes as owners of execution, while ShyftR owns durable memory, provenance, packs, feedback, and proposals.

Acceptance criteria:

- A cautious developer can tell exactly what data to use and avoid during alpha testing.
- README safety claims match current implementation status and security docs.
- Service/console language stays localhost-only.
- Runtime integration language stays advisory and review-gated.

Verification:

```bash
python scripts/public_readiness_check.py
bash scripts/alpha_gate.sh
python -m pytest -q tests/test_privacy_sensitivity.py tests/test_policy.py tests/test_console_api.py tests/test_server.py
```

Expected: all commands pass and alpha gate final line is `ALPHA_GATE_READY`.

---

## Tranche 6 — Current-state honesty, roadmap boundary, and claim audit

Findings addressed: F-09 plus final claim hygiene for all findings.

Objective: ensure the README sells the eventual end state without overstating current implementation.

Files:

- Modify: `README.md`.
- Modify if needed: `docs/status/current-implementation-status.md` if the README uncovers stale status text.
- Reference only: `docs/status/public-readiness-audit.md`, `docs/plans/2026-04-24-shyftr-implementation-tranches.md`, `docs/plans/2026-04-24-shyftr-runtime-integration-adapter-plan.md`, `docs/plans/2026-04-24-shyftr-active-learning-follow-up-plan.md`.

Tasks:

1. Create a claim matrix during drafting with three buckets:
   - implemented and tested;
   - implemented but alpha/qualified;
   - planned, gated, or private-core dependent.
2. For every README claim about pattern/rule distillation, advanced scoring, multi-cell intelligence, managed-memory replacement, hosted service, benchmarks, or commercial integrations, choose one:
   - remove from README;
   - move behind roadmap/gated wording;
   - link to a plan/status doc;
   - implement and verify separately before claiming.
3. Add a short `Roadmap boundary` note:
   - current public repo proves local-first cells and controlled-pilot workflows;
   - broader adoption paths remain gated by implementation evidence and review.
4. Remove any private operator references, local absolute paths, private runtime names, or internal-only strategy details from README draft.
5. Run a final public-language pass for clear, professional wording.

Acceptance criteria:

- Every current-tense product claim can be traced to implementation status, tests, examples, or docs.
- Every future-facing claim is labeled as planned, gated, or roadmap material.
- README contains no private runtime/project dependency and no local machine paths.
- README remains compelling without vague hype or weak contrast phrasing.

Verification:

```bash
python - <<'PY'
from pathlib import Path
text = Path('README.md').read_text(errors='ignore')
needles = ['/'+'Users'+'/', '/'+'home'+'/', 'Ant'+'aeus', 'private'+'-core', 'managed-memory replacement', 'production-hardened hosted']
for n in needles:
    if n.lower() in text.lower():
        print(n)
PY
python scripts/terminology_inventory.py --fail-on-public-stale
python scripts/terminology_inventory.py --fail-on-capitalized-prose
python scripts/public_readiness_check.py
git diff --check
```

Expected: no private/path hits from the custom scan, terminology checks pass, public readiness passes, and diff check passes.

---

## Tranche 7 — Full verification, independent review, commit, push gate

Findings addressed: all findings.

Objective: verify the README overhaul as a public-facing artifact before committing or pushing.

Files:

- Modify: final intended files only.
- No external publication changes without explicit operator approval.

Tasks:

1. Inspect the final diff:

```bash
git diff -- README.md docs/plans/2026-05-06-shyftr-readme-public-overhaul-plan.md pyproject.toml SECURITY.md docs/status/alpha-readiness.md docs/status/current-implementation-status.md docs/concepts/runtime-integration-contract.md
```

2. Run the complete local verification bundle:

```bash
python -m pytest -q
bash examples/run-local-lifecycle.sh
python scripts/terminology_inventory.py --fail-on-public-stale
python scripts/terminology_inventory.py --fail-on-capitalized-prose
python scripts/public_readiness_check.py
bash scripts/check.sh
bash scripts/alpha_gate.sh
git diff --check
```

3. Run optional console verification when Node/npm are available:

```bash
(cd apps/console && npm install && npm run build && npm audit --omit=dev)
```

4. Run README-specific public wording scans:

```bash
python3 - <<'PY'
from pathlib import Path
terms = ['not '+'just', 'not '+'only', 'not '+'simply', 'not '+'merely', 'is '+'not', 'is '+'not trying', 'another memory '+'bucket', 'just '+'context', 'just '+'a store']
for p in [Path('README.md')]:
    for i, line in enumerate(p.read_text(errors='ignore').splitlines(), 1):
        low = line.lower()
        if any(t in low for t in terms):
            print(f'{p}:{i}:{line}')
PY
python3 - <<'PY'
from pathlib import Path
private_terms = ['/'+'Users'+'/', '/'+'home'+'/', 'Ant'+'aeus', 'private'+'-core']
text = Path('README.md').read_text(errors='ignore')
for term in private_terms:
    if term.lower() in text.lower():
        print(term)
PY
```

5. Request independent review with this scope:
   - README positioning strength;
   - current-state accuracy;
   - alpha/data boundary clarity;
   - terminology compliance;
   - install/quickstart correctness;
   - public/private boundary;
   - no private identifiers or local paths;
   - no broad claims unsupported by status files.
6. Commit only after local verification and independent review pass.
7. Push only after the operator approves push or the active task explicitly includes push.
8. After any push, verify exact remote SHA and CI:

```bash
LOCAL_SHA=$(git rev-parse HEAD)
REMOTE_SHA=$(gh api repos/stefan-mcf/shyftr/git/ref/heads/main --jq '.object.sha')
test "$LOCAL_SHA" = "$REMOTE_SHA"
gh run list --repo stefan-mcf/shyftr --limit 20 --json databaseId,status,conclusion,headSha,workflowName,url --jq '.[] | select(.headSha=="'"$LOCAL_SHA"'")'
```

Acceptance criteria:

- Complete local verification passes.
- Independent review returns pass or all findings are resolved.
- Git status contains only intended README-overhaul files.
- If pushed, remote `main` equals local `HEAD` and CI succeeds for that exact SHA.

---

## README copy constraints

Use these constraints while drafting:

- Use lowercase lifecycle nouns in prose: evidence, candidate, memory, pattern, rule, cell, regulator, ledger, grid, pack, feedback.
- Use `ShyftR` for the product and `shyftr` for repo/package/CLI.
- Avoid deprecated or historical product vocabulary as current terms.
- Avoid private runtime/project names in README examples.
- Avoid direct competitor callouts in the README body; category-level positioning is enough.
- Avoid promising hosted SaaS, multi-tenant production, package release, broad managed-memory replacement, production hardening, or external runtime control.
- Avoid fake metrics. If benchmarks are added, create a benchmark script and publish exact methodology first.
- Avoid local absolute paths in public docs.
- Keep current alpha warnings professional and concise.
- Keep the README comprehensive, but move deep implementation details to docs.

---

## Suggested hero draft for Tranche 1

This is drafting input, not mandatory final copy:

```markdown
# ShyftR

Attachable recursive memory cells for AI agents.

ShyftR gives agents memory that can prove where it came from, whether it helped, and how it changed over time. It captures evidence in append-only cell ledgers, promotes reviewed memories through a regulator, assembles trust-labeled packs for runtimes, and records feedback so useful memory gains confidence while harmful or stale memory can be challenged.

Current status: local-first alpha / controlled-pilot developer preview. Use synthetic or operator-approved data, run the alpha gate, and treat hosted or multi-tenant production deployment as outside the current public release.
```

---

## Suggested differentiator table for Tranche 1

| Need | Typical solution category | ShyftR stance |
|---|---|---|
| Store facts | profile stores or framework memory helpers | preserve provenance and review before durable authority |
| Search context | vector index or RAG pipeline | keep ledgers as truth and use indexes as rebuildable acceleration |
| Scope memory | global assistant profile | attach cells to agents, users, projects, teams, apps, or domains |
| Use memory safely | raw retrieval into prompt context | assemble trust-labeled packs through regulator policy |
| Improve over time | manual edits or opaque updates | record feedback and evolve confidence from verified outcomes |
```

---

## Deferred decisions

These require explicit implementation or operator approval before public README claims expand:

- public benchmark metrics;
- hosted service language;
- package publishing language;
- multi-cell intelligence claims;
- commercial-core ranking/scoring details;
- managed-memory replacement claims beyond bounded controlled-pilot status;
- screenshots or diagrams generated from non-synthetic data;
- public roadmap removal or broad cleanup of alpha language.
