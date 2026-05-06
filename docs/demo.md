# ShyftR Local Demo

This guide walks through the complete ShyftR memory lifecycle from Pulse
capture through Signal recording. All commands run locally — no network,
no API keys, no external services needed.

ShyftR uses append-only JSONL ledgers as canonical truth. Indexes and
search are rebuildable acceleration layers on top of that truth.

---

## Prerequisites

Python 3.11+ and ShyftR installed (see README for setup).

---

## 1. Create a Cell

A Cell is an attachable memory namespace. Create one with:

```bash
shyftr init-cell ./demo-cell
```

This creates the directory layout: `config/`, `ledger/`, `grid/`, and
empty JSONL ledgers for Pulses, Sparks, Charges, Coils, Rails,
Packs, and Signal.

---

## 2. Ingest a Pulse

A Pulse is raw evidence — a file, a log, a chat transcript. Ingest it:

```bash
shyftr ingest ./demo-cell examples/pulse.md --kind lesson
```

The ingester computes a SHA-256 fingerprint, returns a current `source_id`, and
appends a Pulse record to `ledger/pulses.jsonl`.

---

## 3. Extract Sparks

Sparks are bounded, typed pieces extracted from a Pulse:

```bash
shyftr sparks ./demo-cell <source_id>
```

This reads the Pulse record, parses the file into candidate memory
pieces (Sparks), and appends them to `ledger/sparks.jsonl`.

---

## 4. Approve Sparks

Review each Spark and approve it for promotion:

```bash
shyftr approve ./demo-cell <spark_id> --reviewer demo --rationale "Accurate and relevant lesson"
```

Approved Sparks remain in `ledger/sparks.jsonl` with
`review_status: approved`.

---

## 5. Promote to Charge

Promote an approved Spark into a durable Charge:

```bash
shyftr charge ./demo-cell <spark_id> --promoter demo --rationale "Regulator-scoping pattern confirmed"
```

The promotion creates a Charge record in `charges/approved.jsonl` with an
identifier, a `statement`, and provenance back to the original Spark.

---

## 6. Search Approved Charges

The search command rebuilds or queries the sparse FTS5 index:

```bash
shyftr search ./demo-cell "pack confidence"
```

Results include `charge_id` / legacy `charge_id`, `statement`, `confidence`, `bm25_score`,
and tags — useful for verifying what was promoted.

---

## 7. Assemble a Pack

A Pack is a bounded, trust-labeled memory context for a task:

```bash
shyftr pack ./demo-cell "How to improve Pack relevance" --task-id demo-task-001
```

The Pack selects Charges by relevance score and returns a bounded
context with a `trust_label`.

---

## 8. Record Signal

After the task completes, record what happened:

```bash
shyftr signal ./demo-cell <pack_id> success \
  --useful <charge_id_1>,<charge_id_2> \
  --missing "more scope-tagged charges"
```

Signals flow back into the confidence engine, decaying or boosting
Charge confidence based on verified results.

---

## Lifecycle Summary

```
Pulse -> Spark -> Charge -> Pack -> Signal
                 ^                      |
                 |--- confidence loop --|
```

- **Ledgers** (JSONL files under each Cell) are the canonical truth.
- **Indexes** (SQLite FTS5) are rebuildable acceleration.
- **Packs** are the application — bounded memory for a specific task.
- **Signal** are the learning signal — they update Charge confidence.

Run the full demo test suite to verify the local setup:

```bash
python3 -m pytest tests/test_demo_flow.py -v
```
