"""Outcome learning loop for ShyftR.

Records whether retrieved memory helped, computes Trace usage counters,
emits missing-memory candidates, and preserves append-only ledger truth.

ShyftR doctrine: JSONL ledgers are canonical truth; Outcome learning
must not directly create approved Traces or Doctrine.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .ledger import append_jsonl, read_jsonl
from .models import Outcome
from .policy import check_source_boundary

PathLike = Union[str, Path]

# Valid miss types for Loadout/Pack misses.
VALID_MISS_TYPES = frozenset(
    {"not_relevant", "not_actionable", "contradicted", "duplicative", "unknown"}
)


# ---------------------------------------------------------------------------
# PackMiss — typed record for a single Loadout/Pack miss
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PackMiss:
    """A Charge that was retrieved but not applied or contradicted.

    Fields
    ------
    charge_id : the Trace/Charge ID that was missed
    miss_type : one of not_relevant, not_actionable, contradicted,
                duplicative, unknown
    reason : optional human-readable explanation
    """

    charge_id: str
    miss_type: str
    reason: Optional[str] = None

    def __post_init__(self) -> None:
        if self.miss_type not in VALID_MISS_TYPES:
            raise ValueError(
                f"Invalid miss_type '{self.miss_type}'. "
                f"Must be one of: {sorted(VALID_MISS_TYPES)}"
            )

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "charge_id": self.charge_id,
            "miss_type": self.miss_type,
        }
        if self.reason is not None:
            d["reason"] = self.reason
        return d


# ---------------------------------------------------------------------------
# Missing-memory candidate
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MissingMemoryCandidate:
    """A Source/Fragment candidate emitted from missing-memory items.

    These remain candidates/untrusted and must not bypass review or
    Trace promotion.
    """

    candidate_id: str
    cell_id: str
    source_text: str
    missing_from_loadout_id: str
    emitted_at: str
    review_status: str = "pending"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "cell_id": self.cell_id,
            "source_text": self.source_text,
            "missing_from_loadout_id": self.missing_from_loadout_id,
            "emitted_at": self.emitted_at,
            "review_status": self.review_status,
        }


# ---------------------------------------------------------------------------
# Usage counters
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TraceUsageCounters:
    """Aggregated usage counters for a single Trace."""

    trace_id: str
    use_count: int
    success_count: int
    failure_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "use_count": self.use_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
        }


# ---------------------------------------------------------------------------
# Cell data readers
# ---------------------------------------------------------------------------


def _read_cell_id(cell_path: Path) -> str:
    """Read cell_id from the Cell manifest."""
    manifest_path = cell_path / "config" / "cell_manifest.json"
    if not manifest_path.exists():
        raise ValueError(f"Cell manifest does not exist: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    cell_id = manifest.get("cell_id")
    if not cell_id:
        raise ValueError("Cell manifest is missing cell_id")
    return str(cell_id)


def _read_outcomes(cell_path: Path) -> List[Dict[str, Any]]:
    """Read all Outcome rows from ledger/outcomes.jsonl."""
    ledger = cell_path / "ledger" / "outcomes.jsonl"
    if not ledger.exists():
        return []
    return [record for _, record in read_jsonl(ledger)]


# ---------------------------------------------------------------------------
# Pack/retrieval log reader
# ---------------------------------------------------------------------------


def _read_pack_trace_ids(cell_path: Path, loadout_id: str) -> List[str]:
    """Read guidance Trace IDs associated with a Pack/Loadout.

    Prefer the append-only ``ledger/retrieval_logs.jsonl`` records written by
    Loadout assembly.  Those rows carry the selected IDs plus AL-3 role
    partitions, so Pack miss learning can focus on selected guidance rather
    than treating cautionary/background rows as misses.  A legacy
    ``store/loadouts/*.json`` fallback is retained for older fixture data.
    """

    retrieval_log = cell_path / "ledger" / "retrieval_logs.jsonl"
    if retrieval_log.exists():
        selected: List[str] = []
        caution_ids: set[str] = set()
        for _line, record in read_jsonl(retrieval_log):
            if str(record.get("loadout_id") or "") != str(loadout_id):
                continue
            selected = [str(tid) for tid in record.get("selected_ids", [])]
            caution_ids = {str(tid) for tid in record.get("caution_ids", [])}
        if selected:
            return [tid for tid in selected if tid not in caution_ids]

    pack_dir = cell_path / "store" / "loadouts"
    if not pack_dir.exists():
        return []
    for fpath in pack_dir.iterdir():
        if not fpath.suffix == ".json":
            continue
        try:
            pack = json.loads(fpath.read_text(encoding="utf-8"))
            if pack.get("loadout_id") == loadout_id:
                return [str(tid) for tid in pack.get("trace_ids", [])]
        except (json.JSONDecodeError, OSError):
            continue
    return []


def _normalise_pack_miss_details(details: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Validate and normalise structured Pack miss detail dictionaries."""
    normalised: List[Dict[str, Any]] = []
    for detail in details:
        charge_id = str(detail.get("charge_id") or "")
        if not charge_id:
            continue
        miss_type = str(detail.get("miss_type") or "unknown")
        reason = detail.get("reason")
        normalised.append(PackMiss(charge_id=charge_id, miss_type=miss_type, reason=reason).to_dict())
    return normalised


# ---------------------------------------------------------------------------
# Miss derivation
# ---------------------------------------------------------------------------


def derive_pack_misses(
    pack_trace_ids: List[str],
    applied_trace_ids: List[str],
    useful_trace_ids: List[str],
    harmful_trace_ids: List[str],
    ignored_charge_ids: Optional[List[str]] = None,
    ignored_caution_ids: Optional[List[str]] = None,
    contradicted_charge_ids: Optional[List[str]] = None,
    over_retrieved_charge_ids: Optional[List[str]] = None,
) -> List[PackMiss]:
    """Derive PackMiss records by comparing Pack contents against an Outcome.

    For each Trace/Charge in the Pack that was NOT applied or that was
    contradicted, a PackMiss is emitted with a miss_type:

    - **contradicted**: the Charge was explicitly marked as contradicted.
    - **not_relevant**: the Charge was over-retrieved (retrieved but
      judged irrelevant).
    - **not_actionable**: the Charge was in the Pack but was ignored
      (applied or offered but not used).
    - **duplicative**: the Charge appears in both useful and harmful
      — the overlap signals split opinion, treated as duplicative.
    - **unknown**: the Charge was in the Pack and not mentioned in any
      feedback list (not applied, not useful, not harmful, not ignored,
      not contradicted, not over-retrieved).

    Parameters
    ----------
    pack_trace_ids : list of Trace IDs from the Pack/Loadout
    applied_trace_ids : Traces that were actually applied
    useful_trace_ids : Traces that proved helpful
    harmful_trace_ids : Traces that proved harmful
    ignored_charge_ids : Charges that were applied or offered but not used
    ignored_caution_ids : Cautionary Charges that were bypassed
    contradicted_charge_ids : Charges explicitly contradicted
    over_retrieved_charge_ids : Charges retrieved but judged irrelevant

    Returns
    -------
    List of PackMiss records.
    """
    applied = set(applied_trace_ids)
    useful = set(useful_trace_ids)
    harmful = set(harmful_trace_ids)
    ignored = set(ignored_charge_ids or [])
    cautioned = set(ignored_caution_ids or [])
    contradicted = set(contradicted_charge_ids or [])
    over_retrieved = set(over_retrieved_charge_ids or [])

    missed: List[PackMiss] = []

    for tid in pack_trace_ids:
        if tid in applied:
            continue

        # Priority: contradicted > over-retrieved > ignored > useful+harmful overlap > default
        if tid in contradicted:
            missed.append(PackMiss(charge_id=tid, miss_type="contradicted"))
        elif tid in over_retrieved:
            missed.append(PackMiss(charge_id=tid, miss_type="not_relevant"))
        elif tid in ignored or tid in cautioned:
            missed.append(PackMiss(charge_id=tid, miss_type="not_actionable"))
        elif tid in useful and tid in harmful:
            missed.append(PackMiss(charge_id=tid, miss_type="duplicative"))
        elif tid in useful or tid in harmful:
            continue
        else:
            missed.append(PackMiss(charge_id=tid, miss_type="unknown"))

    return missed


def pack_misses_to_details(misses: List[PackMiss]) -> List[Dict[str, Any]]:
    """Convert PackMiss list to detail dicts for Outcome storage."""
    return [m.to_dict() for m in misses]


def pack_misses_to_ids(misses: List[PackMiss]) -> List[str]:
    """Extract charge_id list from PackMiss records for backward compat."""
    return [m.charge_id for m in misses]


# ---------------------------------------------------------------------------
# Miss summary computation
# ---------------------------------------------------------------------------


def compute_miss_summary(
    outcomes: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Summarise miss behaviour across a set of Outcome records.

    Returns a dict with:

    - ``misses_by_charge`` : dict mapping charge_id -> miss count
    - ``misses_by_type`` : dict mapping miss_type -> count
    - ``over_retrieved_by_charge`` : dict mapping charge_id ->
      over-retrieved count
    - ``charges_with_mixed_signal`` : list of charge_ids that appear in
      both useful and harmful in any Outcome
    """
    from collections import Counter

    misses_by_charge: Counter[str] = Counter()
    misses_by_type: Counter[str] = Counter()
    over_retrieved_by_charge: Counter[str] = Counter()
    mixed_signal_charges: set[str] = set()

    for outcome in outcomes:
        # Count structured miss details first; fall back to legacy flat ids.
        miss_rows = outcome.get("pack_miss_details") or outcome.get("pack_misses", [])
        for pm in miss_rows:
            if isinstance(pm, dict):
                cid = str(pm.get("charge_id") or "")
                mtype = str(pm.get("miss_type") or "unknown")
            else:
                cid = str(pm)
                mtype = "unknown"
            if not cid:
                continue
            misses_by_charge[cid] += 1
            misses_by_type[mtype] += 1

        # Count over-retrieved
        for oid in outcome.get("over_retrieved_charge_ids", []):
            over_retrieved_by_charge[str(oid)] += 1

        # Detect mixed signal: charge in both useful and harmful
        meta = outcome.get("metadata", {})
        useful_set = set(str(t) for t in meta.get("useful_trace_ids", []))
        harmful_set = set(str(t) for t in meta.get("harmful_trace_ids", []))
        overlap = useful_set & harmful_set
        if overlap:
            mixed_signal_charges.update(overlap)

    return {
        "total_misses": sum(misses_by_charge.values()),
        "misses_by_charge": dict(
            sorted(misses_by_charge.items(), key=lambda x: -x[1])
        ),
        "misses_by_type": dict(
            sorted(misses_by_type.items(), key=lambda x: -x[1])
        ),
        "over_retrieved_by_charge": dict(
            sorted(over_retrieved_by_charge.items(), key=lambda x: -x[1])
        ),
        "charges_with_mixed_signal": sorted(mixed_signal_charges),
    }


# ---------------------------------------------------------------------------
# Core: record_outcome
# ---------------------------------------------------------------------------


def record_outcome(
    cell_path: PathLike,
    loadout_id: str,
    result: str,
    applied_trace_ids: List[str],
    useful_trace_ids: List[str],
    harmful_trace_ids: List[str],
    missing_memory: List[str],
    verification_evidence: Optional[Dict[str, Any]] = None,
    ignored_charge_ids: Optional[List[str]] = None,
    ignored_caution_ids: Optional[List[str]] = None,
    contradicted_charge_ids: Optional[List[str]] = None,
    over_retrieved_charge_ids: Optional[List[str]] = None,
    pack_misses: Optional[List[str]] = None,
    pack_miss_details: Optional[List[Dict[str, Any]]] = None,
) -> Outcome:
    """Record an Outcome and append it to the Cell ledger.

    Parameters
    ----------
    cell_path : path to the Cell directory
    loadout_id : the Loadout that was used
    result : verdict string (e.g. "success", "failure", "partial")
    applied_trace_ids : all Traces that were applied during the task
    useful_trace_ids : Traces that proved helpful
    harmful_trace_ids : Traces that proved harmful or contradicted
    missing_memory : text items the agent needed but could not find
    verification_evidence : optional dict with verification details
    ignored_charge_ids : applied or offered Charges that were not used
    ignored_caution_ids : cautionary Charges that were bypassed
    contradicted_charge_ids : Charges contradicted by the task result
    over_retrieved_charge_ids : Charges retrieved but judged irrelevant
    pack_misses : missing Loadout/Pack coverage notes (flat string list,
        backward-compatible)
    pack_miss_details : structured PackMiss detail dicts with
        ``charge_id``, ``miss_type``, and optional ``reason``

    Returns
    -------
    The appended Outcome record.

    Side effects
    -------------
    - Appends an Outcome row to ledger/outcomes.jsonl
    - Appends missing-memory Source candidates to ledger/missing_memory_candidates.jsonl
    - Does NOT directly modify Trace confidence (use confidence.adjust_confidence)
    """
    cell = Path(cell_path)
    now = datetime.now(timezone.utc).isoformat()
    cell_id = _read_cell_id(cell)

    outcome_id = f"oc-{uuid.uuid4().hex[:12]}"

    # Resolve Pack miss ids/details.  Explicit structured details are
    # validated first; otherwise derive misses from the linked Pack retrieval
    # log and outcome feedback.  Legacy flat ids remain supported.
    resolved_pack_miss_details: List[Dict[str, Any]] = []
    if pack_miss_details:
        resolved_pack_miss_details = _normalise_pack_miss_details(pack_miss_details)
    elif pack_misses:
        resolved_pack_miss_details = [
            PackMiss(charge_id=str(charge_id), miss_type="unknown").to_dict()
            for charge_id in pack_misses
        ]
    else:
        pack_trace_ids = _read_pack_trace_ids(cell, loadout_id)
        resolved_pack_miss_details = pack_misses_to_details(
            derive_pack_misses(
                pack_trace_ids=pack_trace_ids,
                applied_trace_ids=applied_trace_ids,
                useful_trace_ids=useful_trace_ids,
                harmful_trace_ids=harmful_trace_ids,
                ignored_charge_ids=ignored_charge_ids,
                ignored_caution_ids=ignored_caution_ids,
                contradicted_charge_ids=contradicted_charge_ids,
                over_retrieved_charge_ids=over_retrieved_charge_ids,
            )
        )
    resolved_pack_misses: List[str] = [
        str(detail["charge_id"]) for detail in resolved_pack_miss_details
    ]

    outcome = Outcome(
        outcome_id=outcome_id,
        cell_id=cell_id,
        loadout_id=loadout_id,
        task_id=f"task-{uuid.uuid4().hex[:8]}",
        verdict=result,
        trace_ids=applied_trace_ids,
        ignored_charge_ids=ignored_charge_ids or [],
        ignored_caution_ids=ignored_caution_ids or [],
        contradicted_charge_ids=contradicted_charge_ids or [],
        over_retrieved_charge_ids=over_retrieved_charge_ids or [],
        pack_misses=resolved_pack_misses,
        pack_miss_details=resolved_pack_miss_details,
        score=None,
        observed_at=now,
        metadata={
            "useful_trace_ids": useful_trace_ids,
            "harmful_trace_ids": harmful_trace_ids,
            "verification_evidence": verification_evidence or {},
        },
    )

    # Append outcome to ledger (append-only)
    outcomes_ledger = cell / "ledger" / "outcomes.jsonl"
    append_jsonl(outcomes_ledger, outcome.to_dict())

    # Emit missing-memory candidates (untrusted, must not bypass review)
    if missing_memory:
        candidates_ledger = cell / "ledger" / "missing_memory_candidates.jsonl"
        for text in missing_memory:
            # Boundary check: reject operational-state pollution
            boundary = check_source_boundary(text)
            if not boundary.accepted:
                continue
            candidate = MissingMemoryCandidate(
                candidate_id=f"mmc-{uuid.uuid4().hex[:12]}",
                cell_id=cell_id,
                source_text=text,
                missing_from_loadout_id=loadout_id,
                emitted_at=now,
            )
            append_jsonl(candidates_ledger, candidate.to_dict())

    return outcome


# ---------------------------------------------------------------------------
# Trace usage counter computation
# ---------------------------------------------------------------------------


def compute_trace_usage_counters(cell_path: PathLike) -> Dict[str, TraceUsageCounters]:
    """Compute Trace usage counters from retrieval logs and Outcome rows.

    Returns a dict mapping trace_id -> TraceUsageCounters.
    """
    cell = Path(cell_path)
    outcomes = _read_outcomes(cell)

    counters: Dict[str, TraceUsageCounters] = {}

    for outcome in outcomes:
        applied = outcome.get("trace_ids", [])
        metadata = outcome.get("metadata", {})
        useful = set(metadata.get("useful_trace_ids", []))
        harmful = set(metadata.get("harmful_trace_ids", []))
        verdict = outcome.get("verdict", "")

        for tid in applied:
            if tid not in counters:
                counters[tid] = TraceUsageCounters(
                    trace_id=tid, use_count=0, success_count=0, failure_count=0
                )
            c = counters[tid]
            # Rebuild with incremented values (frozen dataclass)
            counters[tid] = TraceUsageCounters(
                trace_id=tid,
                use_count=c.use_count + 1,
                success_count=c.success_count + (1 if tid in useful else 0),
                failure_count=c.failure_count + (1 if tid in harmful else 0),
            )

    return counters


def get_trace_counters_as_dicts(cell_path: PathLike) -> List[Dict[str, Any]]:
    """Return trace usage counters as a list of dicts for serialization."""
    return [c.to_dict() for c in compute_trace_usage_counters(cell_path).values()]
