"""Runtime proposal export contract for external integrations.

Runtime proposals are advisory records that let ShyftR offer recommendations to
an external runtime without mutating that runtime's policy, queue, config, or
operational state. Proposals remain review-gated data until an operator or
runtime-side manager explicitly accepts and applies them.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

PathLike = Union[str, Path]

PROPOSAL_LEDGER_RELATIVE_PATH = Path("proposals") / "proposed.jsonl"
PROPOSAL_EXPORT_RELATIVE_DIR = Path("exports") / "proposals"

RUNTIME_PROPOSAL_TYPES: Tuple[str, ...] = (
    "memory_application_hint",
    "routing_hint",
    "verification_hint",
    "retry_caution",
    "policy_change_candidate",
    "missing_memory_candidate",
)

REVIEW_STATUSES: Tuple[str, ...] = ("pending", "accepted", "rejected", "deferred")
EXPORTABLE_REVIEW_STATUSES: Tuple[str, ...] = ("pending", "deferred")


@dataclass(frozen=True)
class RuntimeProposal:
    """Advisory recommendation exported to an external runtime for review."""

    proposal_id: str
    proposal_type: str
    target_external_system: str
    target_external_scope: str
    recommendation: str
    evidence_charge_ids: List[str] = field(default_factory=list)
    evidence_pulse_ids: List[str] = field(default_factory=list)
    target_external_refs: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.5
    review_status: str = "pending"
    created_timestamp: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.proposal_id:
            raise ValueError("proposal_id is required")
        if self.proposal_type not in RUNTIME_PROPOSAL_TYPES:
            raise ValueError(
                f"proposal_type must be one of {', '.join(RUNTIME_PROPOSAL_TYPES)}"
            )
        if not self.target_external_system:
            raise ValueError("target_external_system is required")
        if not self.target_external_scope:
            raise ValueError("target_external_scope is required")
        if not self.recommendation:
            raise ValueError("recommendation is required")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        if self.review_status not in REVIEW_STATUSES:
            raise ValueError(f"review_status must be one of {', '.join(REVIEW_STATUSES)}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "proposal_type": self.proposal_type,
            "target_external_system": self.target_external_system,
            "target_external_scope": self.target_external_scope,
            "target_external_refs": list(self.target_external_refs),
            "recommendation": self.recommendation,
            "evidence_charge_ids": list(self.evidence_charge_ids),
            "evidence_pulse_ids": list(self.evidence_pulse_ids),
            "confidence": float(self.confidence),
            "review_status": self.review_status,
            "created_timestamp": self.created_timestamp,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "RuntimeProposal":
        return cls(
            proposal_id=str(payload.get("proposal_id", "")),
            proposal_type=str(payload.get("proposal_type", "")),
            target_external_system=str(payload.get("target_external_system", "")),
            target_external_scope=str(payload.get("target_external_scope", "")),
            target_external_refs=list(payload.get("target_external_refs") or []),
            recommendation=str(payload.get("recommendation", "")),
            evidence_charge_ids=[str(v) for v in payload.get("evidence_charge_ids") or []],
            evidence_pulse_ids=[
                str(v)
                for v in (payload.get("evidence_pulse_ids") or payload.get("evidence_feed_ids") or [])
            ],
            confidence=float(payload.get("confidence", 0.5)),
            review_status=str(payload.get("review_status", "pending")),
            created_timestamp=str(payload.get("created_timestamp", "")),
            metadata=dict(payload.get("metadata") or {}),
        )


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def runtime_proposals_ledger_path(cell_path: PathLike) -> Path:
    return Path(cell_path) / PROPOSAL_LEDGER_RELATIVE_PATH


def append_runtime_proposal(cell_path: PathLike, proposal: RuntimeProposal) -> Path:
    """Append one pending runtime proposal to the Cell proposal ledger."""

    ledger_path = runtime_proposals_ledger_path(cell_path)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(proposal.to_dict(), sort_keys=True) + "\n")
    return ledger_path


def read_runtime_proposals(
    cell_path: PathLike,
    *,
    external_system: Optional[str] = None,
    review_statuses: Sequence[str] = EXPORTABLE_REVIEW_STATUSES,
) -> List[RuntimeProposal]:
    """Read review-gated runtime proposals from the Cell proposal ledger."""

    ledger_path = runtime_proposals_ledger_path(cell_path)
    if not ledger_path.exists():
        return []

    allowed_statuses = set(review_statuses)
    proposals: List[RuntimeProposal] = []
    for line_no, line in enumerate(ledger_path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            proposal = RuntimeProposal.from_dict(json.loads(stripped))
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            raise ValueError(f"invalid runtime proposal at {ledger_path}:{line_no}: {exc}") from exc
        if external_system and proposal.target_external_system != external_system:
            continue
        if proposal.review_status not in allowed_statuses:
            continue
        proposals.append(proposal)
    return proposals


def runtime_proposal_export_payload(
    cell_path: PathLike,
    *,
    external_system: Optional[str] = None,
    include_accepted: bool = False,
) -> Dict[str, Any]:
    """Build the stable JSON payload consumed by external runtimes."""

    review_statuses = EXPORTABLE_REVIEW_STATUSES
    if include_accepted:
        review_statuses = (*EXPORTABLE_REVIEW_STATUSES, "accepted")
    proposals = read_runtime_proposals(
        cell_path,
        external_system=external_system,
        review_statuses=review_statuses,
    )
    return {
        "contract": "shyftr.runtime_proposals.v1",
        "generated_at": now_utc_iso(),
        "cell_path": str(Path(cell_path)),
        "external_system": external_system or "",
        "proposal_count": len(proposals),
        "advisory_only": True,
        "requires_external_review": True,
        "mutates_external_runtime": False,
        "proposals": [proposal.to_dict() for proposal in proposals],
    }


def export_runtime_proposals(
    cell_path: PathLike,
    *,
    external_system: Optional[str] = None,
    output_path: Optional[PathLike] = None,
    include_accepted: bool = False,
) -> Dict[str, Any]:
    """Return proposal export JSON and optionally write it to disk."""

    payload = runtime_proposal_export_payload(
        cell_path,
        external_system=external_system,
        include_accepted=include_accepted,
    )
    if output_path is not None:
        path = Path(output_path)
        if not path.is_absolute():
            path = Path(cell_path) / PROPOSAL_EXPORT_RELATIVE_DIR / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        payload = {**payload, "export_path": str(path)}
    return payload


def proposal_from_evidence(
    *,
    proposal_id: str,
    proposal_type: str,
    target_external_system: str,
    target_external_scope: str,
    recommendation: str,
    evidence_charge_ids: Optional[Iterable[str]] = None,
    evidence_pulse_ids: Optional[Iterable[str]] = None,
    target_external_refs: Optional[Iterable[Dict[str, Any]]] = None,
    confidence: float = 0.5,
    metadata: Optional[Dict[str, Any]] = None,
    created_timestamp: Optional[str] = None,
) -> RuntimeProposal:
    """Create a pending proposal with explicit provenance evidence."""

    return RuntimeProposal(
        proposal_id=proposal_id,
        proposal_type=proposal_type,
        target_external_system=target_external_system,
        target_external_scope=target_external_scope,
        target_external_refs=list(target_external_refs or []),
        recommendation=recommendation,
        evidence_charge_ids=[str(v) for v in evidence_charge_ids or []],
        evidence_pulse_ids=[str(v) for v in evidence_pulse_ids or []],
        confidence=confidence,
        review_status="pending",
        created_timestamp=created_timestamp or now_utc_iso(),
        metadata=dict(metadata or {}),
    )


__all__ = [
    "EXPORTABLE_REVIEW_STATUSES",
    "PROPOSAL_EXPORT_RELATIVE_DIR",
    "PROPOSAL_LEDGER_RELATIVE_PATH",
    "REVIEW_STATUSES",
    "RUNTIME_PROPOSAL_TYPES",
    "RuntimeProposal",
    "append_runtime_proposal",
    "export_runtime_proposals",
    "proposal_from_evidence",
    "read_runtime_proposals",
    "runtime_proposal_export_payload",
    "runtime_proposals_ledger_path",
]
