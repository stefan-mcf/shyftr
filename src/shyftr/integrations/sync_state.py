"""Incremental sync state for runtime adapter sources.

Tracks per-adapter/per-source sync positions so repeated runtime ingest can
process append-only external logs without rereading already ingested rows.

Sync state is adapter bookkeeping, not canonical Cell memory. Cell ledgers
remain truth; sync state lives under ``<cell_path>/indexes`` as a rebuildable
runtime integration accelerator.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SYNC_STATE_FILENAME = "adapter_sync_state.json"
SYNC_STATE_SCHEMA = "shyftr.adapter_sync_state.v1"


class SyncStateError(Exception):
    """Raised when sync state cannot be loaded, saved, or applied."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class SyncTruncationError(SyncStateError):
    """Raised when an append-only source was truncated, removed, or rotated."""


@dataclass
class SyncStateEntry:
    """Incremental sync cursor for one adapter source path."""

    adapter_id: str
    source_path: str
    last_byte_offset: int = 0
    last_line_number: int = 0
    last_content_hash: str = ""
    last_sync_time: str = ""

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "SyncStateEntry":
        return cls(
            adapter_id=str(payload.get("adapter_id", "")),
            source_path=str(payload.get("source_path", "")),
            last_byte_offset=int(payload.get("last_byte_offset", 0) or 0),
            last_line_number=int(payload.get("last_line_number", 0) or 0),
            last_content_hash=str(payload.get("last_content_hash", "")),
            last_sync_time=str(payload.get("last_sync_time", "")),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "adapter_id": self.adapter_id,
            "source_path": self.source_path,
            "last_byte_offset": self.last_byte_offset,
            "last_line_number": self.last_line_number,
            "last_content_hash": self.last_content_hash,
            "last_sync_time": self.last_sync_time,
        }


@dataclass
class SyncStateStore:
    """File-backed sync state store under a Cell's indexes directory."""

    sync_states: Dict[str, SyncStateEntry] = field(default_factory=dict)
    cell_indexes_path: Optional[Path] = None

    @classmethod
    def load(cls, cell_path: Path) -> "SyncStateStore":
        indexes_path = Path(cell_path) / "indexes"
        state_path = indexes_path / SYNC_STATE_FILENAME
        if not state_path.exists():
            return cls(sync_states={}, cell_indexes_path=indexes_path)
        try:
            raw = json.loads(state_path.read_text(encoding="utf-8"))
            states = {
                key: SyncStateEntry.from_dict(value)
                for key, value in raw.get("sync_states", {}).items()
                if isinstance(value, dict)
            }
            return cls(sync_states=states, cell_indexes_path=indexes_path)
        except (json.JSONDecodeError, OSError, ValueError) as exc:
            raise SyncStateError(
                f"Failed to load sync state: {state_path}",
                details={"path": str(state_path), "error": str(exc)},
            )

    def save(self) -> None:
        if self.cell_indexes_path is None:
            raise SyncStateError("cell_indexes_path is not set")
        self.cell_indexes_path.mkdir(parents=True, exist_ok=True)
        state_path = self.cell_indexes_path / SYNC_STATE_FILENAME
        payload = {
            "sync_states": {
                key: value.to_dict()
                for key, value in sorted(self.sync_states.items())
            },
            "_meta": {
                "schema": SYNC_STATE_SCHEMA,
                "entry_count": len(self.sync_states),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
        }
        try:
            state_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        except OSError as exc:
            raise SyncStateError(
                f"Failed to save sync state: {state_path}",
                details={"path": str(state_path), "error": str(exc)},
            )

    def get_entry(self, source_path: str) -> Optional[SyncStateEntry]:
        return self.sync_states.get(str(source_path))

    def upsert_entry(self, entry: SyncStateEntry) -> None:
        self.sync_states[str(entry.source_path)] = entry

    def remove_entry(self, source_path: str) -> None:
        self.sync_states.pop(str(source_path), None)

    def list_entries(self) -> List[SyncStateEntry]:
        return [self.sync_states[key] for key in sorted(self.sync_states)]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_file_content_hash(file_path: Path) -> str:
    digest = hashlib.sha256()
    with Path(file_path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_lines(file_path: Path) -> int:
    try:
        with Path(file_path).open("r", encoding="utf-8") as handle:
            return sum(1 for _ in handle)
    except OSError as exc:
        raise SyncStateError(
            f"Failed to count lines: {file_path}",
            details={"path": str(file_path), "error": str(exc)},
        )


def count_file_jsonl_rows(file_path: Path) -> int:
    return count_lines(file_path)


def read_new_lines(file_path: Path, start_line: int) -> List[str]:
    lines: List[str] = []
    try:
        with Path(file_path).open("r", encoding="utf-8") as handle:
            for line_number, raw in enumerate(handle, start=1):
                if line_number <= start_line:
                    continue
                stripped = raw.strip()
                if stripped:
                    lines.append(stripped)
        return lines
    except OSError as exc:
        raise SyncStateError(
            f"Failed to read new lines from: {file_path}",
            details={"path": str(file_path), "start_line": start_line, "error": str(exc)},
        )


def new_sync_entry(
    adapter_id: str,
    source_path: str,
    file_size: int,
    line_count: int,
    content_hash: str,
) -> SyncStateEntry:
    return SyncStateEntry(
        adapter_id=adapter_id,
        source_path=str(source_path),
        last_byte_offset=file_size,
        last_line_number=line_count,
        last_content_hash=content_hash,
        last_sync_time=utc_now(),
    )


def check_file_truncation(file_path: Path, entry: SyncStateEntry) -> None:
    """Validate that a source is still append-only relative to its cursor.

    Missing files, smaller files, and same-size files with different content are
    treated as rotation/truncation. Callers must explicitly reset or backfill
    before continuing from such a state.
    """
    path = Path(file_path)
    if entry.last_byte_offset <= 0 and entry.last_line_number <= 0:
        return
    if not path.exists():
        raise SyncTruncationError(
            f"Source file no longer exists: {path}",
            details={"source_path": str(path), "last_byte_offset": entry.last_byte_offset},
        )
    current_size = path.stat().st_size
    if current_size < entry.last_byte_offset:
        raise SyncTruncationError(
            f"Source file truncated or rotated: {path}",
            details={
                "source_path": str(path),
                "last_byte_offset": entry.last_byte_offset,
                "current_size": current_size,
            },
        )
    if current_size == entry.last_byte_offset and entry.last_content_hash:
        current_hash = build_file_content_hash(path)
        if current_hash != entry.last_content_hash:
            raise SyncTruncationError(
                f"Source file rotated with unchanged size: {path}",
                details={
                    "source_path": str(path),
                    "last_byte_offset": entry.last_byte_offset,
                    "current_size": current_size,
                },
            )


__all__ = [
    "SYNC_STATE_FILENAME",
    "SYNC_STATE_SCHEMA",
    "SyncStateEntry",
    "SyncStateError",
    "SyncStateStore",
    "SyncTruncationError",
    "build_file_content_hash",
    "check_file_truncation",
    "count_file_jsonl_rows",
    "count_lines",
    "new_sync_entry",
    "read_new_lines",
]
