# Phase 7 public/private split

Status: implemented as public-safe Phase 7 frontier foundations for local controlled pilots.

This split keeps public `main` focused on transparent, append-only, review-gated primitives. Private calibration, proprietary ranking, advanced compaction, commercial strategy, real memory data, and private operator workflow remain outside this public surface unless explicitly approved later.

## Split table

| Phase 7 tranche | public-safe contract/skeleton | public-safe baseline implementation | private-core reserved logic | deferred/non-goal items | tests required | docs required |
| --- | --- | --- | --- | --- | --- | --- |
| 7.1 confidence belief baseline | confidence state fields alongside scalar `confidence` | deterministic beta-binomial-style counts, expected confidence, uncertainty, bounds, scalar compatibility | learned calibration, private evaluator data, proprietary scoring weights | automatic confidence mutation outside reviewed feedback | `tests/test_confidence_model.py` | confidence/simulation concept doc |
| 7.2 causal memory graph | append-only graph edge ledger with explicit edge types | graph edge model, validation, listing, and pack explainability context | hidden causality inference, graph ranking optimization | graph auto-mutation from unreviewed runtime records | `tests/test_memory_graph.py` | graph/reputation concept doc |
| 7.3 policy simulation | read-only simulation request/report schema | dry-run pack replay comparing current and proposed retrieval modes | private simulation scoring or customer data replay | automatic policy application | `tests/test_policy_simulation.py` | confidence/simulation concept doc |
| 7.4 retrieval modes | explicit retrieval mode names and validation | transparent public mode table for balanced, conservative, exploratory, risk_averse, audit, rule_only, and low_latency | moat-bearing ranking formulas | silent default behavior changes | `tests/test_retrieval_modes.py` | confidence/simulation concept doc and example |
| 7.5 reputation baseline | append-only reputation event ledger and summaries | approval, rejection, useful, harmful, contradiction, stale, and import rates | advanced trust weighting and private origin scoring | reputation bypassing review gates | `tests/test_reputation.py` | graph/reputation concept doc |
| 7.6 regulator proposals | proposal and review event shapes | repeated synthetic event detection, required simulation reference for approval, no policy mutation | self-modifying regulator logic without human review | auto-apply of policies or rules | `tests/test_regulator_proposals.py` | graph/reputation concept doc |
| 7.7 synthetic eval generator | public-safe eval task schema | deterministic tasks from synthetic feedback and high-value memory fixtures | real/private training data generation | opaque benchmark generation | `tests/test_eval_generator.py` | eval example docs |
| 7B surface coherence | CLI/API/console discovery surfaces | `pack --retrieval-mode`, `simulate`, `graph`, `reputation`, `regulator-proposals`, `evalgen`, `/simulate`, `/frontier`, console projection | hosted service or production control plane | stable public API guarantee | console/server/CLI smoke tests | status docs |
| 7C docs/status | public concepts and examples | public docs tied to implemented behavior | private roadmap or strategy | release-scope claims | terminology/readiness guards | this document plus concept/example docs |
| 7D bridge landing | exact-SHA proof gate | local tests, guards, alpha gate, push, CI watch | Checkpoint E/F or Phase 8 execution | starting Phase 8 | full suite and CI | closeout evidence after CI |

## One-run gate checklist

- [x] public/private classification complete.
- [x] scalar compatibility preserved for `confidence` while belief metadata is additive.
- [x] review gates preserved for graph, reputation, import, regulator, and policy state.
- [x] simulation is read-only by default and does not apply proposed settings.
- [x] reputation may prioritize review/proposals but cannot bypass review gates.
- [x] synthetic eval generation excludes private data by default.
- [ ] full local gates green.
- [ ] GitHub CI green for the exact pushed SHA.

## Public/private classification of changed surfaces

| Surface | Classification | Notes |
| --- | --- | --- |
| `src/shyftr/frontier.py` and small wrapper modules | public proof / public contract | transparent baseline algorithms only. |
| `src/shyftr/pack.py`, `layout.py`, `cli.py`, `console_api.py`, `server.py` updates | public proof | additive fields and read-only surfaces; no hosted or production claim. |
| `tests/test_*phase 7*` focused tests | public synthetic examples | deterministic local fixtures only. |
| `docs/concepts/*`, `docs/phase-7-example.md`, status docs | public contract / public proof | describes implemented local controlled-pilot behavior. |
| private ranking, learned calibration, real runtime data | private-core reserved | not present in public `main`. |

## Non-goals for this public landing

- No private scoring, ranking, compaction, calibration, or commercial strategy.
- No use of real/private memory data.
- No hosted SaaS, stable-release, package-release, Checkpoint E, Checkpoint F, or Phase 8 claim.
- No automatic policy mutation, auto-approval, auto-import, or reputation trust bypass.

## Closeout evidence fields

Record after bridge landing:

- final local full test verdict;
- terminology inventory verdicts;
- public readiness verdict;
- alpha gate verdict;
- exact pushed SHA;
- exact GitHub CI run and result;
- remaining private-core/deferred items, if any.
