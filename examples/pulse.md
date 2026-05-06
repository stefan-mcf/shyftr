# ShyftR Sample Pulse: Pack Confidence Heuristic

Pulse ID: `src-demo-pack-confidence`
Kind: `lesson`
Captured: `2026-04-24T18:00:00Z`

## Observation

During an AI agent's task, a Pack was assembled with 12 Charges from the
development Cell. The agent completed the task successfully but reported that
two Charges in the Pack were irrelevant — they matched the query keywords
but described a different programming language runtime.

## Durable Lesson

A keyword-only search produces false positives when Charge statements lack
contextual scoping. Pack quality improves when:

- Each Charge includes a scope tag (e.g., `lang:python`, `domain:testing`)
- The Pack query specifies expected scope via `--query-tags`
- Sparks are reviewed for regulator clarity before promotion to Charge

## Resulting Signal

The Signal recorded two `harmful_charge_ids` and noted `missing_memory`
entries for better-scoped alternatives. Charge confidence decayed for the
misleading entries, and the user added a more specific Scope Pulse.

This is the ShyftR learning loop in action: Pulse -> Spark -> Charge ->
Pack -> Signal -> confidence adjustment -> improved future Packs.
