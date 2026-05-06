# ShyftR Compaction Intelligence Concept

Date: 2026-05-05
Status: Source concept note
Scope: Future ShyftR product direction; runtime-neutral compaction support

## Summary

ShyftR has a strong potential role in improving context compaction for agentic systems. As agent runtimes increasingly depend on compactors to preserve continuity across long sessions, the limiting factor will not only be summarization quality. The harder problem will be deciding what deserves to survive compression, why it should survive, how much confidence to place in it, and whether preserving it helped future work.

ShyftR is well positioned to become a compaction intelligence layer: a runtime-neutral substrate that helps compactors select, justify, preserve, and evaluate the most important memory before context is compressed.

The concise thesis:

```text
As agent contexts grow and compaction becomes routine, agent runtimes will need memory-aware compactors. ShyftR can supply the substrate that tells compactors what deserves to survive, records why, and learns from whether that choice helped.
```

## Core framing

ShyftR should not be framed as merely a memory store used after compaction. It can become part of the decision system that improves compaction itself.

A conventional compactor often follows this pattern:

```text
large context -> summarize important things -> smaller context
```

A ShyftR-assisted compaction loop could evolve this into:

```text
large context
-> extract Pulses and Sparks
-> compare against existing Charges, Coils, and Rails
-> assemble a compaction-oriented Pack
-> compact with provenance and confidence
-> observe future Signal
-> improve future compactions
```

In this model, ShyftR does not merely summarize the current session. It helps decide what deserves to survive compression, for whom, under what scope, with what confidence, and with what provenance.

## Problem: compaction is becoming a memory-selection problem

Compaction has several hard problems that simple summarization does not fully solve:

- distinguishing durable lessons from temporary operational state;
- preserving user intent without over-preserving incidental details;
- separating project, user, session, runtime, and task memory;
- identifying which memories should become long-term records;
- avoiding stale, harmful, duplicated, or over-generalized memories;
- retaining enough provenance to audit why a compressed memory exists;
- learning whether previous compactions preserved the right information;
- recovering from compaction misses, where a future agent loses an important fact.

These are memory governance problems, not only token-reduction problems.

## ShyftR mapping

ShyftR's existing doctrine maps naturally onto compaction intelligence:

- **Pulse**: raw pre-compaction context, such as session transcript, task closeout, tool run, issue, document, or runtime log.
- **Spark**: candidate memory extracted from the context before compaction.
- **Charge**: reviewed durable memory that should survive future compactions and retrieval events.
- **Coil**: repeated pattern distilled from multiple compactions, sessions, or related Charges.
- **Rail**: high-confidence rule or policy that should strongly influence future compaction and Pack construction.
- **Grid**: rebuildable retrieval/index layer used to find relevant memory before compaction.
- **Pack**: bounded memory bundle supplied to the runtime, agent, or compactor.
- **Signal**: feedback record showing whether the compacted context helped, missed key facts, preserved stale assumptions, or caused confusion.
- **Regulator**: review and policy boundary that prevents promotion of junk, secrets, transient state, unsafe details, and stale assumptions.

This turns compaction into a learning loop:

```text
Pulse -> Spark -> Charge -> Pack -> compaction -> resumed work -> Signal -> confidence update
```

## Product boundary

The recommended boundary is:

```text
Runtime compactor = performs mechanical compression.
ShyftR = selects durable memory, provides provenance, manages confidence, and learns from compaction outcomes.
```

ShyftR should not initially position itself as the compactor itself. Mechanical compression can remain owned by the attached runtime or model. ShyftR's stronger role is to make that compaction memory-aware, provenance-aware, review-aware, and outcome-aware.

This preserves ShyftR's runtime-neutral positioning. Any runtime with context pressure could ask ShyftR what should survive before the runtime performs its own compression.

## Proposed module: Continuity Pack

A compelling product primitive is the **Continuity Pack**.

A Continuity Pack is a bounded memory/context bundle created specifically for compaction and session continuation. Before a runtime compacts context, it asks ShyftR:

```text
Given this context and task state, what must survive compression?
```

ShyftR returns a structured Pack that may include:

- active goal and user intent;
- current task state;
- open decisions and unresolved questions;
- constraints that must remain active;
- relevant user preferences;
- relevant project or repository facts;
- recent failures, fixes, and verification evidence;
- durable Charges touched during the session;
- newly proposed Sparks from the session;
- Coils or Rails that should shape the next step;
- items explicitly marked ephemeral or unsafe to preserve;
- provenance links back to the original Pulses.

The runtime compactor then uses the Continuity Pack as the skeleton for its compressed context.

Potential adjacent terms:

- Compaction Pack
- Survival Pack
- Context Regulator
- Compression Signal
- Resume Pack
- Session Coil

Among these, **Continuity Pack** is the strongest concept because the core value is preserving continuity across context loss.

## Proposed module: Compaction Signal

A **Compaction Signal** records whether a compacted context worked after the session resumed.

Example Signal dimensions:

- `missed_important_fact`: an important fact was lost during compaction.
- `preserved_stale_fact`: the compacted context carried forward outdated or contradicted information.
- `overweighted_irrelevant_memory`: irrelevant memory was preserved too strongly.
- `lost_user_intent`: the compressed context failed to preserve the user's actual goal or preference.
- `kept_correct_constraint`: the compaction successfully preserved a critical constraint.
- `saved_time`: preserved context reduced rediscovery or repeated work.
- `caused_bad_action`: compacted memory caused an incorrect action or recommendation.

Signals would update ShyftR's memory state:

- useful Charges gain confidence;
- harmful or stale Charges decay;
- repeated misses become new Sparks;
- repeated compaction failures become Coils;
- high-confidence repeated patterns may propose Rails;
- unsafe or contradicted memory can be isolated by the Regulator.

## Why this is differentiated

Many compaction systems are one-shot summarizers. They compress the visible context but lack durable machinery for:

- provenance;
- review gates;
- confidence and decay;
- reuse history;
- cross-session learning;
- separation of user/project/runtime/session memory;
- auditability;
- negative feedback when compaction fails.

ShyftR can supply those missing properties.

This makes the product claim more precise:

```text
Compaction should be memory-aware, provenance-aware, and outcome-aware.
```

## Runtime-neutral applicability

This direction fits the post-Antaeus runtime-neutral ShyftR strategy. ShyftR does not need to belong to a single agent runtime. It can attach to any runtime that experiences context pressure:

- terminal agents;
- coding agents;
- research agents;
- browser agents;
- project-management agents;
- support/chat agents;
- multi-agent swarms;
- workspace assistants;
- long-running autonomous workflows.

The common interface is simple:

```text
Runtime sends Pulses.
Runtime requests a Continuity Pack before compaction.
Runtime performs compression.
Runtime reports a Compaction Signal after resumed work.
ShyftR updates Charge confidence, proposes Sparks, and improves future Packs.
```

## Implementation implications

This concept can be developed incrementally without changing ShyftR's core architecture.

Possible implementation path:

1. Define a `continuity_pack` profile type that ranks Charges, Sparks, Coils, Rails, and active session facts for compaction survival.
2. Add a compaction-oriented Pack schema with sections for active intent, current state, durable memory, open decisions, risks, and ephemeral exclusions.
3. Capture session closeouts as Pulses.
4. Extract Sparks from closeouts before compaction.
5. Add a Compaction Signal schema to record continuation quality.
6. Use Signal data to update confidence, decay stale memory, and identify repeated compaction misses.
7. Add tests around survival ranking, stale-memory exclusion, and missed-memory feedback.
8. Later, expose the flow through a runtime adapter or pilot harness.

The first proof does not require ShyftR to own summarization. A pilot can use deterministic or model-assisted Pack construction, then let the attached runtime perform the actual compaction.

## Strategic significance

This concept strengthens ShyftR's position as a universal memory substrate and control plane. It connects ShyftR directly to a growing operational need in agentic systems: continuity under context pressure.

The strategic claim:

```text
Compactors decide what survives context loss. ShyftR can make that decision inspectable, memory-aware, review-gated, and self-improving.
```

This is a strong future module because it uses ShyftR's core primitives exactly as intended:

- Cell ledger as truth;
- Grid for retrieval;
- Pack for application;
- Signal for learning;
- Regulator for trust;
- Sparks, Charges, Coils, and Rails for recursive improvement.

## Working conclusion

ShyftR has a credible and differentiated place in the future of compaction. The opportunity is not to compete with every runtime's internal summarizer. The stronger opportunity is to become the memory substrate that informs compaction, preserves continuity, and learns from compaction outcomes.

A future ShyftR compaction flow can be summarized as:

```text
Session Pulse
-> Spark extraction
-> Regulator review
-> Continuity Pack
-> runtime compaction
-> resumed agent work
-> Compaction Signal
-> Charge confidence update
```

This should be preserved as a serious future product concept for ShyftR.
