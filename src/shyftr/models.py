from __future__ import annotations

from dataclasses import MISSING, dataclass, field, fields
import json
from typing import Any, ClassVar, Dict, List, Optional, Sequence, Type, TypeVar


T = TypeVar("T", bound="SerializableModel")


class SerializableModel:
    """Small deterministic serialization base for ShyftR lifecycle records."""

    _required_fields: ClassVar[Sequence[str]] = ()
    _non_empty_fields: ClassVar[Sequence[str]] = ()
    _bounded_fields: ClassVar[Sequence[str]] = ()

    def __post_init__(self) -> None:
        _validate_required(self, self._required_fields)
        for field_name in self._non_empty_fields:
            _validate_non_empty_string_list(field_name, getattr(self, field_name))
        for field_name in self._bounded_fields:
            value = getattr(self, field_name)
            if value is not None:
                _validate_zero_to_one(field_name, value)
        _validate_non_negative_counters(self)

    def to_dict(self) -> Dict[str, Any]:
        return {
            field.name: getattr(self, field.name)
            for field in sorted(fields(self), key=lambda item: item.name)
        }

    @classmethod
    def from_dict(cls: Type[T], payload: Dict[str, Any]) -> T:
        if not isinstance(payload, dict):
            raise ValueError(f"{cls.__name__}.from_dict requires a mapping payload")

        missing = [field_name for field_name in cls._required_fields if field_name not in payload]
        if missing:
            raise ValueError(f"Missing required field(s): {', '.join(missing)}")

        allowed = {field.name for field in fields(cls)}
        unknown = sorted(set(payload) - allowed)
        if unknown:
            raise ValueError(f"Unknown field(s): {', '.join(unknown)}")

        values = {}
        for field in fields(cls):
            if field.name in payload:
                values[field.name] = payload[field.name]
            elif field.default is not MISSING or field.default_factory is not MISSING:  # type: ignore[attr-defined]
                continue
            else:
                raise ValueError(f"Missing required field(s): {field.name}")
        return cls(**values)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls: Type[T], payload: str) -> T:
        return cls.from_dict(json.loads(payload))


def _validate_required(instance: Any, field_names: Sequence[str]) -> None:
    for field_name in field_names:
        value = getattr(instance, field_name)
        if value is None:
            raise ValueError(f"{field_name} is required")
        if isinstance(value, str) and value == "":
            raise ValueError(f"{field_name} is required")


def _validate_non_empty_string_list(field_name: str, value: Any) -> None:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    if not value:
        raise ValueError(f"{field_name} must contain at least one entry")
    if any(not isinstance(item, str) or item == "" for item in value):
        raise ValueError(f"{field_name} entries must be non-empty strings")


def _validate_zero_to_one(field_name: str, value: Any) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{field_name} must be a number between 0.0 and 1.0")
    if value < 0.0 or value > 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


def _validate_non_negative_counters(instance: Any) -> None:
    for field_name in ("use_count", "success_count", "failure_count"):
        if not hasattr(instance, field_name):
            continue
        value = getattr(instance, field_name)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"{field_name} must be a non-negative integer")


@dataclass(frozen=True)
class Source(SerializableModel):
    source_id: str
    cell_id: str
    kind: str
    sha256: str
    captured_at: str
    uri: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    _required_fields: ClassVar[Sequence[str]] = (
        "source_id",
        "cell_id",
        "kind",
        "sha256",
        "captured_at",
    )


@dataclass(frozen=True)
class Fragment(SerializableModel):
    fragment_id: str
    source_id: str
    cell_id: str
    kind: str
    text: str
    source_excerpt: Optional[str] = None
    boundary_status: str = "pending"
    review_status: str = "pending"
    confidence: Optional[float] = None
    tags: List[str] = field(default_factory=list)

    _required_fields: ClassVar[Sequence[str]] = (
        "fragment_id",
        "source_id",
        "cell_id",
        "text",
    )
    _bounded_fields: ClassVar[Sequence[str]] = ("confidence",)


TRACE_KINDS = (
    "success_pattern",
    "failure_signature",
    "anti_pattern",
    "recovery_pattern",
    "verification_heuristic",
    "routing_heuristic",
    "tool_quirk",
    "escalation_rule",
    "preference",
    "constraint",
    "workflow",
    "rail_candidate",
    "supersession",
    "scope_exception",
    "audit_finding",
)

TRACE_STATUSES = (
    "proposed",
    "approved",
    "challenged",
    "isolation_candidate",
    "isolated",
    "superseded",
    "deprecated",
)


@dataclass(frozen=True)
class Trace(SerializableModel):
    trace_id: str
    cell_id: str
    statement: str
    source_fragment_ids: List[str]
    kind: Optional[str] = None
    rationale: Optional[str] = None
    status: str = "proposed"
    confidence: Optional[float] = None
    tags: List[str] = field(default_factory=list)
    use_count: int = 0
    success_count: int = 0
    failure_count: int = 0

    _required_fields: ClassVar[Sequence[str]] = (
        "trace_id",
        "cell_id",
        "statement",
        "source_fragment_ids",
    )
    _non_empty_fields: ClassVar[Sequence[str]] = ("source_fragment_ids",)
    _bounded_fields: ClassVar[Sequence[str]] = ("confidence",)


@dataclass(frozen=True)
class Alloy(SerializableModel):
    alloy_id: str
    cell_id: str
    theme: str
    summary: str
    source_trace_ids: List[str]
    proposal_status: str = "proposed"
    confidence: Optional[float] = None

    _required_fields: ClassVar[Sequence[str]] = (
        "alloy_id",
        "cell_id",
        "theme",
        "summary",
        "source_trace_ids",
    )
    _non_empty_fields: ClassVar[Sequence[str]] = ("source_trace_ids",)
    _bounded_fields: ClassVar[Sequence[str]] = ("confidence",)


@dataclass(frozen=True)
class DoctrineProposal(SerializableModel):
    doctrine_id: str
    source_alloy_ids: List[str]
    scope: str
    statement: str
    review_status: str = "pending"

    _required_fields: ClassVar[Sequence[str]] = (
        "doctrine_id",
        "source_alloy_ids",
        "scope",
        "statement",
        "review_status",
    )
    _non_empty_fields: ClassVar[Sequence[str]] = ("source_alloy_ids",)


@dataclass(frozen=True)
class Loadout(SerializableModel):
    loadout_id: str
    cell_id: str
    trace_ids: List[str]
    alloy_ids: List[str]
    doctrine_ids: List[str]
    trust_label: str
    generated_at: str
    metadata: Optional[Dict[str, Any]] = None

    _required_fields: ClassVar[Sequence[str]] = (
        "loadout_id",
        "cell_id",
        "trace_ids",
        "alloy_ids",
        "doctrine_ids",
        "trust_label",
        "generated_at",
    )


@dataclass(frozen=True)
class Outcome(SerializableModel):
    outcome_id: str
    cell_id: str
    loadout_id: str
    task_id: str
    verdict: str
    trace_ids: List[str] = field(default_factory=list)
    ignored_charge_ids: List[str] = field(default_factory=list)
    ignored_caution_ids: List[str] = field(default_factory=list)
    contradicted_charge_ids: List[str] = field(default_factory=list)
    over_retrieved_charge_ids: List[str] = field(default_factory=list)
    pack_misses: List[str] = field(default_factory=list)
    pack_miss_details: List[Dict[str, Any]] = field(default_factory=list)
    score: Optional[float] = None
    observed_at: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    _required_fields: ClassVar[Sequence[str]] = (
        "outcome_id",
        "cell_id",
        "loadout_id",
        "task_id",
        "verdict",
    )
    _bounded_fields: ClassVar[Sequence[str]] = ("score",)


# Power-theme public aliases. The current Python API keeps legacy field names for compatibility.
Feed = Source
Spark = Fragment
Charge = Trace
Coil = Alloy
RailProposal = DoctrineProposal
Pack = Loadout
Signal = Outcome
