"""Runtime-agnostic adapter protocol interfaces for ShyftR integration.

Defines ExternalSourceRef (identity/provenance for external evidence),
SourcePayload (the data unit exchanged between adapters and ShyftR),
SourceAdapter (protocol for discovering and reading external sources),
and OutcomeAdapter (protocol for discovering and mapping outcomes).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import (
    Any,
    ClassVar,
    Dict,
    List,
    Optional,
    Protocol,
    Sequence,
    Type,
    runtime_checkable,
)

from shyftr.models import SerializableModel


# ── Data models ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ExternalSourceRef(SerializableModel):
    """Identity and provenance metadata for an external evidence source.

    Fields:
        adapter_id: Unique identifier for the adapter that produced this ref.
        external_system: Name of the external runtime system (e.g. "hermes",
            "custom-runtime").
        external_scope: Scope or namespace within the external system (e.g.
            "worker", "monitor").
        source_kind: Kind of source material (e.g. "closeout", "log",
            "artifact", "message").
        source_uri: URI or file path locating the original source.
        source_line_offset: Line or byte offset within the source, where
            applicable.
        external_ids: Stable external identity fields (e.g.
            {"external_run_id": "...", "external_task_id": "..."}).
        metadata: Additional provenance or routing metadata.
    """

    adapter_id: str
    external_system: str
    external_scope: str
    source_kind: str
    source_uri: Optional[str] = None
    source_line_offset: Optional[int] = None
    external_ids: Dict[str, str] = field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = None

    _required_fields: ClassVar[Sequence[str]] = (
        "adapter_id",
        "external_system",
        "external_scope",
        "source_kind",
    )


@dataclass(frozen=True)
class SourcePayload(SerializableModel):
    """A unit of evidence sourced from an external adapter.

    Fields:
        content_hash: Deterministic hash of the source text or bytes (e.g.
            SHA-256 hex digest).
        kind: Kind of payload content (e.g. "text", "json", "log").
        metadata: Optional metadata associated with this payload.
        external_refs: External provenance refs linking this payload to
            original source locations.
    """

    content_hash: str
    kind: str
    metadata: Optional[Dict[str, Any]] = None
    external_refs: List[ExternalSourceRef] = field(default_factory=list)

    _required_fields: ClassVar[Sequence[str]] = (
        "content_hash",
        "kind",
    )

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["external_refs"] = [ref.to_dict() for ref in self.external_refs]
        return d

    @classmethod
    def from_dict(cls: Type[SourcePayload], payload: Dict[str, Any]) -> SourcePayload:
        d = dict(payload)
        if "external_refs" in d and isinstance(d["external_refs"], list):
            d["external_refs"] = [
                ExternalSourceRef.from_dict(ref) if isinstance(ref, dict) else ref
                for ref in d["external_refs"]
            ]
        return super().from_dict(d)


# ── Adapter protocols ────────────────────────────────────────────────────────


@runtime_checkable
class SourceAdapter(Protocol):
    """Protocol for adapters that discover and read external source evidence.

    Implementations are runtime-specific but the protocol is not — any
    runtime that provides discoverable source files, messages, or artifacts
    can implement this interface.
    """

    def discover_sources(self) -> List[ExternalSourceRef]:
        """Return all discoverable external source references.

        Returns:
            A list of ExternalSourceRef items describing available sources.
            May be empty if no sources are currently discoverable.
        """
        ...

    def read_source(self, ref: ExternalSourceRef) -> SourcePayload:
        """Read and return the source payload for a given reference.

        Args:
            ref: An ExternalSourceRef previously returned by
                discover_sources() or constructed by the caller.

        Returns:
            A SourcePayload containing the content and metadata for the
            referenced source.

        Raises:
            IntegrationAdapterError: If the source cannot be read (missing
                file, permission error, etc.).
        """
        ...

    def source_metadata(self, ref: ExternalSourceRef) -> Dict[str, Any]:
        """Return metadata about a source without reading its full content.

        Args:
            ref: An ExternalSourceRef identifying the source.

        Returns:
            A dictionary of metadata (size, modified time, content-type,
            etc.). Exact keys are implementation-specific.
        """
        ...


@runtime_checkable
class OutcomeAdapter(Protocol):
    """Protocol for adapters that discover and map external outcome evidence.

    Implementations translate external runtime outcome records into the
    ShyftR SourcePayload format, preserving provenance so ShyftR can
    record and learn from outcome feedback.
    """

    def discover_outcomes(self) -> List[ExternalSourceRef]:
        """Return all discoverable external outcome references.

        Returns:
            A list of ExternalSourceRef items describing available outcome
            sources. May be empty if no outcomes are currently discoverable.
        """
        ...

    def read_outcome(self, ref: ExternalSourceRef) -> SourcePayload:
        """Read and return the outcome payload for a given reference.

        Args:
            ref: An ExternalSourceRef previously returned by
                discover_outcomes() or constructed by the caller.

        Returns:
            A SourcePayload containing the outcome content and metadata.

        Raises:
            IntegrationAdapterError: If the outcome cannot be read.
        """
        ...

    def map_outcome(self, payload: SourcePayload) -> Dict[str, Any]:
        """Convert a generic SourcePayload into a structured outcome
        representation suitable for ShyftR Outcome recording.

        Args:
            payload: A SourcePayload with external reference provenance.

        Returns:
            A dictionary with outcome fields (verdict, score, applied
            trace IDs, etc.). Exact keys are implementation-specific but
            should align with the ShyftR Outcome model.
        """
        ...


__all__ = [
    "ExternalSourceRef",
    "SourcePayload",
    "SourceAdapter",
    "OutcomeAdapter",
]
