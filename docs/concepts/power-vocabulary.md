# Power Vocabulary

ShyftR uses a power-cell vocabulary for its durable memory architecture. The terms keep the system concrete: cells store reviewed memory, regulators control what becomes authoritative, and packs deliver bounded energy to agents before work.

## Formal vocabulary

- **cell**: attachable memory/power unit.
- **evidence**: raw experience entering a cell as append-only evidence.
- **candidate**: extracted candidate lesson from a evidence.
- **memory**: reviewed durable memory.
- **pattern**: distilled pattern from multiple memories.
- **rule**: high-confidence multi-cell rule.
- **grid**: rebuildable retrieval/index layer.
- **pack**: bounded memory bundle supplied to an agent or runtime.
- **feedback**: evidenceback after a pack is used.
- **regulator**: review/policy regulator controlling admission, promotion, retrieval, and export.
- **Decay**: confidence decay.
- **quarantine**: quarantine for unsafe, conflicting, harmful, or untrusted memory.

## Lifecycle

```text
candidate -> memory -> pattern -> rule
```

A evidence is preserved as evidence. When a evidence reveals a reusable lesson, it becomes a candidate checked by the regulator. Approved candidates become memories. Related memories can be distilled into patterns. patterns that prove broadly useful can be promoted onto rules.

## Application loop

```text
grid builds from cell ledgers.
Agent receives a pack.
Agent reports feedback.
feedbacks raise confidence, trigger decay, or isolate memories.
```

The cell ledger remains canonical truth. The grid is rebuildable acceleration. The pack is application. feedback is learning. memory confidence is evolution.
