from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union
from uuid import uuid4

from .ledger import append_jsonl, read_jsonl

PathLike = Union[str, Path]


class ReviewError(ValueError):
    """Raised when a Fragment review event cannot be recorded."""


def approve_fragment(
    cell_path: PathLike,
    fragment_id: str,
    *,
    reviewer: str,
    rationale: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return _append_review_event(
        cell_path,
        fragment_id=fragment_id,
        review_action="approve",
        review_status="approved",
        reviewer=reviewer,
        rationale=rationale,
        metadata=metadata or {},
    )


def reject_fragment(
    cell_path: PathLike,
    fragment_id: str,
    *,
    reviewer: str,
    rationale: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return _append_review_event(
        cell_path,
        fragment_id=fragment_id,
        review_action="reject",
        review_status="rejected",
        reviewer=reviewer,
        rationale=rationale,
        metadata=metadata or {},
    )


def split_fragment(
    cell_path: PathLike,
    fragment_id: str,
    *,
    reviewer: str,
    proposed_texts: List[str],
    rationale: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if not proposed_texts or any(not text.strip() for text in proposed_texts):
        raise ReviewError("split review requires non-empty proposed_texts")
    event_metadata = dict(metadata or {})
    event_metadata["proposed_texts"] = proposed_texts
    return _append_review_event(
        cell_path,
        fragment_id=fragment_id,
        review_action="split",
        review_status="split_proposed",
        reviewer=reviewer,
        rationale=rationale,
        metadata=event_metadata,
    )


def merge_fragments(
    cell_path: PathLike,
    fragment_ids: List[str],
    *,
    reviewer: str,
    proposed_text: str,
    rationale: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if len(fragment_ids) < 2:
        raise ReviewError("merge review requires at least two fragment ids")
    if not proposed_text.strip():
        raise ReviewError("merge review requires proposed_text")
    _require_fragments(cell_path, fragment_ids)
    event_metadata = dict(metadata or {})
    event_metadata["source_fragment_ids"] = fragment_ids
    event_metadata["proposed_text"] = proposed_text
    return _append_review_event(
        cell_path,
        fragment_id=fragment_ids[0],
        review_action="merge",
        review_status="merge_proposed",
        reviewer=reviewer,
        rationale=rationale,
        metadata=event_metadata,
    )


def latest_review(cell_path: PathLike, fragment_id: str) -> Optional[Dict[str, Any]]:
    latest: Optional[Dict[str, Any]] = None
    reviews_ledger = Path(cell_path) / "ledger" / "reviews.jsonl"
    for _, record in read_jsonl(reviews_ledger):
        if record.get("fragment_id") == fragment_id:
            latest = record
    return latest


def _append_review_event(
    cell_path: PathLike,
    *,
    fragment_id: str,
    review_action: str,
    review_status: str,
    reviewer: str,
    rationale: str,
    metadata: Dict[str, Any],
) -> Dict[str, Any]:
    if not reviewer:
        raise ReviewError("reviewer is required")
    if not rationale:
        raise ReviewError("rationale is required")
    _require_fragments(cell_path, [fragment_id])
    event = {
        "review_id": f"rev-{uuid4().hex}",
        "fragment_id": fragment_id,
        "review_action": review_action,
        "review_status": review_status,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "reviewer": reviewer,
        "rationale": rationale,
        "metadata": metadata,
    }
    append_jsonl(Path(cell_path) / "ledger" / "reviews.jsonl", event)
    return event


def _require_fragments(cell_path: PathLike, fragment_ids: Iterable[str]) -> None:
    existing = set()
    for _, record in read_jsonl(Path(cell_path) / "ledger" / "fragments.jsonl"):
        existing.add(record.get("fragment_id"))
    missing = [fragment_id for fragment_id in fragment_ids if fragment_id not in existing]
    if missing:
        raise ReviewError(f"Unknown fragment id(s): {', '.join(missing)}")
