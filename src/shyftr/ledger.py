from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterator, Tuple, Union

PathLike = Union[str, Path]
JsonRecord = Dict[str, Any]


def append_jsonl(path: PathLike, record: JsonRecord) -> None:
    """Append one deterministic JSON object to a JSONL ledger.

    Every newly appended row carries a tamper-evident hash-chain envelope. The
    chain fields are stored in the row, while ``read_jsonl`` hides them from
    legacy consumers so existing model parsers keep their stable schemas.
    """
    ledger_path = Path(path)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(record)
    previous_hash = _last_row_hash(ledger_path)
    payload_without_chain = {k: v for k, v in payload.items() if k not in {"row_hash", "previous_row_hash"}}
    canonical = json.dumps(payload_without_chain, sort_keys=True, separators=(",", ":"))
    row_hash = hashlib.sha256(previous_hash.encode("utf-8") + b"\0" + canonical.encode("utf-8")).hexdigest()
    payload.update({"previous_row_hash": previous_hash, "row_hash": row_hash})
    line = json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
    with ledger_path.open("a", encoding="utf-8") as ledger_file:
        ledger_file.write(line)
        ledger_file.flush()
        os.fsync(ledger_file.fileno())


def _last_row_hash(path: Path) -> str:
    if not path.exists():
        return ""
    last = ""
    with path.open("r", encoding="utf-8") as ledger_file:
        for line in ledger_file:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                row = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            embedded = row.get("row_hash")
            if isinstance(embedded, str) and embedded:
                last = embedded
            else:
                payload = {k: v for k, v in row.items() if k not in {"row_hash", "previous_row_hash"}}
                canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
                last = hashlib.sha256(last.encode("utf-8") + b"\0" + canonical.encode("utf-8")).hexdigest()
    return last


def read_jsonl(path: PathLike) -> Iterator[Tuple[int, JsonRecord]]:
    """Yield non-blank JSONL records as (line_number, decoded_record)."""
    ledger_path = Path(path)
    with ledger_path.open("r", encoding="utf-8") as ledger_file:
        for line_number, line in enumerate(ledger_file, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            record = json.loads(stripped)
            record.pop("row_hash", None)
            record.pop("previous_row_hash", None)
            yield line_number, record


def file_sha256(path: PathLike) -> str:
    """Return the SHA256 digest of a file's raw bytes."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as payload_file:
        for chunk in iter(lambda: payload_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


# ---------------------------------------------------------------------------
# Active-learning ledger readers (Sweep / Challenger passes)
# ---------------------------------------------------------------------------


def read_confidence_events(cell_path: PathLike) -> Iterator[Tuple[int, JsonRecord]]:
    """Yield (line_number, record) from ledger/confidence_events.jsonl."""
    return read_jsonl(Path(str(cell_path)) / "ledger" / "confidence_events.jsonl")


def read_retrieval_affinity_events(cell_path: PathLike) -> Iterator[Tuple[int, JsonRecord]]:
    """Yield (line_number, record) from ledger/retrieval_affinity_events.jsonl."""
    return read_jsonl(Path(str(cell_path)) / "ledger" / "retrieval_affinity_events.jsonl")


def read_audit_sparks(cell_path: PathLike) -> Iterator[Tuple[int, JsonRecord]]:
    """Yield (line_number, record) from ledger/audit_sparks.jsonl."""
    return read_jsonl(Path(str(cell_path)) / "ledger" / "audit_sparks.jsonl")


def read_audit_reviews(cell_path: PathLike) -> Iterator[Tuple[int, JsonRecord]]:
    """Yield (line_number, record) from ledger/audit_reviews.jsonl."""
    return read_jsonl(Path(str(cell_path)) / "ledger" / "audit_reviews.jsonl")
