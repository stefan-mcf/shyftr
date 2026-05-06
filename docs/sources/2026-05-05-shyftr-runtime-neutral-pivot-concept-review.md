# ShyftR Post-Antaeus Concept Review

> Source: Hermes remote terminal side review with swarm advisory lanes on 2026-05-05.
> Context: Antaeus has been disbanded/shut down, so ShyftR should no longer depend on Antaeus as its first-party proving ground or public product boundary.

## Working verdict

Antaeus shutting down changes the proving path, not the core ShyftR thesis.

ShyftR should remain a local-first universal memory substrate: cell ledgers are canonical truth; the regulator controls admission, promotion, retrieval, mutation, and export; the grid accelerates retrieval; packs apply memory to work; feedbacks close the learning loop; profiles, markdown, dashboards, and UI views are projections.

The concept should pivot from “memory layer for Antaeus/Hermes” to “runtime-neutral memory control plane for agents, assistants, projects, and knowledge workflows.” Antaeus/Hermes can remain private historical source material, but public and executable planning should speak in terms of target runtimes, existing memory backends, bounded domains, global runtime memory, and adapter contracts.

## What to keep

- The power vocabulary and lifecycle: evidence -> candidate -> memory -> pattern -> rule.
- The universal substrate boundary: ShyftR owns durable memory authority, not execution, note editing, orchestration, or hosted collaboration.
- The staged adoption shape: shadow observation -> advisory pack injection -> bounded-domain authority -> runtime-wide authority.
- The safety posture: append-only ledgers, review gates, provenance, explainable pack selection, rollback/fallback during pilots, and measured feedbacks.
- The product promise: capture evidence, promote reviewed memory, retrieve bounded packs, record feedbacks, learn from feedbacks, and maintain auditability.

## What to adjust now

1. Reframe Antaeus/Hermes checkpoints as runtime-memory adoption checkpoints.
   - “Antaeus/Hermes Integration Checkpoints” should become “Runtime memory Integration Checkpoints.”
   - “Antaeus task IDs” becomes “target runtime task IDs.”
   - “sector manager” becomes “bounded-domain manager,” “planning layer,” or “orchestration layer.”
   - “Hermes main memory” becomes “runtime-wide memory authority.”
   - “mem0” becomes “existing memory backend” unless discussing a private historical migration source.

2. Treat the Antaeus/Hermes source strategy as historical/reference input.
   - Preserve it under docs/sources as provenance.
   - Do not let it define current public-facing plan language.

3. Replace the first-party Antaeus proving ground with one real, repeatable, runtime-neutral proof loop.
   - candidate A: generic local assistant/runtime harness that requests packs before tasks and records feedbacks after tasks.
   - candidate B: Hermes-style adapter if Hermes remains active as a generic runtime target, not as Antaeus.
   - candidate C: markdown/docs workspace adapter that ingests notes/docs as evidences, proposes candidates, and drives review.

4. Move toward contract completion before more application surface.
   - Provider contract front door: remember, search, profile, forget/replace/deprecate, pack, record_feedback, import/export.
   - Closed-loop priority: pack + feedback + retrieval logs + confidence/provenance explanation.
   - UI remains an operator console, not a full workspace app.

## Recommended near-term plan changes

- Rename Tranche 3.1 from Antaeus-specific adapter work to a generic “Runtime Adapter / Pilot Harness” tranche.
- Add an explicit adapter/pilot implementation tranche near the post-1.8 boundary if checkpoints are meant to be executed before Phase 3.
- Make checkpoint advancement metric-driven:
  - pack application rate
  - useful / harmful / ignored / missing rates
  - over-retrieval rate
  - review queue burden
  - rollback/replay success
- Clarify that no adapter or existing-memory-backend replacement is implemented until the relevant tranche lands.
- Keep public docs product-neutral and category-level. Named runtimes/providers belong in sources, private notes, or adapter examples.

## Discussion prompts

1. What should be the new first proof loop?
   - generic runtime harness
   - Hermes-style adapter
   - markdown/docs workspace adapter
   - another repeated real workflow

2. Is the near-term narrative “agent memory provider” first, or “knowledge workspace substrate” first?
   - Both are valid category targets.
   - The first proof should pick one front door so the MVP story stays sharp.

3. How much of Phase 2 UI is required before authority pilots?
   - A pack debugger, feedback viewer, and review queue may be safety requirements rather than polish.

4. What thresholds unlock broader authority?
   - Define minimum sample size and acceptable harmful/missing/review-burden rates before bounded-domain or runtime-wide authority.

## Swarm evidence

Advisory reports generated in `.hermes-swarm-reports/`:

- `swarm10-plan-review.md`: recommends reframing checkpoints as generic runtime-memory adoption gates while preserving staged safety logic.
- `swarm2-repo-state-review.md`: found code/tests are already runtime-neutral; Antaeus/mem0 are mainly in plans/source strategy docs.
- `swarm6-strategy-review.md`: recommends Universal memory Substrate as the strategic arc plus one narrow closed-loop proof.

One concept-review lane (`swarm5`) was smoke-tested but killed after timeout without a report; it is not counted as completed evidence.
