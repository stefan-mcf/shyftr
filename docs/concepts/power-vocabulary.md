# Power Vocabulary

ShyftR uses a power-cell vocabulary for its durable memory architecture. The terms keep the system concrete: Cells store reviewed charge, Regulators control what becomes authoritative, and Packs deliver bounded energy to agents before work.

## Formal vocabulary

- **Cell**: attachable memory/power unit.
- **Pulse**: raw experience entering a Cell as append-only evidence.
- **Spark**: extracted candidate lesson from a Pulse.
- **Charge**: reviewed durable memory.
- **Coil**: distilled pattern from multiple Charges.
- **Rail**: high-confidence multi-Cell rule.
- **Grid**: rebuildable retrieval/index layer.
- **Pack**: bounded memory bundle supplied to an agent or runtime.
- **Signal**: pulseback after a Pack is used.
- **Regulator**: review/policy regulator controlling admission, promotion, retrieval, and export.
- **Decay**: confidence decay.
- **Isolation**: Isolation for unsafe, conflicting, harmful, or untrusted memory.

## Lifecycle

```text
Spark -> Charge -> Coil -> Rail
```

A Pulse is preserved as evidence. When a Pulse reveals a reusable lesson, it becomes a Spark checked by the Regulator. Approved Sparks become Charges. Related Charges can be distilled into Coils. Coils that prove broadly useful can be promoted onto Rails.

## Application loop

```text
Grid builds from Cell ledgers.
Agent receives a Pack.
Agent reports Signal.
Signals raise confidence, trigger decay, or isolate Charges.
```

The Cell Ledger remains canonical truth. The Grid is rebuildable acceleration. The Pack is application. Signal is learning. Charge confidence is evolution.
