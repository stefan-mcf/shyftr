# Memory Provider Contract

This contract defines how ShyftR presents a local-first memory-provider surface to assistant runtimes and automation tools. The contract is category-level and provider-neutral. It captures the durable memory responsibilities commonly expected from assistant-memory layers while preserving ShyftR's Cell ledger truth model.

## Contract principles

- Cell ledgers are canonical truth for every memory write, mutation, review event, and Signal.
- The Regulator controls admission, promotion, retrieval, mutation, and export.
- Search uses the Grid as rebuildable acceleration over ledger-backed Charges, Coils, Rails, and evidence.
- Profiles are projections generated from reviewed memory.
- Packs are bounded applications of memory for a task or runtime context.
- Importers convert provider exports into Pulses with provenance before promotion.
- Exports produce snapshots or projection artifacts without transferring canonical authority away from the Cell ledger.

## Compatibility surface

### `remember`

Purpose: add explicit durable memory material.

Expected inputs:

- target Cell
- memory statement or structured fact
- kind such as preference, constraint, workflow, tool quirk, identity fact, project vocabulary, or safety boundary
- actor and source context
- optional sensitivity, scope, and review policy metadata

ShyftR behavior:

1. Record a Pulse or accepted trusted-memory event.
2. Apply Regulator checks for scope, sensitivity, pollution, duplication, and policy.
3. Create a Spark or, when policy allows, a reviewed Charge with full provenance.
4. Preserve review and promotion evidence in append-only ledgers.

Output should include a stable ShyftR identifier, review state, provenance pointers, and any Regulator warnings.

### `search`

Purpose: retrieve durable memory relevant to a query, task, profile section, or runtime context.

Expected inputs:

- target Cell or Cell scope set
- query text or structured query
- optional trust tiers, kinds, status filters, sensitivity filters, and result limit
- optional task or runtime context for scoring

ShyftR behavior:

1. Query the Grid and ledger-derived metadata.
2. Apply status, sensitivity, scope, confidence, and trust filters.
3. Return labeled results with Charge, Coil, Rail, Spark, or Pulse provenance.
4. Record retrieval logs when the search contributes to a Pack or task.

Results must identify trust tier, confidence, lifecycle status, source IDs, and selection rationale.

### `profile`

Purpose: build a compact assistant profile from reviewed memory.

Expected inputs:

- target Cell or Cell scope set
- optional section filters
- token or character budget
- target runtime constraints

ShyftR behavior:

1. Select reviewed Charges, Coils, and Rails that belong in stable profile material.
2. Exclude deprecated, superseded, isolated, or sensitivity-excluded memory by default.
3. Render deterministic profile sections with provenance references.
4. Preserve the profile as a rebuildable projection.

Profiles must never become canonical truth. The Cell ledger remains the source.

### `forget`

Purpose: remove memory from normal retrieval and profile projections while preserving auditability.

Expected inputs:

- memory ID or query-resolved target
- actor
- reason
- optional scope and effective policy

ShyftR behavior:

1. Append a lifecycle or redaction/exclusion event.
2. Exclude the affected memory from normal search, Pack assembly, and profile generation.
3. Preserve enough ledger metadata for audit, conflict handling, backup validation, and lawful export policies.

Forget is implemented through append-only exclusion semantics, not silent ledger rewriting.

### `replace`

Purpose: supersede one memory with a corrected or more current memory.

Expected inputs:

- source memory ID
- replacement statement or structured fact
- actor and reason
- optional review policy metadata

ShyftR behavior:

1. Record the replacement material as new evidence.
2. Promote the replacement through the Regulator.
3. Append a supersession event linking old and new memory.
4. Exclude superseded memory from normal Pack/profile output unless explicitly requested.

### `deprecate`

Purpose: reduce or remove authority from memory that has aged, failed, conflicted, or become less useful.

Expected inputs:

- memory ID or target set
- actor or automated proposal source
- reason and evidence
- optional severity and review state

ShyftR behavior:

1. Append a deprecation proposal or approved deprecation event.
2. Adjust retrieval and Pack eligibility according to policy.
3. Preserve the memory, reason, and evidence for audit and future review.

Destructive deprecation should remain review-gated.

### `pack`

Purpose: provide bounded task-ready memory context to an assistant runtime.

Expected inputs:

- target Cell or Cell scope set
- task description or structured task context
- runtime identity and scope
- optional token budget, trust tiers, roles, and sensitivity rules

ShyftR behavior:

1. Retrieve and rank relevant memory.
2. Apply Regulator limits for trust, sensitivity, scope, lifecycle status, and export policy.
3. Produce role-labeled guidance, caution, background, and conflict items.
4. Record retrieval logs and Pack identifiers for later Signal.

The Pack is an application artifact. The ledger remains canonical.

### `record_signal`

Purpose: record whether memory helped, harmed, was ignored, or was missing after use.

Expected inputs:

- Pack ID or retrieval log reference
- runtime/task identifiers
- useful, harmful, ignored, violated, or missing memory details
- verification evidence
- result status

ShyftR behavior:

1. Append Signal and related confidence events.
2. Update confidence projections from append-only ledgers.
3. Preserve Pack miss details and evidence for Sweep, Challenger, and review workflows.
4. Avoid lowering global confidence from a single ambiguous miss without corroborating evidence.

Signal drives learning but does not rewrite memory history.

### `import_memory_export`

Purpose: ingest an exported memory set from another provider category.

Expected inputs:

- export artifact or parsed records
- source category and provenance metadata
- target Cell
- import policy and review mode

ShyftR behavior:

1. Treat every imported item as Pulse evidence with source provenance.
2. Normalize fields into ShyftR kinds, scopes, timestamps, and sensitivity metadata.
3. Detect duplicates and conflicts before promotion.
4. Require review or configured trusted-import policy before imported material becomes durable Charges.
5. Preserve an import manifest with counts, rejected rows, warnings, and source hashes.

Imports are migration Sources, not direct canonical replacements.

### `export_memory_snapshot`

Purpose: produce portable memory output for backup, audit, runtime injection, or migration.

Expected inputs:

- target Cell or Cell scope set
- requested projection type
- sensitivity and redaction policy
- format such as JSONL, JSON, or markdown

ShyftR behavior:

1. Export ledger-backed records or projection artifacts according to policy.
2. Include provenance, lifecycle status, confidence, and source references when allowed.
3. Exclude sensitive, forgotten, deprecated, or isolated items by default unless an audit policy explicitly includes them.
4. Include snapshot metadata, schema version, and source ledger hashes.

Snapshots are portable artifacts. The source Cell ledger remains authoritative.

## Category capability mapping

| Provider-category capability | ShyftR contract operation | ShyftR-native authority |
|---|---|---|
| Store a user preference | `remember` | Pulse/Spark/Charge ledgers |
| Search memories | `search` | Grid over Cell ledgers |
| Generate assistant profile | `profile` | Profile projection from reviewed memory |
| Supply task context | `pack` | Pack projection plus retrieval logs |
| Record usefulness | `record_signal` | Signal and confidence ledgers |
| Forget memory | `forget` | Lifecycle/redaction/exclusion ledgers |
| Correct memory | `replace` | Supersession ledgers plus new Charge |
| Age out weak memory | `deprecate` | Deprecation events and review state |
| Migrate from an export | `import_memory_export` | Imported Pulses with provenance |
| Create a backup or migration artifact | `export_memory_snapshot` | Policy-bound snapshot projection |

## Implementation status

Current implementation status after UMS-2:

- `shyftr.provider.MemoryProvider` provides a Cell-bound facade for the implemented memory-provider surface.
- `remember(cell_path, statement, kind, pulse_context=None, metadata=None)` writes explicit memory through the Regulator and records a Pulse, Spark review, promotion event, and Charge with provenance.
- `remember_trusted(cell_path, statement, kind, actor, trust_reason, pulse_channel, created_at, trusted_direct_promotion=True, metadata=None)` is the hardened trusted explicit-memory path. It requires actor, trust reason, Pulse channel, and creation time before any ledger write.
- `TrustedMemoryProvider(cell_path, actor, pulse_channel)` wraps the same trusted path for Cell-bound runtime use.
- Trusted kinds are intentionally narrow: `preference`, `constraint`, `workflow`, and `tool_quirk`. Unsupported kinds fail before ledger writes.
- Trusted writes still pass Regulator pollution checks. Operational state, branch/worktree details, artifact paths, queue status, and unverified completion claims are rejected before admission.
- When trusted direct promotion is enabled, the trusted path still records Source/Pulse evidence, a Fragment/Spark, review metadata, a promotion event, and an approved Charge/Trace. It does not write Charges directly.
- When trusted direct promotion is disabled, ShyftR captures the Source/Pulse and pending Fragment/Spark evidence without creating a review, promotion event, or approved Charge automatically.
- `search(cell_path, query, top_k=10, trust_tiers=None, kinds=None)` reads approved Charge rows, collapses append-only ledger updates to the latest row per Charge ID, excludes user-facing forgotten or replaced Charges, and returns trust tier, Charge ID, confidence, lifecycle status, selection rationale, and provenance.
- `profile(cell_path, max_tokens=2000)` returns a compact markdown profile projection with source Charge IDs. It is a rebuildable projection, not canonical truth.
- `forget(cell_path, charge_id, reason, actor)`, `replace(cell_path, charge_id, new_statement, reason, actor)`, and `deprecate(cell_path, charge_id, reason, actor)` append provider lifecycle events. `forget` and `replace` exclude affected Charges from normal provider search/profile reads; broader lifecycle ledgers remain planned for UMS-4.

Current boundaries:

- UMS-1 covers the direct provider API and local lexical search/profile projection path.
- UMS-2 covers the trusted explicit-memory path, required metadata, narrow trusted kinds, Regulator pollution protection, and the direct-promotion disable switch.
- `pack`, `record_signal`, `import_memory_export`, and `export_memory_snapshot` remain contract items for later tranches.
- Lifecycle semantics are provider-local until UMS-4 adds broader status, supersession, deprecation, Isolation, conflict, and redaction event models.
- Provider outputs remain ShyftR-native and category-level; adapters can map external categories into this surface without making any external provider canonical.

## Runtime compatibility notes

Assistant runtimes integrating with this contract should send explicit source identity, task identity, actor identity, and scope. They should treat ShyftR IDs as stable references and report Signal after using Packs. They should avoid treating profile text as the source of truth; profiles should be regenerated when relevant ledger state changes.

The contract deliberately avoids product-specific field names. Adapters can map named provider exports into this contract, but the public ShyftR surface stays ShyftR-native.
