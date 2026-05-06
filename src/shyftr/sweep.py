"""Sweep dry-run analysis for ShyftR Cell ledgers.

The Sweep is a safe maintenance pass that reads retrieval logs, Signal
(Outcome), audit sparks, confidence events, retrieval-affinity events, and
approved/deprecated/isolated Trace/Charge ledgers.  It computes per-Trace
metrics (retrieval count, application count, useful/harmful/miss counts and
rates) and emits a deterministic report of proposed actions.

Dry-run mode writes no ledger records.  With explicit proposal mode, the
Sweep appends low-authority active-learning proposal events only; it never
mutates Trace/Charge lifecycle ledgers.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
import hashlib
import json as _json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from shyftr.ledger import append_jsonl, read_jsonl

PathLike = Union[str, Path]
JsonRecord = Dict[str, Any]


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TraceMetrics:
    """Per-Trace/Charge metrics computed by the Sweep."""

    trace_id: str
    trace_kind: Optional[str] = None
    trace_status: Optional[str] = None
    confidence: Optional[float] = None
    source_fragment_ids: Tuple[str, ...] = ()
    retrieval_count: int = 0
    application_count: int = 0
    useful_count: int = 0
    harmful_count: int = 0
    miss_count: int = 0
    application_rate: Optional[float] = None
    useful_rate: Optional[float] = None
    harmful_rate: Optional[float] = None
    miss_rate: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "trace_kind": self.trace_kind,
            "trace_status": self.trace_status,
            "confidence": self.confidence,
            "source_fragment_ids": list(self.source_fragment_ids),
            "retrieval_count": self.retrieval_count,
            "application_count": self.application_count,
            "useful_count": self.useful_count,
            "harmful_count": self.harmful_count,
            "miss_count": self.miss_count,
            "application_rate": self.application_rate,
            "useful_rate": self.useful_rate,
            "harmful_rate": self.harmful_rate,
            "miss_rate": self.miss_rate,
        }


PROPOSED_ACTION_TYPES = frozenset({
    "retrieval_affinity_decrease",
    "confidence_decrease",
    "confidence_increase",
    "manual_review",
    "split_charge",
    "supersession_candidate",
})


@dataclass(frozen=True)
class ProposedAction:
    """A single proposed action from the Sweep analysis.

    Fields
    ------
    trace_id : the Trace/Charge this action targets
    action_type : one of the PROPOSED_ACTION_TYPES
    rationale : human-readable explanation for the proposal
    signal_strength : rough indicator of evidence weight (0.0-1.0)
    supporting_data : optional dict with counters or references
    """

    trace_id: str
    action_type: str
    rationale: str
    signal_strength: float = 0.5
    supporting_data: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if self.action_type not in PROPOSED_ACTION_TYPES:
            raise ValueError(
                f"Invalid action_type '{self.action_type}'. "
                f"Must be one of: {sorted(PROPOSED_ACTION_TYPES)}"
            )

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "trace_id": self.trace_id,
            "action_type": self.action_type,
            "rationale": self.rationale,
            "signal_strength": self.signal_strength,
        }
        if self.supporting_data:
            d["supporting_data"] = self.supporting_data
        return d


CONFIDENCE_PROPOSAL_ACTION_TYPES = frozenset({
    "confidence_decrease",
    "confidence_increase",
    "manual_review",
    "split_charge",
})

RETRIEVAL_AFFINITY_PROPOSAL_ACTION_TYPES = frozenset({
    "retrieval_affinity_decrease",
    "supersession_candidate",
})


@dataclass(frozen=True)
class SweepProposalEvent:
    """Append-only low-authority proposal event emitted by the Sweep."""

    proposal_event_id: str
    proposal_key: str
    cell_id: str
    trace_id: str
    action_type: str
    ledger_kind: str
    event_status: str
    rationale: str
    signal_strength: float
    supporting_data: Optional[Dict[str, Any]] = None
    proposed_at: str = ""

    def __post_init__(self) -> None:
        if self.action_type not in PROPOSED_ACTION_TYPES:
            raise ValueError(f"Invalid action_type '{self.action_type}'")
        if self.ledger_kind not in {"confidence", "retrieval_affinity"}:
            raise ValueError("ledger_kind must be confidence or retrieval_affinity")
        if not self.proposal_event_id:
            raise ValueError("proposal_event_id is required")
        if not self.proposal_key:
            raise ValueError("proposal_key is required")
        if not self.trace_id:
            raise ValueError("trace_id is required")

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "proposal_event_id": self.proposal_event_id,
            "proposal_key": self.proposal_key,
            "cell_id": self.cell_id,
            "trace_id": self.trace_id,
            "action_type": self.action_type,
            "ledger_kind": self.ledger_kind,
            "event_status": self.event_status,
            "rationale": self.rationale,
            "signal_strength": self.signal_strength,
            "proposed_at": self.proposed_at,
        }
        if self.supporting_data:
            payload["supporting_data"] = dict(self.supporting_data)
        return payload


@dataclass(frozen=True)
class SweepReport:
    """Complete report from a Sweep pass."""

    cell_id: str
    scanned_at: str
    dry_run: bool
    trace_metrics: Dict[str, TraceMetrics] = field(default_factory=dict)
    proposed_actions: List[ProposedAction] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    written_proposal_ids: List[str] = field(default_factory=list)
    skipped_proposal_ids: List[str] = field(default_factory=list)
    apply_low_risk_written_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cell_id": self.cell_id,
            "scanned_at": self.scanned_at,
            "dry_run": self.dry_run,
            "trace_count": len(self.trace_metrics),
            "proposed_action_count": len(self.proposed_actions),
            "summary": dict(self.summary),
            "written_proposal_ids": list(self.written_proposal_ids),
            "skipped_proposal_ids": list(self.skipped_proposal_ids),
            "apply_low_risk_written_ids": list(self.apply_low_risk_written_ids),
            "proposed_actions": [a.to_dict() for a in self.proposed_actions],
            "trace_metrics": {
                tid: m.to_dict()
                for tid, m in sorted(self.trace_metrics.items())
            },
        }


# ---------------------------------------------------------------------------
# Ledger readers
# ---------------------------------------------------------------------------


def _read_retrieval_logs(cell_path: Path) -> List[JsonRecord]:
    """Read ledger/retrieval_logs.jsonl."""
    path = cell_path / "ledger" / "retrieval_logs.jsonl"
    if not path.exists():
        return []
    return [record for _, record in read_jsonl(path)]


def _read_outcomes(cell_path: Path) -> List[JsonRecord]:
    """Read ledger/outcomes.jsonl (Signal)."""
    path = cell_path / "ledger" / "outcomes.jsonl"
    if not path.exists():
        return []
    return [record for _, record in read_jsonl(path)]


def _read_audit_sparks(cell_path: Path) -> List[JsonRecord]:
    """Read ledger/audit_sparks.jsonl."""
    path = cell_path / "ledger" / "audit_sparks.jsonl"
    if not path.exists():
        return []
    return [record for _, record in read_jsonl(path)]


def _read_confidence_events(cell_path: Path) -> List[JsonRecord]:
    """Read ledger/confidence_events.jsonl."""
    path = cell_path / "ledger" / "confidence_events.jsonl"
    if not path.exists():
        return []
    return [record for _, record in read_jsonl(path)]


def _read_retrieval_affinity_events(cell_path: Path) -> List[JsonRecord]:
    """Read ledger/retrieval_affinity_events.jsonl."""
    path = cell_path / "ledger" / "retrieval_affinity_events.jsonl"
    if not path.exists():
        return []
    return [record for _, record in read_jsonl(path)]


def _read_trace_ledgers(cell_path: Path) -> List[JsonRecord]:
    """Read all Trace/Charge ledgers under preferred charges/ and legacy traces/."""
    records: List[JsonRecord] = []
    for directory_name in ("traces", "charges"):
        ledger_dir = cell_path / directory_name
        if not ledger_dir.is_dir():
            continue
        for fpath in sorted(ledger_dir.iterdir()):
            if fpath.suffix != ".jsonl":
                continue
            for _, record in read_jsonl(fpath):
                normalized = dict(record)
                normalized.setdefault("_ledger_directory", directory_name)
                normalized.setdefault("_ledger_status", fpath.stem)
                records.append(normalized)
    return records


# ---------------------------------------------------------------------------
# Metrics computation
# ---------------------------------------------------------------------------


def compute_trace_metrics(
    cell_path: Path,
) -> Dict[str, TraceMetrics]:
    """Compute per-Trace metrics from all ledger sources.

    Reads retrieval logs to count retrievals.  Reads Outcomes (Signal) to
    count applications, useful, harmful, and misses.  Reads Trace ledgers
    to obtain kind/status/confidence metadata.

    Returns a dict mapping trace_id -> TraceMetrics.
    """
    # 1. Read all sources
    retrieval_logs = _read_retrieval_logs(cell_path)
    outcomes = _read_outcomes(cell_path)
    trace_records = _read_trace_ledgers(cell_path)

    # Build trace metadata map
    trace_meta: Dict[str, Dict[str, Any]] = {}
    for rec in trace_records:
        tid = rec.get("trace_id") or rec.get("charge_id") or ""
        if tid:
            # Keep latest record (append-only: later rows have most recent conf).
            # Charge ledgers may encode lifecycle through the file name rather
            # than a row-level status.
            source_fragment_ids = rec.get("source_fragment_ids") or rec.get("source_ids") or []
            if isinstance(source_fragment_ids, str):
                source_fragment_ids = [source_fragment_ids]
            trace_meta[str(tid)] = {
                "trace_kind": rec.get("kind"),
                "trace_status": rec.get("status") or rec.get("_ledger_status"),
                "confidence": rec.get("confidence"),
                "source_fragment_ids": tuple(str(fid) for fid in source_fragment_ids if fid),
            }

    # 2. Count retrievals per trace from retrieval logs
    retrieval_counts: Counter[str] = Counter()
    for rec in retrieval_logs:
        for tid in sorted({str(item) for item in rec.get("selected_ids", [])} | {str(item) for item in rec.get("caution_ids", [])}):
            retrieval_counts[tid] += 1

    # 3. Count applications, useful, harmful, and misses from outcomes
    app_counts: Counter[str] = Counter()
    useful_counts: Counter[str] = Counter()
    harmful_counts: Counter[str] = Counter()
    miss_counts: Counter[str] = Counter()

    for outcome in outcomes:
        applied = outcome.get("trace_ids", [])
        meta = outcome.get("metadata", {})
        useful = meta.get("useful_trace_ids", [])
        harmful = meta.get("harmful_trace_ids", [])
        miss_details = outcome.get("pack_miss_details", [])
        flat_pack_misses = outcome.get("pack_misses", [])

        for tid in applied:
            app_counts[str(tid)] += 1
        for tid in useful:
            useful_counts[str(tid)] += 1
        for tid in harmful:
            harmful_counts[str(tid)] += 1

        # Count structured miss details
        seen_miss_ids: set[str] = set()
        for md in miss_details:
            cid = str(md.get("charge_id", ""))
            if cid:
                miss_counts[cid] += 1
                seen_miss_ids.add(cid)
        # Flat fallback for legacy records
        for cid in flat_pack_misses:
            if str(cid) not in seen_miss_ids:
                miss_counts[str(cid)] += 1

    # 4. Build TraceMetrics with rates
    all_trace_ids = (
        set(retrieval_counts.keys())
        | set(app_counts.keys())
        | set(useful_counts.keys())
        | set(harmful_counts.keys())
        | set(miss_counts.keys())
        | set(trace_meta.keys())
    )

    metrics: Dict[str, TraceMetrics] = {}
    for tid in sorted(all_trace_ids):
        rc = retrieval_counts.get(tid, 0)
        ac = app_counts.get(tid, 0)
        uc = useful_counts.get(tid, 0)
        hc = harmful_counts.get(tid, 0)
        mc = miss_counts.get(tid, 0)

        app_rate = round(ac / rc, 4) if rc > 0 else None
        useful_rate = round(uc / ac, 4) if ac > 0 else None
        harmful_rate = round(hc / ac, 4) if ac > 0 else None
        miss_rate = round(mc / rc, 4) if rc > 0 else None

        meta = trace_meta.get(tid, {})
        metrics[tid] = TraceMetrics(
            trace_id=tid,
            trace_kind=meta.get("trace_kind"),
            trace_status=meta.get("trace_status"),
            confidence=meta.get("confidence"),
            source_fragment_ids=tuple(meta.get("source_fragment_ids") or ()),
            retrieval_count=rc,
            application_count=ac,
            useful_count=uc,
            harmful_count=hc,
            miss_count=mc,
            application_rate=app_rate,
            useful_rate=useful_rate,
            harmful_rate=harmful_rate,
            miss_rate=miss_rate,
        )

    return metrics


# ---------------------------------------------------------------------------
# Action proposal logic
# ---------------------------------------------------------------------------


def _fragment_to_trace_ids(metrics: Dict[str, TraceMetrics]) -> Dict[str, Tuple[str, ...]]:
    """Build a deterministic fragment_id -> Trace/Charge ids lookup."""
    lookup: Dict[str, List[str]] = defaultdict(list)
    for trace_id, metric in metrics.items():
        for fragment_id in metric.source_fragment_ids:
            lookup[fragment_id].append(trace_id)
    return {key: tuple(sorted(values)) for key, values in lookup.items()}


def _record_trace_ids(
    record: JsonRecord,
    fragment_trace_ids: Dict[str, Tuple[str, ...]],
) -> Tuple[str, ...]:
    """Return Trace/Charge ids referenced by an active-learning event row.

    Existing active-learning ledgers use result_id for retrieval-affinity rows
    and fragment_id for confidence/audit rows. Transitional rows may already
    carry trace_id/charge_id; all forms are accepted.
    """
    direct_ids: List[str] = []
    for key in (
        "trace_id",
        "charge_id",
        "target_trace_id",
        "target_charge_id",
        "result_id",
    ):
        value = record.get(key)
        if value:
            direct_ids.append(str(value))
    fragment_id = record.get("fragment_id")
    if fragment_id:
        direct_ids.extend(fragment_trace_ids.get(str(fragment_id), ()))
    return tuple(sorted(set(direct_ids)))


def _event_counts_by_trace(
    records: Sequence[JsonRecord],
    fragment_trace_ids: Dict[str, Tuple[str, ...]],
) -> Counter[str]:
    """Count event rows by their target Trace/Charge id."""
    counts: Counter[str] = Counter()
    for record in records:
        for trace_id in _record_trace_ids(record, fragment_trace_ids):
            counts[trace_id] += 1
    return counts


def _clamped_signal_strength(base: float, event_count: int) -> float:
    """Bump signal strength with event-history support while staying bounded."""
    return min(1.0, round(base + min(event_count, 5) * 0.05, 4))


def propose_actions(
    metrics: Dict[str, TraceMetrics],
    retrieval_affinity_events: List[JsonRecord],
    confidence_events: List[JsonRecord],
    audit_sparks: List[JsonRecord],
) -> List[ProposedAction]:
    """Derive proposed actions from computed metrics and event history.

    Proposal rules (deterministic, stable across repeated runs):
    - **retrieval_affinity_decrease**: Trace has >= 3 misses and miss_rate > 0.5
    - **confidence_decrease**: Trace has >= 1 harmful application
    - **confidence_increase**: Trace has >= 3 useful applications and
      useful_rate > 0.7
    - **manual_review**: Trace appears in audit sparks or has >= 5 misses
      with miss_rate > 0.8 (persistent complete failure)
    - **split_charge**: Trace appears in both useful and harmful outcomes
      (mixed signal)
    - **supersession_candidate**: Trace has 0 retrievals and is deprecated
      or isolated — it has been superseded

    The read-only event ledgers are used as support evidence. They are surfaced
    in supporting_data and contribute bounded signal-strength increases so
    reports explain how existing confidence/retrieval-affinity history informed
    the proposal.
    """
    actions: List[ProposedAction] = []

    fragment_trace_ids = _fragment_to_trace_ids(metrics)
    retrieval_event_counts = _event_counts_by_trace(retrieval_affinity_events, fragment_trace_ids)
    confidence_event_counts = _event_counts_by_trace(confidence_events, fragment_trace_ids)

    trace_ids_in_audit: set[str] = set()
    for record in audit_sparks:
        trace_ids_in_audit.update(_record_trace_ids(record, fragment_trace_ids))

    mixed_signal_tids: set[str] = set()
    for tid, m in metrics.items():
        if m.useful_count > 0 and m.harmful_count > 0:
            mixed_signal_tids.add(tid)

    all_trace_ids: set[str] = set(metrics.keys()) | trace_ids_in_audit

    for tid in sorted(all_trace_ids):
        m = metrics.get(tid)
        retrieval_event_count = retrieval_event_counts.get(tid, 0)
        confidence_event_count = confidence_event_counts.get(tid, 0)

        if m is None:
            if tid in trace_ids_in_audit:
                actions.append(ProposedAction(
                    trace_id=tid,
                    action_type="manual_review",
                    rationale="Trace appears in audit sparks; requires human review",
                    signal_strength=_clamped_signal_strength(0.8, confidence_event_count),
                    supporting_data={
                        "audit_spark_present": True,
                        "confidence_event_count": confidence_event_count,
                        "retrieval_affinity_event_count": retrieval_event_count,
                    },
                ))
            continue

        if m.miss_count >= 3 and m.miss_rate is not None and m.miss_rate > 0.5:
            actions.append(ProposedAction(
                trace_id=tid,
                action_type="retrieval_affinity_decrease",
                rationale=(
                    f"Trace retrieved {m.retrieval_count} time(s) with "
                    f"{m.miss_count} misses ({m.miss_rate:.0%} miss rate); "
                    f"repeated misses suggest retrieval affinity should decrease"
                ),
                signal_strength=_clamped_signal_strength(0.6, retrieval_event_count),
                supporting_data={
                    "retrieval_count": m.retrieval_count,
                    "miss_count": m.miss_count,
                    "miss_rate": m.miss_rate,
                    "retrieval_affinity_event_count": retrieval_event_count,
                },
            ))

        if m.harmful_count >= 1:
            actions.append(ProposedAction(
                trace_id=tid,
                action_type="confidence_decrease",
                rationale=(
                    f"Trace had {m.harmful_count} harmful application(s); "
                    f"confidence should decrease"
                ),
                signal_strength=_clamped_signal_strength(0.7, confidence_event_count),
                supporting_data={
                    "harmful_count": m.harmful_count,
                    "confidence_event_count": confidence_event_count,
                },
            ))

        if m.useful_count >= 3 and m.useful_rate is not None and m.useful_rate > 0.7:
            actions.append(ProposedAction(
                trace_id=tid,
                action_type="confidence_increase",
                rationale=(
                    f"Trace had {m.useful_count} useful application(s) "
                    f"({m.useful_rate:.0%} useful rate); consistently useful "
                    f"warrants confidence increase"
                ),
                signal_strength=_clamped_signal_strength(0.5, confidence_event_count),
                supporting_data={
                    "useful_count": m.useful_count,
                    "useful_rate": m.useful_rate,
                    "confidence_event_count": confidence_event_count,
                },
            ))

        if tid in trace_ids_in_audit:
            actions.append(ProposedAction(
                trace_id=tid,
                action_type="manual_review",
                rationale="Trace appears in audit sparks; requires human review",
                signal_strength=_clamped_signal_strength(0.8, confidence_event_count),
                supporting_data={
                    "audit_spark_present": True,
                    "confidence_event_count": confidence_event_count,
                    "retrieval_affinity_event_count": retrieval_event_count,
                },
            ))
        elif m.miss_count >= 5 and m.miss_rate is not None and m.miss_rate > 0.8:
            actions.append(ProposedAction(
                trace_id=tid,
                action_type="manual_review",
                rationale=(
                    f"Trace has {m.miss_count} misses with {m.miss_rate:.0%} "
                    f"miss rate; persistent complete failure warrants review"
                ),
                signal_strength=_clamped_signal_strength(0.7, retrieval_event_count),
                supporting_data={
                    "miss_count": m.miss_count,
                    "miss_rate": m.miss_rate,
                    "retrieval_affinity_event_count": retrieval_event_count,
                },
            ))

        if tid in mixed_signal_tids:
            actions.append(ProposedAction(
                trace_id=tid,
                action_type="split_charge",
                rationale=(
                    f"Trace appears in both useful ({m.useful_count}) and harmful "
                    f"({m.harmful_count}) outcomes; mixed signal suggests it "
                    f"should be split into separate Traces"
                ),
                signal_strength=_clamped_signal_strength(0.6, confidence_event_count),
                supporting_data={
                    "useful_count": m.useful_count,
                    "harmful_count": m.harmful_count,
                    "confidence_event_count": confidence_event_count,
                },
            ))

        status = m.trace_status or ""
        if m.retrieval_count == 0 and status in ("deprecated", "isolated"):
            actions.append(ProposedAction(
                trace_id=tid,
                action_type="supersession_candidate",
                rationale=(
                    f"Trace is {status} with 0 retrievals; no evidence of "
                    f"continued use — candidate for supersession"
                ),
                signal_strength=_clamped_signal_strength(0.4, retrieval_event_count),
                supporting_data={
                    "trace_status": status,
                    "retrieval_count": m.retrieval_count,
                    "retrieval_affinity_event_count": retrieval_event_count,
                },
            ))

    return actions

# ---------------------------------------------------------------------------
# Summary computation
# ---------------------------------------------------------------------------


def _compute_summary(
    metrics: Dict[str, TraceMetrics],
    actions: List[ProposedAction],
) -> Dict[str, Any]:
    """Compute top-level summary for the SweepReport."""
    action_type_counts: Counter[str] = Counter()
    for a in actions:
        action_type_counts[a.action_type] += 1

    total = len(metrics)
    with_applications = sum(1 for m in metrics.values() if m.application_count > 0)
    with_misses = sum(1 for m in metrics.values() if m.miss_count > 0)
    with_harmful = sum(1 for m in metrics.values() if m.harmful_count > 0)
    with_useful = sum(1 for m in metrics.values() if m.useful_count > 0)
    with_retrievals = sum(1 for m in metrics.values() if m.retrieval_count > 0)

    return {
        "total_traces_scanned": total,
        "traces_with_retrievals": with_retrievals,
        "traces_with_applications": with_applications,
        "traces_with_misses": with_misses,
        "traces_with_harmful": with_harmful,
        "traces_with_useful": with_useful,
        "total_proposed_actions": len(actions),
        "proposed_actions_by_type": dict(
            sorted(action_type_counts.items(), key=lambda x: -x[1])
        ),
    }


# ---------------------------------------------------------------------------
# Proposal-event writing (AL-6)
# ---------------------------------------------------------------------------


def _proposal_ledger_kind(action_type: str) -> str:
    if action_type in CONFIDENCE_PROPOSAL_ACTION_TYPES:
        return "confidence"
    if action_type in RETRIEVAL_AFFINITY_PROPOSAL_ACTION_TYPES:
        return "retrieval_affinity"
    raise ValueError(f"Unsupported proposal action_type: {action_type}")


def _stable_payload(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _stable_payload(v) for k, v in sorted(value.items())}
    if isinstance(value, (list, tuple, set)):
        return [_stable_payload(v) for v in value]
    return value


def _proposal_key(cell_id: str, action: ProposedAction) -> str:
    evidence = _stable_payload({
        key: value
        for key, value in (action.supporting_data or {}).items()
        if key not in {"confidence_event_count", "retrieval_affinity_event_count"}
    })
    payload = {
        "cell_id": cell_id,
        "trace_id": action.trace_id,
        "action_type": action.action_type,
        "supporting_data": evidence,
    }
    digest = hashlib.sha256(
        _json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:24]
    return f"sweep:{cell_id}:{action.trace_id}:{action.action_type}:{digest}"


def _proposal_event_id(proposal_key: str) -> str:
    digest = hashlib.sha256(proposal_key.encode("utf-8")).hexdigest()[:24]
    return f"sweep-proposal-{digest}"


def _existing_open_proposal_keys(cell: Path) -> set[str]:
    open_keys: set[str] = set()
    for rel in (
        Path("ledger/confidence_events.jsonl"),
        Path("ledger/retrieval_affinity_events.jsonl"),
    ):
        path = cell / rel
        if not path.exists():
            continue
        for _, record in read_jsonl(path):
            key = record.get("proposal_key")
            if not key:
                continue
            status = str(record.get("event_status") or record.get("proposal_status") or "proposed")
            if status not in {"accepted", "rejected", "resolved", "closed"}:
                open_keys.add(str(key))
    return open_keys


def _action_to_event(
    *,
    cell_id: str,
    action: ProposedAction,
    proposed_at: str,
    apply_low_risk: bool,
) -> SweepProposalEvent:
    ledger_kind = _proposal_ledger_kind(action.action_type)
    key = _proposal_key(cell_id, action)
    status = "applied_low_risk" if (
        apply_low_risk and action.action_type == "retrieval_affinity_decrease"
    ) else "proposed"
    return SweepProposalEvent(
        proposal_event_id=_proposal_event_id(key),
        proposal_key=key,
        cell_id=cell_id,
        trace_id=action.trace_id,
        action_type=action.action_type,
        ledger_kind=ledger_kind,
        event_status=status,
        rationale=action.rationale,
        signal_strength=action.signal_strength,
        supporting_data=action.supporting_data,
        proposed_at=proposed_at,
    )


def _event_to_ledger_record(event: SweepProposalEvent) -> Tuple[Path, Dict[str, Any]]:
    base = event.to_dict()
    if event.ledger_kind == "confidence":
        record = {
            "confidence_event_id": event.proposal_event_id,
            "cell_id": event.cell_id,
            "fragment_id": None,
            "confidence": None,
            "reason": event.rationale,
            "observed_at": event.proposed_at,
            **base,
        }
        return Path("ledger/confidence_events.jsonl"), record
    record = {
        "affinity_event_id": event.proposal_event_id,
        "cell_id": event.cell_id,
        "query": None,
        "result_id": event.trace_id,
        "score": event.signal_strength,
        "observed_at": event.proposed_at,
        **base,
    }
    return Path("ledger/retrieval_affinity_events.jsonl"), record


def _append_proposal_events(
    *,
    cell: Path,
    cell_id: str,
    actions: Sequence[ProposedAction],
    proposed_at: str,
    apply_low_risk: bool = False,
) -> Tuple[List[str], List[str], List[str]]:
    existing_keys = _existing_open_proposal_keys(cell)
    written: List[str] = []
    skipped: List[str] = []
    low_risk_written: List[str] = []
    for action in sorted(actions, key=lambda item: (item.action_type, item.trace_id, item.rationale)):
        event = _action_to_event(
            cell_id=cell_id,
            action=action,
            proposed_at=proposed_at,
            apply_low_risk=apply_low_risk,
        )
        if event.proposal_key in existing_keys:
            skipped.append(event.proposal_event_id)
            continue
        rel_path, record = _event_to_ledger_record(event)
        append_jsonl(cell / rel_path, record)
        existing_keys.add(event.proposal_key)
        written.append(event.proposal_event_id)
        if event.event_status == "applied_low_risk":
            low_risk_written.append(event.proposal_event_id)
    return written, skipped, low_risk_written


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_sweep(
    cell_path: PathLike,
    *,
    dry_run: bool = True,
    output_path: Optional[PathLike] = None,
    propose: bool = False,
    apply_low_risk: bool = False,
) -> SweepReport:
    """Run a Sweep analysis pass on a Cell.

    Parameters
    ----------
    cell_path : path to the Cell directory
    dry_run : if True (default), no ledger records are written
    output_path : optional path to write report JSON.
    propose : when True and dry_run is False, append low-authority proposal
        events to active-learning ledgers.
    apply_low_risk : when True with propose, mark retrieval-affinity decrease
        proposal events as applied_low_risk. This remains append-only and never
        mutates Trace/Charge lifecycle ledgers.

    Returns
    -------
    SweepReport with per-Trace metrics and proposed actions.
    """
    from datetime import datetime, timezone

    cell = Path(cell_path)

    # Read cell_id
    manifest_path = cell / "config" / "cell_manifest.json"
    if not manifest_path.exists():
        raise ValueError(f"Cell manifest not found: {manifest_path}")
    manifest = _json.loads(manifest_path.read_text(encoding="utf-8"))
    cell_id = str(manifest.get("cell_id", ""))

    scanned_at = datetime.now(timezone.utc).isoformat()

    # 1. Compute metrics
    trace_metrics = compute_trace_metrics(cell)

    # 2. Read event history for proposal logic
    retrieval_affinity_events = _read_retrieval_affinity_events(cell)
    confidence_events = _read_confidence_events(cell)
    audit_sparks = _read_audit_sparks(cell)

    # 3. Propose actions
    proposed_actions = propose_actions(
        trace_metrics,
        retrieval_affinity_events,
        confidence_events,
        audit_sparks,
    )

    # 4. Compute summary
    summary = _compute_summary(trace_metrics, proposed_actions)

    written_proposal_ids: List[str] = []
    skipped_proposal_ids: List[str] = []
    apply_low_risk_written_ids: List[str] = []
    if propose and not dry_run:
        written_proposal_ids, skipped_proposal_ids, apply_low_risk_written_ids = _append_proposal_events(
            cell=cell,
            cell_id=cell_id,
            actions=proposed_actions,
            proposed_at=scanned_at,
            apply_low_risk=apply_low_risk,
        )
        summary = {
            **summary,
            "proposal_events_written": len(written_proposal_ids),
            "proposal_events_skipped": len(skipped_proposal_ids),
            "apply_low_risk_events_written": len(apply_low_risk_written_ids),
        }

    # 5. Build report
    report = SweepReport(
        cell_id=cell_id,
        scanned_at=scanned_at,
        dry_run=dry_run,
        trace_metrics=trace_metrics,
        proposed_actions=proposed_actions,
        summary=summary,
        written_proposal_ids=written_proposal_ids,
        skipped_proposal_ids=skipped_proposal_ids,
        apply_low_risk_written_ids=apply_low_risk_written_ids,
    )

    # 6. Write report to output_path if provided. Proposal ledger writes, when
    # enabled, already happened above and remain append-only.
    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            _json.dumps(report.to_dict(), sort_keys=True, indent=2, default=str),
            encoding="utf-8",
        )

    return report
