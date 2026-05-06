# Knowledge Workspace Contract

This contract defines how ShyftR works as the durable substrate beneath note, document, research, and project-knowledge workflows. It is category-level and workspace-neutral. Editors, folders, document stores, and dashboards can remain human-facing surfaces while ShyftR Cells hold canonical memory truth.

## Contract principles

- Notes and documents enter ShyftR as Pulses or synchronized evidence.
- Durable claims, decisions, preferences, workflows, and lessons become reviewed Charges.
- Backlinks, topic pages, project pages, summaries, and markdown exports are projections over ledgers.
- Review queues use Regulator state to decide what becomes durable memory.
- Workspace sync must preserve provenance and source identity.
- Generated markdown should be rebuildable from Cell ledgers.

## Compatibility surface

### Note ingest

Purpose: capture note content as memory evidence.

Expected inputs:

- source workspace category
- note identifier and stable path or URI
- title, body, frontmatter, tags, timestamps, and author when available
- optional project, topic, and sensitivity metadata
- content hash for idempotency

ShyftR behavior:

1. Record the note as a Pulse with source metadata.
2. Extract Sparks for durable claims, decisions, preferences, procedures, and lessons.
3. Preserve raw-note provenance and source hashes.
4. Route extracted Sparks through review before Charge promotion unless import policy allows a trusted path.

Note text remains evidence. Reviewed memory comes from ledgers.

### Note sync

Purpose: keep a Cell aware of changed notes without duplicating evidence or overwriting memory state.

Expected inputs:

- source note IDs
- current content hashes
- sync cursor or timestamp
- deleted, moved, renamed, or edited status
- conflict policy

ShyftR behavior:

1. Compare source hashes and cursors against sync state.
2. Append new Pulses for meaningful revisions.
3. Record move, rename, deletion, and conflict events as evidence.
4. Keep previous evidence available for audit and supersession review.
5. Avoid mutating approved Charges directly from note edits.

A note edit can propose a replacement or deprecation, but ledger authority remains append-only and review-gated.

### Document ingest

Purpose: ingest documents, reports, PDFs, research files, transcripts, or exported artifacts as evidence.

Expected inputs:

- document identifier and source metadata
- extracted text or structured sections
- file hash and parser metadata
- citation, author, date, and project/topic tags when available
- optional chunking strategy

ShyftR behavior:

1. Record document-level Pulses and section-level evidence as needed.
2. Preserve extraction metadata and source hashes.
3. Extract Sparks with citations or section references.
4. Route high-authority claims through review before Charge promotion.

Document stores provide source material. ShyftR owns reviewed memory derived from that material.

### Backlinks

Purpose: represent relationships between notes, documents, topics, projects, Charges, Coils, and Rails.

Expected inputs:

- source and target identifiers
- relationship type
- source workspace reference
- optional anchor text or section location

ShyftR behavior:

1. Capture link relationships as Pulse evidence or projection metadata.
2. Materialize backlink views from ledgers and source metadata.
3. Support topic and project projections that include linked evidence and reviewed memory.
4. Keep link graphs rebuildable.

Backlinks are discovery and projection aids rather than canonical memory by themselves.

### Topic and project projections

Purpose: generate durable knowledge views for a topic, project, domain, or workstream.

Expected inputs:

- topic or project identifier
- Cell scope
- filters for kinds, trust tiers, time ranges, tags, source categories, or review state
- output format and budget

ShyftR behavior:

1. Select reviewed Charges, Coils, Rails, and linked evidence.
2. Include provenance and confidence labels.
3. Identify open Sparks, conflicts, outdated material, and review needs.
4. Render deterministic markdown or JSON projections.
5. Treat generated pages as rebuildable outputs.

Topic pages and project pages should help humans work with memory without becoming the memory authority.

### Review queue

Purpose: surface Sparks, conflicts, deprecations, replacements, imports, and workspace-derived proposals for human or policy review.

Expected inputs:

- Cell scope
- proposal types
- priority rules
- reviewer identity or policy context
- source category filters

ShyftR behavior:

1. Gather pending Sparks and lifecycle proposals from ledgers.
2. Rank review items by confidence, impact, recency, conflict, sensitivity, and source quality.
3. Record approve, reject, defer, isolate, deprecate, or supersede decisions as append-only review events.
4. Preserve reviewer identity, reason, and evidence.

The review queue is a Regulator surface over ledger state.

### Markdown export

Purpose: emit portable human-readable knowledge views.

Expected inputs:

- Cell scope or projection target
- export template or projection type
- sensitivity policy
- destination path or package format
- optional backlink and frontmatter settings

ShyftR behavior:

1. Render markdown from ledger-backed memory and source references.
2. Include stable ShyftR IDs, confidence labels, status, and provenance when policy allows.
3. Exclude forgotten, sensitive, isolated, or deprecated memory by default.
4. Include export metadata and source ledger hashes.
5. Allow exports to be regenerated from ledgers.

Markdown export is a projection and portability surface. The Cell ledger remains canonical.

## Category capability mapping

| Workspace-category capability | ShyftR-native equivalent | Canonical truth |
|---|---|---|
| Capture a note | Note ingest as Pulse evidence | Cell ledgers |
| Keep notes in sync | Note sync cursors and revision Pulses | Cell ledgers plus sync state |
| Capture documents | Document ingest as Pulses and cited Sparks | Cell ledgers |
| Navigate links | Backlink projections from source metadata and ledgers | Rebuildable projection |
| Build a topic page | Topic projection from reviewed memory and evidence | Cell ledgers |
| Build a project page | Project projection from reviewed memory and evidence | Cell ledgers |
| Review pending knowledge | Regulator review queue | Review ledgers |
| Export notes or pages | Markdown export | Rebuildable projection |

## Sync and projection boundaries

Workspace adapters should avoid writing directly to approved memory ledgers. Their job is to capture source evidence, maintain sync cursors, preserve hashes, and propose memory changes. The Regulator decides which extracted Sparks become Charges and which lifecycle changes gain authority.

Generated workspace outputs may include:

- topic pages
- project pages
- decision records
- Rail pages
- profile summaries
- research digests
- review bundles
- export packages

All of these outputs are applications or projections. They can be useful, editable, and portable, but they should point back to Cell ledger IDs for durable authority.

## Workspace compatibility notes

Workspace integrations should keep product-specific mapping inside adapters. Public ShyftR contracts should describe broad categories such as markdown workspace, document repository, note editor, research library, review surface, or dashboard.

The substrate goal is portability: a Cell should outlive any single editor, folder layout, hosted workspace, retrieval backend, or dashboard. The ledgers carry memory truth; workspace surfaces make that truth usable.
