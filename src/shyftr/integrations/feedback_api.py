"""Runtime Outcome reporting API for external agent runtimes.

Defines the stable JSON-serializable contract that external runtimes use
to report what happened after a ShyftR Loadout was supplied.

ShyftR doctrine:
  - Outcome is learning.
  - Cell ledgers are canonical truth.
  - External runtimes own operational execution; ShyftR records durable,
    provenance-linked Outcome evidence and confidence signals.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..outcomes import compute_trace_usage_counters, record_outcome


_VALID_RESULTS = {"success", "failure", "partial", "abandoned", "unknown"}


@dataclass(frozen=True)
class RuntimeOutcomeReport:
    """JSON-serializable Outcome report from an external runtime.

    `external_task_id` and `external_run_id` are preserved as provenance in
    Outcome verification evidence. ShyftR still generates its own internal
    Cell-local `Outcome.task_id` when appending the ledger row.
    """

    cell_path_or_id: str
    loadout_id: str
    result: str
    external_system: str
    external_scope: str
    external_run_id: Optional[str] = None
    external_task_id: Optional[str] = None
    applied_trace_ids: List[str] = field(default_factory=list)
    useful_trace_ids: List[str] = field(default_factory=list)
    harmful_trace_ids: List[str] = field(default_factory=list)
    ignored_trace_ids: List[str] = field(default_factory=list)
    violated_caution_ids: List[str] = field(default_factory=list)
    missing_memory_notes: List[str] = field(default_factory=list)
    verification_evidence: Dict[str, Any] = field(default_factory=dict)
    runtime_metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cell_path_or_id": self.cell_path_or_id,
            "loadout_id": self.loadout_id,
            "result": self.result,
            "external_system": self.external_system,
            "external_scope": self.external_scope,
            "external_run_id": self.external_run_id,
            "external_task_id": self.external_task_id,
            "applied_trace_ids": list(self.applied_trace_ids),
            "useful_trace_ids": list(self.useful_trace_ids),
            "harmful_trace_ids": list(self.harmful_trace_ids),
            "ignored_trace_ids": list(self.ignored_trace_ids),
            "violated_caution_ids": list(self.violated_caution_ids),
            "missing_memory_notes": list(self.missing_memory_notes),
            "verification_evidence": dict(self.verification_evidence),
            "runtime_metadata": dict(self.runtime_metadata),
            "tags": list(self.tags),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "RuntimeOutcomeReport":
        values = {k: v for k, v in payload.items() if k in cls.__dataclass_fields__}
        return cls(**values)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, payload: str) -> "RuntimeOutcomeReport":
        return cls.from_dict(json.loads(payload))


@dataclass(frozen=True)
class RuntimeOutcomeResponse:
    """JSON-serializable response from processing a runtime Outcome report."""

    status: str
    accepted: bool = False
    outcome_id: str = ""
    trace_counters: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "accepted": self.accepted,
            "outcome_id": self.outcome_id,
            "trace_counters": list(self.trace_counters),
            "warnings": list(self.warnings),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "RuntimeOutcomeResponse":
        values = {k: v for k, v in payload.items() if k in cls.__dataclass_fields__}
        return cls(**values)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, payload: str) -> "RuntimeOutcomeResponse":
        return cls.from_dict(json.loads(payload))


def _reject(message: str, warnings: Optional[List[str]] = None) -> RuntimeOutcomeResponse:
    return RuntimeOutcomeResponse(
        status="rejected",
        accepted=False,
        warnings=[message, *(warnings or [])],
    )


def _validate_report(report: RuntimeOutcomeReport) -> Optional[str]:
    for field_name in (
        "cell_path_or_id",
        "loadout_id",
        "result",
        "external_system",
        "external_scope",
    ):
        value = getattr(report, field_name)
        if not value:
            return f"{field_name} is required"
    return None


def process_runtime_outcome_report(report: RuntimeOutcomeReport) -> RuntimeOutcomeResponse:
    """Validate, append, and summarize a Runtime Outcome report.

    The append path is intentionally routed through `record_outcome()` so RI-6
    preserves the existing Outcome ledger semantics, missing-memory proposal
    behavior, and derived trace counter computation.
    """

    validation_error = _validate_report(report)
    if validation_error:
        return _reject(validation_error)

    cell_path = Path(report.cell_path_or_id)
    if not cell_path.exists():
        return _reject(f"Cell path does not exist: {report.cell_path_or_id}")

    warnings: List[str] = []
    if report.result not in _VALID_RESULTS:
        warnings.append(
            f"result '{report.result}' is not one of {sorted(_VALID_RESULTS)}; recording as supplied"
        )

    verification_evidence = dict(report.verification_evidence)
    verification_evidence.update(
        {
            "external_system": report.external_system,
            "external_scope": report.external_scope,
            "external_run_id": report.external_run_id,
            "external_task_id": report.external_task_id,
            "ignored_trace_ids": list(report.ignored_trace_ids),
            "violated_caution_ids": list(report.violated_caution_ids),
            "runtime_metadata": dict(report.runtime_metadata),
            "tags": list(report.tags),
        }
    )

    try:
        outcome = record_outcome(
            cell_path=cell_path,
            loadout_id=report.loadout_id,
            result=report.result,
            applied_trace_ids=list(report.applied_trace_ids),
            useful_trace_ids=list(report.useful_trace_ids),
            harmful_trace_ids=list(report.harmful_trace_ids),
            missing_memory=list(report.missing_memory_notes),
            verification_evidence=verification_evidence,
        )
    except ValueError as exc:
        return _reject(f"Cell validation failed: {exc}", warnings=warnings)

    counters = [
        counter.to_dict()
        for trace_id, counter in sorted(compute_trace_usage_counters(cell_path).items())
    ]

    return RuntimeOutcomeResponse(
        status="accepted",
        accepted=True,
        outcome_id=outcome.outcome_id,
        trace_counters=counters,
        warnings=warnings,
    )
