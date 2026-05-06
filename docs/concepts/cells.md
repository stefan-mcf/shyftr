# Memory Cells

ShyftR's primary abstraction is a Cell.

A Cell is an isolated, attachable, durable memory namespace with its own Cell Ledger, Regulator, reviewed Charges, Grid, reports, and policy. A Cell can attach to a person, assistant, agent, project, team, organization, application, domain, capability, or global rail layer.

Canonical system vocabulary:

- ShyftR Cell: a bounded attachable memory unit.
- Regulator: the review and policy layer controlling admission, promotion, retrieval, and export.
- Cell Ledger: the append-only canonical truth inside a Cell.
- Charge: a reviewed durable memory item.
- Grid: the rebuildable retrieval and index layer.
- Pack: the bounded memory bundle supplied to an agent or runtime.
- Signal: the pulseback record that tells ShyftR whether retrieved memory helped or harmed.

The Regulator remains separate from durable truth storage. It is the Cell-local scope and policy surface implemented by admission checks, review gates, trust-tier filtering, retrieval limits, and export rules.

## Why Cell?

ShyftR is an attachable memory module. A Cell can be slotted into an agent, project, team, tool, or domain so reviewed experience can shift future behavior.

## Common Cell types

- `core`: default user or deployment memory
- `personal`: personal assistant memory
- `agent`: one autonomous agent's durable learning
- `project`: project-local knowledge and heuristics
- `team`: shared team memory
- `organization`: organization-wide rail
- `application`: app-specific memory
- `domain`: domain or capability memory
- `global-rail`: multi-Cell promoted rail

## Default memory

A user's default memory can be represented as a `core` Cell.

Example:

```text
cells/core/memory/
  ledger/
  charges/
  grid/
  summaries/
  reports/
  config/
```

This lets ShyftR handle ordinary assistant memory while using the same review, promotion, retrieval, and recursive distillation machinery as project, team, agent, and domain Cells.

## Lifecycle

Core ShyftR code should depend on the portable lifecycle:

```text
Spark -> Charge -> Coil -> Rail
```

- Pulse: raw evidence preserved append-only before lifecycle promotion.
- Spark: bounded candidate memory piece extracted from a Pulse.
- Charge: reviewed durable memory.
- Coil: recursive pattern distilled from related Charges.
- Rail: shared promoted rule.

## Rule

Core ShyftR code should depend on Cells, the Cell Ledger, the Regulator, Pulses, Sparks, Charges, Coils, Rails, the Grid, Packs, Signal, retrieval, and distillation. Integration-specific terms should live in adapters and metadata, not in the core data model.
