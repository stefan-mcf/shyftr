from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union
from uuid import uuid4

from .ledger import append_jsonl, read_jsonl
from .layout import _validate_cell_id

PathLike = Union[str, Path]
REGISTRY_LEDGER_NAME = "cell_registry.jsonl"
REGISTRY_EVENT_KINDS = {"registered", "updated", "unregistered", "relationship_added", "relationship_removed"}

@dataclass(frozen=True)
class CellRegistryEntry:
    cell_id: str
    cell_type: str
    path: str
    owner: str
    tags: List[str]
    domain: str
    trust_boundary: str
    registered_at: str
    status: str = "active"
    relationship_edges: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_cell_id(self.cell_id)
        required = {
            "cell_type": self.cell_type,
            "path": self.path,
            "owner": self.owner,
            "domain": self.domain,
            "trust_boundary": self.trust_boundary,
            "registered_at": self.registered_at,
            "status": self.status,
        }
        missing = [name for name, value in required.items() if not str(value or "").strip()]
        if missing:
            raise ValueError(f"Missing required registry field(s): {', '.join(missing)}")
        if not isinstance(self.tags, list):
            raise ValueError("tags must be a list")
        path = Path(self.path).expanduser()
        if not path.is_absolute():
            raise ValueError("registry path must be local and explicit")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cell_id": self.cell_id,
            "cell_type": self.cell_type,
            "path": self.path,
            "owner": self.owner,
            "tags": list(self.tags),
            "domain": self.domain,
            "trust_boundary": self.trust_boundary,
            "registered_at": self.registered_at,
            "status": self.status,
            "relationship_edges": list(self.relationship_edges),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "CellRegistryEntry":
        data = dict(payload)
        if "registered_at" not in data:
            data["registered_at"] = _now()
        if "tags" not in data or data["tags"] is None:
            data["tags"] = []
        if "relationship_edges" not in data or data["relationship_edges"] is None:
            data["relationship_edges"] = []
        if "metadata" not in data or data["metadata"] is None:
            data["metadata"] = {}
        allowed = set(cls.__dataclass_fields__)
        missing = [name for name in ("cell_id", "cell_type", "path", "owner", "domain", "trust_boundary", "registered_at") if name not in data]
        if missing:
            raise ValueError(f"Missing required registry field(s): {', '.join(missing)}")
        return cls(**{k: v for k, v in data.items() if k in allowed})


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def registry_ledger_path(registry_path: PathLike) -> Path:
    path = Path(registry_path).expanduser()
    if path.suffix == ".jsonl":
        return path
    return path / "ledger" / REGISTRY_LEDGER_NAME


def _event(kind: str, entry: Optional[CellRegistryEntry] = None, *, cell_id: Optional[str] = None, reason: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if kind not in REGISTRY_EVENT_KINDS:
        raise ValueError(f"Unsupported registry event kind: {kind}")
    payload = {
        "event_id": f"cell-reg-{uuid4().hex[:12]}",
        "event_kind": kind,
        "cell_id": cell_id or (entry.cell_id if entry else None),
        "recorded_at": _now(),
        "reason": reason,
        "metadata": metadata or {},
        "append_only": True,
    }
    if entry is not None:
        payload["entry"] = entry.to_dict()
    return payload


def _events(path: PathLike) -> List[Dict[str, Any]]:
    ledger = registry_ledger_path(path)
    if not ledger.exists():
        return []
    return [record for _, record in read_jsonl(ledger)]


def fold_registry(registry_path: PathLike) -> Dict[str, CellRegistryEntry]:
    active: Dict[str, CellRegistryEntry] = {}
    for event in _events(registry_path):
        kind = event.get("event_kind")
        cell_id = str(event.get("cell_id") or "")
        if kind in {"registered", "updated", "relationship_added", "relationship_removed"}:
            entry_payload = event.get("entry") or {}
            entry = CellRegistryEntry.from_dict(entry_payload)
            if entry.status == "active":
                active[entry.cell_id] = entry
            else:
                active.pop(entry.cell_id, None)
        elif kind == "unregistered":
            active.pop(cell_id, None)
    return active


def register_cell(registry_path: PathLike, entry: Union[CellRegistryEntry, Dict[str, Any]]) -> CellRegistryEntry:
    entry_obj = entry if isinstance(entry, CellRegistryEntry) else CellRegistryEntry.from_dict(entry)
    projection = fold_registry(registry_path)
    if entry_obj.cell_id in projection:
        raise ValueError(f"duplicate active cell_id: {entry_obj.cell_id}")
    append_jsonl(registry_ledger_path(registry_path), _event("registered", entry_obj))
    return entry_obj


def list_cells(registry_path: PathLike, *, cell_type: Optional[str] = None, tags: Optional[Sequence[str]] = None, status: str = "active") -> List[CellRegistryEntry]:
    entries = sorted(fold_registry(registry_path).values(), key=lambda item: item.cell_id)
    if status:
        entries = [entry for entry in entries if entry.status == status]
    if cell_type:
        entries = [entry for entry in entries if entry.cell_type == cell_type]
    if tags:
        wanted = set(tags)
        entries = [entry for entry in entries if wanted.issubset(set(entry.tags))]
    return entries


def get_cell(registry_path: PathLike, cell_id: str) -> CellRegistryEntry:
    projection = fold_registry(registry_path)
    if cell_id not in projection:
        raise ValueError(f"Unknown registered cell_id: {cell_id}")
    return projection[cell_id]


def unregister_cell(registry_path: PathLike, cell_id: str, reason: str) -> Dict[str, Any]:
    if not reason:
        raise ValueError("reason is required")
    get_cell(registry_path, cell_id)
    event = _event("unregistered", cell_id=cell_id, reason=reason)
    append_jsonl(registry_ledger_path(registry_path), event)
    return event


def discover_initialized_cells(root: PathLike) -> List[CellRegistryEntry]:
    base = Path(root).expanduser()
    entries: List[CellRegistryEntry] = []
    if not base.exists():
        return entries
    for manifest in sorted(base.glob("*/config/cell_manifest.json")):
        data = json.loads(manifest.read_text(encoding="utf-8"))
        cell_path = manifest.parents[1].resolve()
        entries.append(CellRegistryEntry(
            cell_id=str(data.get("cell_id") or cell_path.name),
            cell_type=str(data.get("cell_type") or "domain"),
            path=str(cell_path),
            owner=str(data.get("owner") or "local"),
            tags=list(data.get("tags") or []),
            domain=str(data.get("domain") or data.get("cell_type") or "local"),
            trust_boundary=str(data.get("trust_boundary") or "local"),
            registered_at=str(data.get("registered_at") or _now()),
        ))
    return entries
