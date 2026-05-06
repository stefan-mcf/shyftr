# Memory graph and reputation

Status: implemented for local controlled pilots as public-safe frontier foundations.

## Causal memory graph

The memory graph records explicit, reviewed relationships between memory items. It is append-only and rebuildable from `ledger/graph_edges.jsonl`.

Allowed edge types:

- `caused_success`
- `contributed_to_failure`
- `contradicted_by`
- `supersedes`
- `depends_on`
- `applies_under`
- `invalid_under`
- `co_retrieved_with`
- `ignored_with`

Graph edges require provenance and reviewer metadata. The public baseline does not infer hidden causality. pack assembly can display graph context as explainability metadata, but graph context does not silently promote, import, approve, or mutate memory.

## Reputation baseline

Reputation tracks reliability observations about evidence origins, agents, reviewers, cells, runtimes, and imported origins. It is append-only under `ledger/reputation/events.jsonl`.

Public metrics include:

- approval rate;
- rejection rate;
- useful feedback rate;
- harmful feedback rate;
- contradiction rate;
- stale memory rate;
- review priority score.

Reputation can help order review attention. It cannot bypass regulator decisions, auto-approve memory, auto-import federated records, or silently trust an origin.

## Regulator proposals

Regulator proposal helpers can detect repeated synthetic false approval or false rejection events and create review-gated proposals. A proposal contains:

- proposal id;
- impacted area;
- examples;
- counterexamples;
- rationale;
- required simulation report reference;
- reviewer decision state.

Approving a proposal requires a simulation reference and records a review event. Approval does not mutate policy automatically.

## CLI examples

```bash
python -m shyftr.cli graph <cell>
python -m shyftr.cli reputation <cell>
python -m shyftr.cli regulator-proposals <cell>
```

## Guardrails

- Ledgers are canonical truth and remain append-only.
- Imported or federated records never become local truth without review.
- Reputation is advisory only.
- regulator proposals require human review and simulation before any future policy change.
