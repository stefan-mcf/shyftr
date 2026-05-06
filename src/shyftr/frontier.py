"""Public-safe frontier primitives: belief, graph, simulation, modes, reputation,
regulator proposals, and synthetic eval generation.

These helpers are deliberately transparent and deterministic. They operate on
append-only JSONL ledgers and expose review/simulation surfaces without private
ranking, calibration, compaction, or auto-approval logic.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union
import json
import math
import uuid

from .ledger import append_jsonl, read_jsonl

PathLike = Union[str, Path]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _records(path: Path) -> List[Dict[str, Any]]:
    return [record for _, record in read_jsonl(path)] if path.exists() else []


# ---------------------------------------------------------------------------
# 7.1 Confidence belief baseline
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ConfidenceState:
    prior: float = 0.5
    positive_evidence_count: int = 0
    negative_evidence_count: int = 0
    context: Optional[str] = None

    def __post_init__(self) -> None:
        if not 0.0 <= float(self.prior) <= 1.0:
            raise ValueError("prior must be between 0.0 and 1.0")
        if self.positive_evidence_count < 0 or self.negative_evidence_count < 0:
            raise ValueError("evidence counts must be non-negative")

    @property
    def alpha(self) -> float:
        return 1.0 + self.prior + self.positive_evidence_count

    @property
    def beta(self) -> float:
        return 1.0 + (1.0 - self.prior) + self.negative_evidence_count

    @property
    def expected_confidence(self) -> float:
        return round(self.alpha / (self.alpha + self.beta), 4)

    @property
    def uncertainty(self) -> float:
        total = self.alpha + self.beta
        variance = (self.alpha * self.beta) / ((total ** 2) * (total + 1.0))
        return round(math.sqrt(variance) * 2.0, 4)

    @property
    def lower_bound(self) -> float:
        return round(max(0.0, self.expected_confidence - self.uncertainty), 4)

    @property
    def upper_bound(self) -> float:
        return round(min(1.0, self.expected_confidence + self.uncertainty), 4)

    @property
    def evidence_count(self) -> int:
        return self.positive_evidence_count + self.negative_evidence_count

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prior": float(self.prior),
            "positive_evidence_count": int(self.positive_evidence_count),
            "negative_evidence_count": int(self.negative_evidence_count),
            "expected_confidence": self.expected_confidence,
            "uncertainty": self.uncertainty,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "evidence_count": self.evidence_count,
            "context": self.context,
            "public_baseline": "transparent_beta_binomial",
        }

    @classmethod
    def from_memory(cls, record: Dict[str, Any]) -> "ConfidenceState":
        existing = record.get("confidence_state")
        if isinstance(existing, dict):
            return cls(
                prior=float(existing.get("prior", record.get("confidence", 0.5) or 0.5)),
                positive_evidence_count=int(existing.get("positive_evidence_count", record.get("success_count", 0) or 0)),
                negative_evidence_count=int(existing.get("negative_evidence_count", record.get("failure_count", 0) or 0)),
                context=existing.get("context"),
            )
        return cls(
            prior=float(record.get("confidence", 0.5) if record.get("confidence") is not None else 0.5),
            positive_evidence_count=int(record.get("success_count", 0) or 0),
            negative_evidence_count=int(record.get("failure_count", 0) or 0),
        )


def project_confidence_state(memory_record: Dict[str, Any]) -> Dict[str, Any]:
    state = ConfidenceState.from_memory(memory_record)
    out = dict(memory_record)
    out.setdefault("confidence", state.expected_confidence)
    out["confidence_state"] = state.to_dict()
    return out


def confidence_from_feedback(memory_record: Dict[str, Any], *, useful: int = 0, harmful: int = 0) -> Dict[str, Any]:
    state = ConfidenceState.from_memory(memory_record)
    return ConfidenceState(
        prior=state.prior,
        positive_evidence_count=state.positive_evidence_count + max(useful, 0),
        negative_evidence_count=state.negative_evidence_count + max(harmful, 0),
        context=state.context,
    ).to_dict()


# ---------------------------------------------------------------------------
# 7.2 causal memory graph foundation
# ---------------------------------------------------------------------------

ALLOWED_EDGE_TYPES = {
    "caused_success",
    "contributed_to_failure",
    "contradicted_by",
    "supersedes",
    "depends_on",
    "applies_under",
    "invalid_under",
    "co_retrieved_with",
    "ignored_with",
}

@dataclass(frozen=True)
class GraphEdge:
    edge_id: str
    source_id: str
    target_id: str
    edge_type: str
    provenance: Dict[str, Any]
    reviewer: str
    created_at: str = field(default_factory=_now)
    labels: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.edge_type not in ALLOWED_EDGE_TYPES:
            raise ValueError(f"invalid graph edge type: {self.edge_type}")
        if not self.source_id or not self.target_id:
            raise ValueError("source_id and target_id are required")
        if not self.reviewer:
            raise ValueError("reviewer is required")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "edge_type": self.edge_type,
            "provenance": dict(self.provenance),
            "reviewer": self.reviewer,
            "created_at": self.created_at,
            "labels": list(self.labels),
        }


def append_graph_edge(cell_path: PathLike, edge: GraphEdge) -> Dict[str, Any]:
    append_jsonl(Path(cell_path) / "ledger" / "graph_edges.jsonl", edge.to_dict())
    return edge.to_dict()


def list_graph_edges(cell_path: PathLike, *, source_id: Optional[str] = None, target_id: Optional[str] = None, edge_type: Optional[str] = None) -> List[Dict[str, Any]]:
    rows = _records(Path(cell_path) / "ledger" / "graph_edges.jsonl")
    if source_id:
        rows = [r for r in rows if r.get("source_id") == source_id]
    if target_id:
        rows = [r for r in rows if r.get("target_id") == target_id]
    if edge_type:
        rows = [r for r in rows if r.get("edge_type") == edge_type]
    return rows


def graph_context_for(cell_path: PathLike, item_ids: Sequence[str]) -> Dict[str, List[Dict[str, Any]]]:
    wanted = set(item_ids)
    out: Dict[str, List[Dict[str, Any]]] = {item_id: [] for item_id in item_ids}
    for edge in list_graph_edges(cell_path):
        if edge.get("source_id") in wanted:
            out.setdefault(str(edge.get("source_id")), []).append(edge)
        if edge.get("target_id") in wanted:
            out.setdefault(str(edge.get("target_id")), []).append(edge)
    return out


# ---------------------------------------------------------------------------
# 7.4 retrieval modes (used by 7.3 simulation too)
# ---------------------------------------------------------------------------

RETRIEVAL_MODES: Dict[str, Dict[str, Any]] = {
    "balanced": {"min_confidence": 0.0, "caution_max_items": 3, "include_fragments": False, "audit_mode": False, "trust_tiers": None, "description": "default-compatible balanced pack behavior"},
    "conservative": {"min_confidence": 0.55, "caution_max_items": 2, "include_fragments": False, "audit_mode": False, "trust_tiers": None, "description": "prefer established reviewed memory"},
    "exploratory": {"min_confidence": 0.0, "caution_max_items": 5, "include_fragments": True, "audit_mode": False, "trust_tiers": None, "description": "allow more candidate/background context with labels"},
    "risk_averse": {"min_confidence": 0.7, "caution_max_items": 5, "include_fragments": False, "audit_mode": False, "trust_tiers": None, "description": "exclude weak memory and surface cautions"},
    "audit": {"min_confidence": 0.0, "caution_max_items": 10, "include_fragments": True, "audit_mode": True, "trust_tiers": None, "description": "read-only audit view including challenged/quarantined records with labels"},
    "rule_only": {"min_confidence": 0.0, "caution_max_items": 0, "include_fragments": False, "audit_mode": False, "trust_tiers": ["doctrine"], "description": "return rules only"},
    "low_latency": {"min_confidence": 0.4, "caution_max_items": 1, "include_fragments": False, "audit_mode": False, "trust_tiers": None, "description": "small fast pack"},
}


def validate_retrieval_mode(mode: Optional[str]) -> str:
    selected = mode or "balanced"
    if selected not in RETRIEVAL_MODES:
        raise ValueError(f"invalid retrieval mode: {selected}")
    return selected


def retrieval_mode_config(mode: Optional[str]) -> Dict[str, Any]:
    selected = validate_retrieval_mode(mode)
    return {"mode": selected, **RETRIEVAL_MODES[selected]}


def apply_retrieval_mode_to_task(task: Any) -> Any:
    mode = retrieval_mode_config(getattr(task, "retrieval_mode", "balanced"))
    updates: Dict[str, Any] = {}
    if mode["include_fragments"]:
        updates["include_fragments"] = True
    if mode["audit_mode"]:
        updates["audit_mode"] = True
    if mode["trust_tiers"] is not None:
        updates["requested_trust_tiers"] = list(mode["trust_tiers"])
    if mode["mode"] != "balanced":
        updates["caution_max_items"] = int(mode["caution_max_items"])
    if mode["mode"] == "low_latency":
        updates["max_items"] = min(getattr(task, "max_items"), 5)
        updates["max_tokens"] = min(getattr(task, "max_tokens"), 1200)
    return replace(task, **updates) if updates else task


def filter_items_for_retrieval_mode(items: List[Any], mode_name: str) -> Tuple[List[Any], List[str]]:
    mode = retrieval_mode_config(mode_name)
    minimum = float(mode["min_confidence"])
    kept = []
    suppressed = []
    for item in items:
        conf = getattr(item, "confidence", None)
        role = getattr(item, "loadout_role", None)
        tier = getattr(item, "trust_tier", None)
        if mode_name == "rule_only" and tier != "doctrine":
            suppressed.append(getattr(item, "item_id", ""))
            continue
        if role != "caution" and conf is not None and conf < minimum:
            suppressed.append(getattr(item, "item_id", ""))
            continue
        if mode_name == "audit":
            trace = dict(getattr(item, "score_trace", {}) or {})
            trace["audit_label"] = "audit_included_review_required"
            object.__setattr__(item, "score_trace", trace)
        kept.append(item)
    return kept, [s for s in suppressed if s]


# ---------------------------------------------------------------------------
# 7.3 read-only policy simulation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SimulationRequest:
    cell_path: str
    query: str
    task_id: str = "simulation"
    current_mode: str = "balanced"
    proposed_mode: str = "balanced"
    max_items: int = 20
    max_tokens: int = 4000

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


def simulate_policy(request: SimulationRequest) -> Dict[str, Any]:
    from .pack import LoadoutTaskInput, assemble_loadout

    before_counts = _ledger_line_counts(Path(request.cell_path))
    current = assemble_loadout(LoadoutTaskInput(
        cell_path=request.cell_path,
        query=request.query,
        task_id=f"{request.task_id}-current",
        max_items=request.max_items,
        max_tokens=request.max_tokens,
        retrieval_mode=request.current_mode,
        dry_run=True,
    ))
    proposed = assemble_loadout(LoadoutTaskInput(
        cell_path=request.cell_path,
        query=request.query,
        task_id=f"{request.task_id}-proposed",
        max_items=request.max_items,
        max_tokens=request.max_tokens,
        retrieval_mode=request.proposed_mode,
        dry_run=True,
    ))
    after_counts = _ledger_line_counts(Path(request.cell_path))
    current_ids = [item.item_id for item in current.items]
    proposed_ids = [item.item_id for item in proposed.items]
    report = {
        "status": "ok",
        "simulation_id": f"sim-{uuid.uuid4().hex[:12]}",
        "read_only": before_counts == after_counts,
        "request": request.to_dict(),
        "current_mode": request.current_mode,
        "proposed_mode": request.proposed_mode,
        "selected_ids": proposed_ids,
        "current_ids": current_ids,
        "missed_ids": [i for i in current_ids if i not in proposed_ids],
        "added_ids": [i for i in proposed_ids if i not in current_ids],
        "changed_order": current_ids != proposed_ids,
        "caution_labels": _caution_labels(proposed.to_dict()),
        "estimated_token_usage": {"current": current.total_tokens, "proposed": proposed.total_tokens},
        "ledger_counts_before": before_counts,
        "ledger_counts_after": after_counts,
        "auto_apply": False,
        "application_requires_operator_review": True,
    }
    return report


def _ledger_line_counts(cell: Path) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for p in sorted((cell / "ledger").rglob("*.jsonl")):
        out[str(p.relative_to(cell))] = len([line for line in p.read_text(encoding="utf-8").splitlines() if line.strip()])
    return out


def _caution_labels(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {"item_id": item.get("item_id"), "label": item.get("loadout_role"), "score_trace": item.get("score_trace", {})}
        for item in payload.get("items", [])
        if item.get("loadout_role") in {"caution", "conflict"} or item.get("score_trace", {}).get("audit_label")
    ]


# ---------------------------------------------------------------------------
# 7.5 reputation baseline
# ---------------------------------------------------------------------------

REPUTATION_EVENT_TYPES = {"approved", "rejected", "useful_feedback", "harmful_feedback", "contradiction", "stale_memory", "import_approved", "import_rejected"}

@dataclass(frozen=True)
class ReputationEvent:
    target_type: str
    target_id: str
    event_type: str
    provenance: Dict[str, Any]
    event_id: str = field(default_factory=lambda: f"rep-{uuid.uuid4().hex[:12]}")
    created_at: str = field(default_factory=_now)

    def __post_init__(self) -> None:
        if self.event_type not in REPUTATION_EVENT_TYPES:
            raise ValueError(f"invalid reputation event type: {self.event_type}")
        if not self.target_type or not self.target_id:
            raise ValueError("target_type and target_id are required")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "event_type": self.event_type,
            "provenance": dict(self.provenance),
            "created_at": self.created_at,
        }


def append_reputation_event(cell_path: PathLike, event: ReputationEvent) -> Dict[str, Any]:
    append_jsonl(Path(cell_path) / "ledger" / "reputation" / "events.jsonl", event.to_dict())
    return event.to_dict()


def reputation_summary(cell_path: PathLike, *, target_type: Optional[str] = None, target_id: Optional[str] = None) -> Dict[str, Any]:
    rows = _records(Path(cell_path) / "ledger" / "reputation" / "events.jsonl")
    if target_type:
        rows = [r for r in rows if r.get("target_type") == target_type]
    if target_id:
        rows = [r for r in rows if r.get("target_id") == target_id]
    grouped: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault((str(row.get("target_type")), str(row.get("target_id"))), []).append(row)
    summaries = []
    for (ttype, tid), events in sorted(grouped.items()):
        total = len(events)
        count = lambda name: sum(1 for e in events if e.get("event_type") == name)
        summaries.append({
            "target_type": ttype,
            "target_id": tid,
            "event_count": total,
            "approval_rate": round((count("approved") + count("import_approved")) / total, 4) if total else 0.0,
            "rejection_rate": round((count("rejected") + count("import_rejected")) / total, 4) if total else 0.0,
            "useful_feedback_rate": round(count("useful_feedback") / total, 4) if total else 0.0,
            "harmful_feedback_rate": round(count("harmful_feedback") / total, 4) if total else 0.0,
            "contradiction_rate": round(count("contradiction") / total, 4) if total else 0.0,
            "stale_memory_rate": round(count("stale_memory") / total, 4) if total else 0.0,
            "review_priority_score": round(count("rejected") + count("harmful_feedback") * 1.5 + count("contradiction") * 2.0, 4),
            "can_bypass_review": False,
        })
    return {"status": "ok", "summaries": summaries, "total": len(summaries)}


# ---------------------------------------------------------------------------
# 7.6 regulator proposals
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RegulatorProposal:
    proposal_id: str
    impacted_area: str
    examples: List[str]
    counterexamples: List[str]
    rationale: str
    required_simulation_report_ref: Optional[str] = None
    reviewer_decision_state: str = "pending"
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "impacted_area": self.impacted_area,
            "examples": list(self.examples),
            "counterexamples": list(self.counterexamples),
            "rationale": self.rationale,
            "required_simulation_report_ref": self.required_simulation_report_ref,
            "reviewer_decision_state": self.reviewer_decision_state,
            "created_at": self.created_at,
            "auto_apply": False,
            "requires_human_review": True,
            "requires_simulation_before_policy_change": True,
        }


def generate_regulator_proposals(cell_path: PathLike, *, min_repeated: int = 2) -> List[Dict[str, Any]]:
    events = _records(Path(cell_path) / "ledger" / "regulator_events.jsonl")
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for event in events:
        kind = str(event.get("event_type") or event.get("kind") or "")
        area = str(event.get("impacted_area") or event.get("regulator_area") or "general")
        if kind in {"false_approval", "false_rejection"}:
            groups.setdefault(f"{kind}:{area}", []).append(event)
    proposals: List[Dict[str, Any]] = []
    for key, rows in sorted(groups.items()):
        if len(rows) < min_repeated:
            continue
        kind, area = key.split(":", 1)
        proposal = RegulatorProposal(
            proposal_id=f"rp-{uuid.uuid5(uuid.NAMESPACE_URL, key + str(len(rows))).hex[:12]}",
            impacted_area=area,
            examples=[str(r.get("memory_id") or r.get("candidate_id") or r.get("event_id") or i) for i, r in enumerate(rows)],
            counterexamples=[str(r.get("counterexample_id")) for r in rows if r.get("counterexample_id")],
            rationale=f"Repeated {kind.replace('_', ' ')} events suggest a review-gated regulator proposal.",
            required_simulation_report_ref=None,
        ).to_dict()
        proposals.append(proposal)
    return proposals


def append_regulator_proposals(cell_path: PathLike, proposals: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    path = Path(cell_path) / "ledger" / "regulator_proposals.jsonl"
    for proposal in proposals:
        append_jsonl(path, dict(proposal))
    return list(proposals)


def review_regulator_proposal(cell_path: PathLike, proposal_id: str, decision: str, reviewer: str, rationale: str, simulation_report_ref: Optional[str] = None) -> Dict[str, Any]:
    if decision not in {"approve", "reject", "defer"}:
        raise ValueError("decision must be approve, reject, or defer")
    if decision == "approve" and not simulation_report_ref:
        raise ValueError("approval requires a simulation_report_ref")
    event = {
        "proposal_id": proposal_id,
        "decision": decision,
        "reviewer": reviewer,
        "rationale": rationale,
        "simulation_report_ref": simulation_report_ref,
        "created_at": _now(),
        "policy_mutated": False,
    }
    append_jsonl(Path(cell_path) / "ledger" / "regulator_proposal_reviews.jsonl", event)
    return event


# ---------------------------------------------------------------------------
# 7.7 synthetic training/eval generator
# ---------------------------------------------------------------------------

def generate_eval_tasks(cell_path: PathLike) -> List[Dict[str, Any]]:
    cell = Path(cell_path)
    outcomes = _records(cell / "ledger" / "outcomes.jsonl") + _records(cell / "ledger" / "feedback.jsonl")
    memories = _records(cell / "traces" / "approved.jsonl") + _records(cell / "ledger" / "memories" / "approved.jsonl")
    tasks: List[Dict[str, Any]] = []
    for i, outcome in enumerate(outcomes):
        useful = outcome.get("useful_trace_ids") or outcome.get("useful_memory_ids") or []
        harmful = outcome.get("harmful_trace_ids") or outcome.get("harmful_memory_ids") or []
        missing = outcome.get("missing_memory") or outcome.get("missing_memory_notes") or []
        if useful or harmful or missing:
            tasks.append({
                "task_id": f"eval-feedback-{i+1}",
                "source": "synthetic_feedback_fixture",
                "provenance": {"ledger": "ledger/outcomes.jsonl", "row_index": i + 1, "outcome_id": outcome.get("outcome_id") or outcome.get("feedback_id")},
                "prompt": "Use the pack to avoid repeated memory mistakes in this synthetic scenario.",
                "expected_pack_item_ids": list(useful),
                "avoid_pack_item_ids": list(harmful),
                "expected_agent_behavior": "apply useful memory, heed caution labels, and mention missing memory only as a review-gated note",
                "private_data_allowed": False,
            })
    for memory in memories:
        conf = memory.get("confidence")
        success = int(memory.get("success_count", 0) or 0)
        if (conf is not None and float(conf) >= 0.8) or success >= 2:
            mid = str(memory.get("trace_id") or memory.get("memory_id"))
            tasks.append({
                "task_id": f"eval-memory-{mid}",
                "source": "synthetic_high_value_memory",
                "provenance": {"ledger": "traces/approved.jsonl", "memory_id": mid},
                "prompt": f"Retrieve public-safe guidance relevant to: {memory.get('statement', '')[:120]}",
                "expected_pack_item_ids": [mid],
                "avoid_pack_item_ids": [],
                "expected_agent_behavior": "use the cited memory when relevant and preserve its trust label",
                "private_data_allowed": False,
            })
    return sorted(tasks, key=lambda r: r["task_id"])


def export_eval_tasks(cell_path: PathLike, output_path: Optional[PathLike] = None, *, jsonl: bool = False) -> Dict[str, Any]:
    tasks = generate_eval_tasks(cell_path)
    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        if jsonl:
            out.write_text("".join(json.dumps(t, sort_keys=True) + "\n" for t in tasks), encoding="utf-8")
        else:
            out.write_text(json.dumps({"tasks": tasks}, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return {"status": "ok", "tasks": tasks, "total": len(tasks), "public_safe": True}
