# Confidence, simulation, and retrieval modes

Status: implemented for local controlled pilots as public-safe frontier foundations.

## Confidence belief baseline

ShyftR keeps the legacy scalar `confidence` field for compatibility. Frontier foundations add additive belief metadata that explains how much evidence supports that scalar:

- `prior`
- `positive_evidence_count`
- `negative_evidence_count`
- `expected_confidence`
- `uncertainty`
- `lower_bound`
- `upper_bound`
- `evidence_count`

The public baseline is a transparent beta-binomial-style projection. It is deterministic, inspectable, and boring by design. Learned calibration, private evaluator data, and proprietary ranking are reserved for private-core work.

New memory with little evidence can have a reasonable expected confidence while still showing high uncertainty. Positive feedback increases expected confidence and lowers uncertainty. Negative feedback lowers expected confidence while preserving auditability.

## Read-only policy simulation

Policy simulation lets an operator compare current pack behavior with proposed retrieval settings before applying anything. A simulation report includes:

- selected IDs;
- missed IDs;
- added IDs;
- changed order;
- caution labels;
- estimated token usage;
- ledger line counts before and after the simulation.

Simulation uses dry-run pack assembly and does not append production retrieval logs. Any future policy application requires explicit operator review.

## Retrieval modes

Retrieval modes make pack behavior explicit for different mission-risk profiles:

| Mode | Intent |
| --- | --- |
| `balanced` | default-compatible pack behavior. |
| `conservative` | prefer established reviewed memory. |
| `exploratory` | include more candidate/background context with labels. |
| `risk_averse` | exclude weak memory and surface more cautions. |
| `audit` | include challenged or quarantined records only with audit labels. |
| `rule_only` | return rules without ordinary memory. |
| `low_latency` | cap the pack for a smaller fast response. |

Mode settings are transparent public configuration. The default remains compatible unless a request explicitly opts into a different mode.

## CLI examples

```bash
python -m shyftr.cli pack <cell> "deployment checklist" --task-id demo --retrieval-mode conservative
python -m shyftr.cli simulate <cell> "deployment checklist" --current-mode balanced --proposed-mode risk_averse
```

## Guardrails

- Scalar `confidence` remains readable and serializable.
- Simulation is read-only by default.
- Retrieval modes do not bypass regulator, sensitivity, or lifecycle gates.
- Public mode settings do not include private scoring or ranking algorithms.
