# ShyftR Sample evidence: pack confidence Heuristic

Evidence ID: `src-demo-pack-confidence`
Kind: `lesson`
Captured: `2026-04-24T18:00:00Z`

## Observation

During an AI agent's task, a pack was assembled with 12 memories from the
development cell. The agent completed the task successfully but reported that
two memories in the pack were irrelevant — they matched the query keywords
but described a different programming language runtime.

## Durable Lesson

A keyword-only search produces false positives when memory statements lack
contextual scoping. pack quality improves when:

- Each memory includes a scope tag (e.g., `lang:python`, `domain:testing`)
- The pack query specifies expected scope via `--query-tags`
- candidates are reviewed for regulator clarity before promotion to memory

## Resulting feedback

The feedback recorded two `harmful_memory_ids` and noted `missing_memory`
entries for better-scoped alternatives. memory confidence decayed for the
misleading entries, and the user added a more specific scope evidence.

This is the ShyftR learning loop in action: evidence -> candidate -> memory ->
pack -> feedback -> confidence adjustment -> improved future packs.
