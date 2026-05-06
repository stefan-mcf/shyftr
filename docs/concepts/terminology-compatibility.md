# Terminology compatibility

ShyftR's canonical public lifecycle is now:

```text
evidence -> candidate -> memory -> pattern -> rule
```

Normal prose should use lowercase common nouns: evidence, candidate, memory, pattern, rule, cell, ledger, regulator, grid, pack, feedback, decay, and quarantine.

## Compatibility policy

The plain-language names are canonical for new docs, examples, CLI output, and public contracts. Deprecated legacy and themed names remain readable where existing users or cells may still contain them.

Compatibility aliases are kept for:

- model imports;
- JSON field reads;
- existing ledger file reads;
- deprecated CLI commands;
- deprecated integration route or payload names;
- old distillation module imports.

New writes should emit canonical names unless an explicit compatibility export mode is added later.

## Lifecycle aliases

| Deprecated name | Canonical name | Notes |
| --- | --- | --- |
| Pulse / Source / Feed | Evidence | Raw or imported experience in the cell ledger. |
| Spark / Fragment | Candidate | Extracted proposal that still needs review. |
| Charge / Trace | Memory | Reviewed durable memory. |
| Coil / Alloy / Circuit | Pattern | Distilled recurring structure across memories. |
| Rail / Doctrine | Rule | Shared high-confidence reviewed rule. |

## Support aliases

| Deprecated name | Canonical name | Notes |
| --- | --- | --- |
| Loadout | Pack | Context supplied to an attached agent or runtime. |
| Outcome / Signal | Feedback | Report of whether supplied context helped or harmed. |
| Isolation | Quarantine | Safety state for conflicting or unsafe memory. |

## Field aliases

Canonical serializers emit canonical fields. Deserializers accept these old fields for compatibility:

| Deprecated field | Canonical field |
| --- | --- |
| `source_id` | `evidence_id` |
| `fragment_id` | `candidate_id` |
| `trace_id` | `memory_id` |
| `alloy_id` | `pattern_id` |
| `doctrine_id` | `rule_id` |
| `loadout_id` | `pack_id` |
| `outcome_id` | `feedback_id` |
| `source_fragment_ids` | `candidate_ids` |
| `source_trace_ids` | `memory_ids` |
| `source_alloy_ids` | `pattern_ids` |

## Human-gated removal

Do not delete compatibility aliases or stop reading legacy fields without explicit human approval and a documented migration path for existing cells.
