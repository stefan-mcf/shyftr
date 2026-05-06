"""Reusable contract checks for ShyftR source adapters.

The harness is intentionally dependency-light so third-party adapter authors can
copy it into their own tests. It validates the public adapter contract without
mutating ShyftR cell ledgers or external runtime state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List

from shyftr.integrations.protocols import ExternalSourceRef, SourceAdapter, SourcePayload


@dataclass(frozen=True)
class AdapterHarnessResult:
    """Result from a public adapter contract check."""

    status: str
    refs_checked: int = 0
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status, "refs_checked": self.refs_checked, "errors": list(self.errors)}


class AdapterTestHarness:
    """Run read-only contract checks against a SourceAdapter implementation."""

    def __init__(self, adapter: SourceAdapter) -> None:
        self.adapter = adapter

    def run(self, *, require_sources: bool = False, max_sources: int | None = None) -> AdapterHarnessResult:
        errors: list[str] = []
        refs: list[ExternalSourceRef] = []
        try:
            refs = list(self.adapter.discover_sources())
        except Exception as exc:  # pragma: no cover - adapter-specific
            errors.append(f"discover_sources raised {type(exc).__name__}: {exc}")

        if require_sources and not refs:
            errors.append("discover_sources returned no sources")

        for index, ref in enumerate(refs[:max_sources]):
            if not isinstance(ref, ExternalSourceRef):
                errors.append(f"source {index} is not ExternalSourceRef")
                continue
            round_trip = ExternalSourceRef.from_dict(ref.to_dict())
            if round_trip != ref:
                errors.append(f"source {index} failed ExternalSourceRef round trip")
            try:
                payload = self.adapter.read_source(ref)
                if not isinstance(payload, SourcePayload):
                    errors.append(f"source {index} read_source did not return SourcePayload")
                elif not payload.content_hash:
                    errors.append(f"source {index} payload has empty content_hash")
            except Exception as exc:  # pragma: no cover - adapter-specific
                errors.append(f"source {index} read_source raised {type(exc).__name__}: {exc}")
            try:
                metadata = self.adapter.source_metadata(ref)
                if not isinstance(metadata, dict):
                    errors.append(f"source {index} source_metadata did not return dict")
            except Exception as exc:  # pragma: no cover - adapter-specific
                errors.append(f"source {index} source_metadata raised {type(exc).__name__}: {exc}")

        return AdapterHarnessResult(status="ok" if not errors else "error", refs_checked=len(refs[:max_sources]), errors=errors)


__all__ = ["AdapterHarnessResult", "AdapterTestHarness"]
