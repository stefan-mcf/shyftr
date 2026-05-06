"""Proposal-only decay and deprecation analysis for ShyftR Traces."""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from shyftr.ledger import append_jsonl, read_jsonl

PathLike = Union[str, Path]
JsonRecord = Dict[str, Any]

DEFAULT_MIN_USES_FOR_FAILURE_RATE = 3
DEFAULT_LOW_SUCCESS_RATE = 0.30


def propose_deprecations(
    cell_path: PathLike,
    *,
    max_deprecations: Optional[int] = None,
    proposed_at: Optional[str] = None,
    min_uses_for_failure_rate: int = DEFAULT_MIN_USES_FOR_FAILURE_RATE,
    low_success_rate: float = DEFAULT_LOW_SUCCESS_RATE,
) -> List[JsonRecord]:
    """Return deprecation proposals without mutating Trace ledgers.

    Reasons currently emitted:
    - ``stale``: no recorded use.
    - ``harmful``: failures outnumber successes.
    - ``underperforming``: established success rate is below threshold.
    - ``unsupported``: source Fragment references are missing.
    - ``superseded``: another approved Trace has the same normalized statement.
    """
    cell = Path(cell_path)
    traces = _read_records(cell / "traces" / "approved.jsonl")
    known_fragments = {
        str(row.get("fragment_id"))
        for row in _read_records(cell / "ledger" / "fragments.jsonl")
        if row.get("fragment_id") is not None
    }
    duplicate_ids = _superseded_trace_ids(traces)
    timestamp = proposed_at or datetime.now(timezone.utc).isoformat()

    proposals: List[JsonRecord] = []
    for trace in traces:
        trace_id = str(trace.get("trace_id") or "")
        use_count = int(trace.get("use_count") or 0)
        success_count = int(trace.get("success_count") or 0)
        failure_count = int(trace.get("failure_count") or 0)
        reasons: List[str] = []
        details: Dict[str, Any] = {}

        if use_count == 0:
            reasons.append("stale")
        if failure_count > success_count and failure_count > 0:
            reasons.append("harmful")
        if use_count >= min_uses_for_failure_rate:
            success_rate = success_count / use_count if use_count else 0.0
            if success_rate < low_success_rate:
                reasons.append("underperforming")
                details["success_rate"] = round(success_rate, 4)

        missing_fragments = [
            fragment_id
            for fragment_id in trace.get("source_fragment_ids", [])
            if str(fragment_id) not in known_fragments
        ]
        if missing_fragments:
            reasons.append("unsupported")
            details["missing_fragment_ids"] = missing_fragments
        if trace_id in duplicate_ids:
            reasons.append("superseded")
            details["duplicate_statement"] = trace.get("statement")

        if reasons:
            proposals.append(
                {
                    "proposal_id": _proposal_id(trace_id, reasons),
                    "proposal_status": "proposed",
                    "trace_id": trace.get("trace_id"),
                    "statement": trace.get("statement"),
                    "reasons": sorted(reasons),
                    "details": details,
                    "confidence": trace.get("confidence"),
                    "use_count": use_count,
                    "success_count": success_count,
                    "failure_count": failure_count,
                    "proposed_at": timestamp,
                }
            )

    proposals.sort(key=lambda item: (-len(item["reasons"]), str(item.get("trace_id") or "")))
    if max_deprecations is not None:
        return proposals[:max_deprecations]
    return proposals


def append_deprecation_proposals(
    cell_path: PathLike, proposals: List[JsonRecord]
) -> int:
    """Append deprecation proposals to ledger/deprecation_proposals.jsonl."""
    path = Path(cell_path) / "ledger" / "deprecation_proposals.jsonl"
    for proposal in proposals:
        append_jsonl(path, proposal)
    return len(proposals)


def decay_summary(cell_path: PathLike) -> Dict[str, Any]:
    """Return aggregate proposal counts by reason for a Cell."""
    traces = _read_records(Path(cell_path) / "traces" / "approved.jsonl")
    proposals = propose_deprecations(cell_path)
    counts: Counter[str] = Counter()
    for proposal in proposals:
        counts.update(proposal.get("reasons", []))
    return {
        "total_approved": len(traces),
        "total_deprecation_proposals": len(proposals),
        "reasons_breakdown": {key: counts[key] for key in sorted(counts)},
        "stale_count": counts.get("stale", 0),
        "harmful_count": counts.get("harmful", 0),
        "underperforming_count": counts.get("underperforming", 0),
        "superseded_count": counts.get("superseded", 0),
        "unsupported_count": counts.get("unsupported", 0),
    }


def _read_records(path: PathLike) -> List[JsonRecord]:
    path = Path(path)
    if not path.exists():
        return []
    return [record for _line, record in read_jsonl(path)]


def _superseded_trace_ids(traces: List[JsonRecord]) -> set[str]:
    by_statement: Dict[str, List[JsonRecord]] = defaultdict(list)
    for trace in traces:
        statement = str(trace.get("statement") or "").strip().lower()
        if statement:
            by_statement[statement].append(trace)

    superseded: set[str] = set()
    for group in by_statement.values():
        if len(group) < 2:
            continue
        ranked = sorted(
            group,
            key=lambda item: (
                float(item.get("confidence") or 0.0),
                int(item.get("success_count") or 0),
                str(item.get("trace_id") or ""),
            ),
            reverse=True,
        )
        for trace in ranked[1:]:
            if trace.get("trace_id") is not None:
                superseded.add(str(trace["trace_id"]))
    return superseded


def _proposal_id(trace_id: str, reasons: List[str]) -> str:
    reason_slug = "-".join(sorted(reasons))
    return f"deprecate-{trace_id}-{reason_slug}"
