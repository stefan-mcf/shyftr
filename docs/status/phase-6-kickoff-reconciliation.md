# Phase 6 kickoff reconciliation

Phase 6 starts from the existing public implementation without deleting compatibility readers or pretending that older internal names are the public model. This file is the handoff map for implementing explicit, review-gated multi-cell behavior.

## Compatibility-to-public surface map

| Existing compatibility surface | Public Phase 6 meaning | Public write/read target | Compatibility note |
| --- | --- | --- | --- |
| `Fragment` | candidate extracted from evidence | `ledger/candidates.jsonl` and existing `ledger/fragments.jsonl` readers | Keep compatibility constructors and readers so old cells can still load. |
| `Trace` | memory | preferred `ledger/memories/approved.jsonl`; compatibility `traces/approved.jsonl` remains readable | New multi-cell code may read both, but local cell ledgers remain authoritative only for their own cell. |
| `Alloy` | pattern | preferred `ledger/patterns/proposed.jsonl` and `ledger/patterns/approved.jsonl`; compatibility `alloys/*.jsonl` remains readable | Pattern resonance can use public `Pattern` records and compatibility records. |
| `DoctrineProposal` | rule proposal | preferred `ledger/rules/proposed.jsonl` and `ledger/rules/approved.jsonl`; compatibility `doctrine/*.jsonl` remains readable | Shared rules require explicit review before pack inclusion. |
| `Loadout` | pack | `ledger/packs.jsonl` and `ledger/retrieval_logs.jsonl` | Pack assembly remains single-cell by default. |
| `Outcome` | feedback | `ledger/feedback.jsonl` plus compatibility `ledger/outcomes.jsonl` | Feedback can inform later ranking but does not silently mutate shared rules. |

## Public ledger write targets

Phase 6 uses these public ledgers:

- patterns: `ledger/patterns/proposed.jsonl`, `ledger/patterns/approved.jsonl`;
- rules: `ledger/rules/proposed.jsonl`, `ledger/rules/approved.jsonl`;
- registry: `ledger/cell_registry.jsonl` or an explicit `.jsonl` registry path;
- federation: `ledger/federation_events.jsonl`, `ledger/import_candidates.jsonl`, and `ledger/import_reviews.jsonl`.

## Implementation boundary

Phase 6 implementation must add or use public model surfaces without deleting compatibility readers. Cross-cell behavior must stay explicit, provenance-linked, scoped, and review-gated. No resonance scan, import, or rule proposal is allowed to rewrite source cell ledgers silently.

This reconciliation note was created before Phase 6 code changes. It does not claim hosted behavior or Phase 7 functionality.
