"""Doctrine proposal generation from high-resonance Alloys.

Doctrine is intentionally review-gated.  This module can append proposed
Doctrine records to ``doctrine/proposed.jsonl`` and can perform an explicit
approval step, but the proposal pipeline never writes to
``doctrine/approved.jsonl`` on its own.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Union

from ..ledger import append_jsonl, read_jsonl
from ..models import Alloy, DoctrineProposal
from ..resonance import ResonanceScore

PathLike = Union[str, Path]


def _doctrine_id_for(alloy_ids: Sequence[str], scope: str) -> str:
    """Return a deterministic Doctrine proposal ID."""
    seed = f"{'|'.join(sorted(alloy_ids))}|{scope.strip().lower()}"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
    return f"doctrine-{digest}"


def _build_doctrine_statement(alloys: Sequence[Alloy], scope: str) -> str:
    summaries = "; ".join(alloy.summary for alloy in sorted(alloys, key=lambda item: item.alloy_id))
    return f"Doctrine proposal ({scope}): {summaries}"


def propose_doctrine(
    high_resonance_alloys: Sequence[Alloy],
    *,
    scope: str = "cross-cell",
    require_min_alloys: int = 1,
) -> List[DoctrineProposal]:
    """Create pending Doctrine proposals from already-filtered Alloys."""
    if len(high_resonance_alloys) < require_min_alloys:
        return []
    alloy_ids = sorted(alloy.alloy_id for alloy in high_resonance_alloys)
    return [
        DoctrineProposal(
            doctrine_id=_doctrine_id_for(alloy_ids, scope),
            source_alloy_ids=alloy_ids,
            scope=scope,
            statement=_build_doctrine_statement(high_resonance_alloys, scope),
            review_status="pending",
        )
    ]


def propose_doctrine_from_resonance(
    alloys: Sequence[Alloy],
    resonance_scores: Iterable[ResonanceScore],
    *,
    min_resonance: float = 0.50,
    scope: str = "cross-cell",
    require_min_alloys: int = 1,
) -> List[DoctrineProposal]:
    """Filter high-resonance Alloys and create pending Doctrine proposals."""
    high_ids = {
        score.alloy_id
        for score in resonance_scores
        if score.score >= min_resonance and score.cell_diversity >= 2
    }
    selected = [alloy for alloy in sorted(alloys, key=lambda item: item.alloy_id) if alloy.alloy_id in high_ids]
    return propose_doctrine(
        selected,
        scope=scope,
        require_min_alloys=require_min_alloys,
    )


def append_doctrine_proposals(
    cell_path: PathLike,
    proposals: Sequence[DoctrineProposal],
) -> int:
    """Append proposals to doctrine/proposed.jsonl and return write count."""
    ledger_path = Path(cell_path) / "doctrine" / "proposed.jsonl"
    count = 0
    for proposal in proposals:
        append_jsonl(ledger_path, proposal.to_dict())
        count += 1
    return count


def read_proposed_doctrines(cell_path: PathLike) -> List[DoctrineProposal]:
    """Read Doctrine proposals from doctrine/proposed.jsonl."""
    ledger_path = Path(cell_path) / "doctrine" / "proposed.jsonl"
    if not ledger_path.exists():
        return []
    return [DoctrineProposal.from_dict(record) for _line, record in read_jsonl(ledger_path)]


def read_approved_doctrines(cell_path: PathLike) -> List[DoctrineProposal]:
    """Read reviewed Doctrine records from doctrine/approved.jsonl."""
    ledger_path = Path(cell_path) / "doctrine" / "approved.jsonl"
    if not ledger_path.exists():
        return []
    return [DoctrineProposal.from_dict(record) for _line, record in read_jsonl(ledger_path)]


def approve_doctrine(cell_path: PathLike, doctrine_id: str) -> Optional[DoctrineProposal]:
    """Explicitly approve one pending Doctrine proposal.

    Approval appends an approved copy to ``doctrine/approved.jsonl`` and leaves
    ``doctrine/proposed.jsonl`` untouched for auditability.  Re-approving the
    same Doctrine ID is idempotent.
    """
    approved = {proposal.doctrine_id: proposal for proposal in read_approved_doctrines(cell_path)}
    if doctrine_id in approved:
        return approved[doctrine_id]

    for proposal in read_proposed_doctrines(cell_path):
        if proposal.doctrine_id != doctrine_id:
            continue
        approved_proposal = DoctrineProposal(
            doctrine_id=proposal.doctrine_id,
            source_alloy_ids=proposal.source_alloy_ids,
            scope=proposal.scope,
            statement=proposal.statement,
            review_status="approved",
        )
        append_jsonl(Path(cell_path) / "doctrine" / "approved.jsonl", approved_proposal.to_dict())
        return approved_proposal
    return None


def distill_doctrine(
    cell_path: PathLike,
    high_resonance_alloys: Sequence[Alloy],
    *,
    scope: str = "cross-cell",
    require_min_alloys: int = 1,
) -> Dict[str, Any]:
    """Append Doctrine proposals only; never silently approve them."""
    before_approved = len(read_approved_doctrines(cell_path))
    proposals = propose_doctrine(
        high_resonance_alloys,
        scope=scope,
        require_min_alloys=require_min_alloys,
    )
    appended = append_doctrine_proposals(cell_path, proposals)
    after_approved = len(read_approved_doctrines(cell_path))
    return {
        "proposal_count": appended,
        "proposal_ids": [proposal.doctrine_id for proposal in proposals],
        "source_alloy_ids": sorted(
            {alloy_id for proposal in proposals for alloy_id in proposal.source_alloy_ids}
        ),
        "scope": scope,
        "approved_count_delta": after_approved - before_approved,
    }
