"""Structured observability for replacement-grade ShyftR operations.

Diagnostic logs are append-only Cell ledger rows. They are not canonical
memory truth; they explain why Pack, Signal, confidence, affinity, and
readiness operations made the decisions they made.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from time import perf_counter
from typing import Any, Dict, Iterable, List, Optional, Union
from uuid import uuid4

from .ledger import append_jsonl, read_jsonl

PathLike = Union[str, Path]
DIAGNOSTIC_LEDGER = "diagnostic_logs.jsonl"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_cell_id(cell_path: Path) -> str:
    manifest_path = cell_path / "config" / "cell_manifest.json"
    if not manifest_path.exists():
        return cell_path.name
    try:
        return str(json.loads(manifest_path.read_text(encoding="utf-8")).get("cell_id") or cell_path.name)
    except json.JSONDecodeError:
        return cell_path.name


@dataclass(frozen=True)
class DiagnosticLogEntry:
    diagnostic_id: str
    request_id: str
    cell_id: str
    runtime_id: str
    operation: str
    status: str = "ok"
    selected_charge_ids: List[str] = field(default_factory=list)
    excluded_charge_ids: List[str] = field(default_factory=list)
    scoring_components: Dict[str, Any] = field(default_factory=dict)
    token_estimate: Optional[int] = None
    loadout_id: Optional[str] = None
    signal_id: Optional[str] = None
    confidence_event_ids: List[str] = field(default_factory=list)
    affinity_event_ids: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    regulator_decisions: List[Dict[str, Any]] = field(default_factory=list)
    latency_ms: float = 0.0
    error_class: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    observed_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "diagnostic_id": self.diagnostic_id,
            "request_id": self.request_id,
            "cell_id": self.cell_id,
            "runtime_id": self.runtime_id,
            "operation": self.operation,
            "status": self.status,
            "selected_charge_ids": list(self.selected_charge_ids),
            "excluded_charge_ids": list(self.excluded_charge_ids),
            "scoring_components": dict(self.scoring_components),
            "token_estimate": self.token_estimate,
            "loadout_id": self.loadout_id,
            "signal_id": self.signal_id,
            "confidence_event_ids": list(self.confidence_event_ids),
            "affinity_event_ids": list(self.affinity_event_ids),
            "warnings": list(self.warnings),
            "regulator_decisions": list(self.regulator_decisions),
            "latency_ms": round(float(self.latency_ms), 3),
            "error_class": self.error_class,
            "metadata": dict(self.metadata),
            "observed_at": self.observed_at or _now(),
            "schema_version": "diagnostic-log/v1",
        }


def append_diagnostic_log(cell_path: PathLike, **kwargs: Any) -> DiagnosticLogEntry:
    cell = Path(cell_path)
    entry = DiagnosticLogEntry(
        diagnostic_id=str(kwargs.pop("diagnostic_id", f"diag-{uuid4().hex}")),
        request_id=str(kwargs.pop("request_id", f"req-{uuid4().hex}")),
        cell_id=str(kwargs.pop("cell_id", _read_cell_id(cell))),
        runtime_id=str(kwargs.pop("runtime_id", "local")),
        operation=str(kwargs.pop("operation", "unknown")),
        observed_at=str(kwargs.pop("observed_at", _now())),
        **kwargs,
    )
    append_jsonl(cell / "ledger" / DIAGNOSTIC_LEDGER, entry.to_dict())
    return entry


def read_diagnostic_logs(cell_path: PathLike, *, operation: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    path = Path(cell_path) / "ledger" / DIAGNOSTIC_LEDGER
    records = [record for _, record in read_jsonl(path)] if path.exists() else []
    if operation:
        records = [record for record in records if record.get("operation") == operation]
    if limit is not None and limit >= 0:
        records = records[-limit:]
    return records


class operation_timer:
    """Tiny context helper that exposes elapsed milliseconds."""

    def __enter__(self) -> "operation_timer":
        self._start = perf_counter()
        self.elapsed_ms = 0.0
        return self

    def __exit__(self, *exc: object) -> None:
        self.elapsed_ms = (perf_counter() - self._start) * 1000.0


def summarize_diagnostics(cell_path: PathLike) -> Dict[str, Any]:
    records = read_diagnostic_logs(cell_path)
    by_operation: Dict[str, int] = {}
    warnings: List[str] = []
    errors: List[str] = []
    for record in records:
        op = str(record.get("operation") or "unknown")
        by_operation[op] = by_operation.get(op, 0) + 1
        warnings.extend(str(w) for w in record.get("warnings", []) if w)
        if record.get("error_class"):
            errors.append(str(record.get("error_class")))
    return {
        "status": "ok",
        "diagnostic_count": len(records),
        "by_operation": by_operation,
        "warnings": warnings,
        "errors": errors,
    }
