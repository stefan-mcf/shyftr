# ShyftR plain lifecycle naming review

Date: 2026-05-06
Status: source review / decision capture, not yet canonical implementation

## Context

The current public ShyftR vocabulary uses the power-cell themed lifecycle:

```text
Pulse -> Spark -> Charge -> Coil -> Rail
```

This is distinctive, but several terms require explanation before a reader can understand the memory lifecycle. The main comprehension concern is that terms such as `Rail`, `Charge`, and `Pulse` feel hard to decode without already knowing the system.

A plain-language candidate lifecycle was reviewed:

```text
Evidence -> Candidate -> Memory -> Pattern -> Rule
```

Stefan prefers this raw/plain lifecycle direction.

## Preferred raw lifecycle

```text
Evidence -> Candidate -> Memory -> Pattern -> Rule
```

Suggested meanings:

- **Evidence**: raw experience entering a Cell as append-only proof, such as chat, task result, closeout, issue, document, log, note, or tool run.
- **Candidate**: extracted possible lesson from Evidence; bounded, typed, provenance-linked, and not trusted yet.
- **Memory**: reviewed durable memory promoted from one or more Candidates.
- **Pattern**: distilled recurring lesson, workflow, or heuristic across related Memories.
- **Rule**: high-confidence shared guidance promoted after explicit review.

## Current-to-plain mapping

| Current themed term | Plain candidate | Notes |
| --- | --- | --- |
| Pulse | Evidence | Strong clarity gain; preserves audit/provenance emphasis. |
| Spark | Candidate | Clearer, but less distinctive. `Spark` is one of the stronger themed terms if any are retained. |
| Charge | Memory | Major clarity gain; `Charge` is thematic but ambiguous. |
| Coil | Pattern | Major clarity gain; existing naming source already questioned `Coil` and recommended `Circuit`. |
| Rail | Rule | Major clarity gain; `Rail` is ambiguous without the guardrail metaphor. |

## Related application-loop terms

The raw lifecycle can coexist with these clearer support terms:

- **Cell**: bounded attachable memory unit.
- **Cell Ledger** or **Ledger**: append-only canonical truth inside a Cell.
- **Regulator**: review/policy boundary controlling admission, promotion, retrieval, and export.
- **Grid** or **Index**: rebuildable retrieval/index layer.
- **Pack** or **Context Pack**: bounded memory context supplied to an agent/runtime before work.
- **Feedback**: record after a Pack is used; tells ShyftR whether retrieved memory helped or harmed.
- **Decay**: confidence reduction caused by staleness, failed reuse, contradiction, supersession, or weak evidence.
- **Quarantine**: isolation for unsafe or conflicting memory.

## Capitalization recommendation

Use lowercase common nouns in normal prose and reserve title case for headings, diagrams, UI labels, table headers, and formal glossary entries.

Recommended prose style:

```text
Evidence enters the cell. A candidate is reviewed into memory. Related memories can form a pattern. A high-confidence pattern can become a rule.
```

Avoid treating every lifecycle noun as a proper noun in sentences:

```text
Evidence enters the Cell. A Candidate is reviewed into Memory. Related Memories can form a Pattern. A high-confidence Pattern can become a Rule.
```

That style reads more like fantasy/system lore than professional technical documentation. The terms should be canonical concepts, not branded proper names in every sentence.

Acceptable capitalization:

- `Evidence -> Candidate -> Memory -> Pattern -> Rule` in lifecycle diagrams.
- `Evidence`, `Candidate`, `Memory`, `Pattern`, and `Rule` as glossary/table labels.
- lowercase `evidence`, `candidate`, `memory`, `pattern`, and `rule` in normal explanatory prose.
- lowercase support terms in prose: `cell`, `ledger`, `regulator`, `grid`, `pack`, `feedback`, `decay`, `quarantine`.
- preserve exact product/package names: `ShyftR`, CLI `shyftr`, class/type/API names where code requires capitalization.

This follows the usual professional documentation convention: capitalize product names, headings, UI labels, formal schema/type names, and sentence starts; otherwise use lowercase for domain nouns.

## Recommended migration posture

Treat this as a deep canonical rename, not a simple prose edit.

If adopted, migrate in layers:

1. Decide whether the public canonical lifecycle becomes exactly:

   ```text
   Evidence -> Candidate -> Memory -> Pattern -> Rule
   ```

2. Decide whether support terms also become plainer:

   ```text
   Signal -> Feedback
   Isolation -> Quarantine
   Grid -> Index, optional
   Pack -> Context Pack, optional
   ```

3. Update public docs first, especially:
   - `README.md`
   - `docs/concepts/power-vocabulary.md` or replacement concept document
   - `docs/concepts/cells.md`
   - `docs/concepts/storage-retrieval-learning.md`
   - runtime integration and API docs

4. Then update code/API compatibility deliberately:
   - CLI commands and help text
   - JSON field names and ledgers
   - examples and fixtures
   - tests
   - backward-compatible aliases/read paths

5. Keep a migration/compatibility document so existing themed names can be understood by older tests, docs, or user data.

## Caution

The plain lifecycle is much easier to comprehend, but it reduces some of the distinctive battery/power-cell flavor. A balanced alternative would keep `Cell`, `Ledger`, `Regulator`, `Grid`, and `Pack`, while making the lifecycle plain:

```text
Evidence -> Candidate -> Memory -> Pattern -> Rule
```

That version likely gives the best clarity/brand tradeoff.
