# memory cells

ShyftR's primary abstraction is a cell.

A cell is an isolated, attachable, durable memory namespace with its own cell ledger, regulator, reviewed memories, grid, reports, and policy. A cell can attach to a person, assistant, agent, project, team, organization, application, domain, capability, or global rule layer.

Canonical system vocabulary:

- ShyftR cell: a bounded attachable memory unit.
- regulator: the review and policy layer controlling admission, promotion, retrieval, and export.
- cell ledger: the append-only canonical truth inside a cell.
- memory: a reviewed durable memory item.
- grid: the rebuildable retrieval and index layer.
- pack: the bounded memory bundle supplied to an agent or runtime.
- feedback: the evidenceback record that tells ShyftR whether retrieved memory helped or harmed.

The regulator remains separate from durable truth storage. It is the cell-local scope and policy surface implemented by admission checks, review gates, trust-tier filtering, retrieval limits, and export rules.

## Why cell?

ShyftR is an attachable memory module. A cell can be slotted into an agent, project, team, tool, or domain so reviewed experience can shift future behavior.

## Common cell types

- `core`: default user or deployment memory
- `personal`: personal assistant memory
- `agent`: one autonomous agent's durable learning
- `project`: project-local knowledge and heuristics
- `team`: shared team memory
- `organization`: organization-wide rule
- `application`: app-specific memory
- `domain`: domain or capability memory
- `global-rule`: multi-cell promoted rule

## Default memory

A user's default memory can be represented as a `core` cell.

Example:

```text
cells/core/memory/
  ledger/
  memories/
  grid/
  summaries/
  reports/
  config/
```

This lets ShyftR handle ordinary assistant memory while using the same review, promotion, retrieval, and recursive distillation machinery as project, team, agent, and domain cells.

## Lifecycle

Core ShyftR code should depend on the portable lifecycle:

```text
candidate -> memory -> pattern -> rule
```

- evidence: raw evidence preserved append-only before lifecycle promotion.
- candidate: bounded candidate memory piece extracted from a evidence.
- memory: reviewed durable memory.
- pattern: recursive pattern distilled from related memories.
- rule: shared promoted rule.

## rule

Core ShyftR code should depend on cells, the cell ledger, the regulator, evidences, candidates, memories, patterns, rules, the grid, packs, feedback, retrieval, and distillation. Integration-specific terms should live in adapters and metadata, not in the core data model.
