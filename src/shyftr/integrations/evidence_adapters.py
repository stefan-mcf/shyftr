"""Generic evidence adapters for local-first ShyftR integrations.

These adapters implement the existing SourceAdapter protocol. They do not create
a second integration protocol; they turn inline or artifact-backed evidence into
materialized local source snapshots with stable provenance so the normal ShyftR
ledger, regulator, extraction, review, pack, and feedback path can process it.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from shyftr.integrations import IntegrationAdapterError
from shyftr.integrations.protocols import ExternalSourceRef, SourceAdapter, SourcePayload

_GENERIC_ADAPTER_VERSION = "1.0.0"
_DEFAULT_EXTERNAL_SYSTEM = "generic-evidence"
_SAFE_SLUG_RE = re.compile(r"[^a-zA-Z0-9_.-]+")


@dataclass(frozen=True)
class EvidenceDocument:
    """Inline or artifact-backed evidence for a generic SourceAdapter.

    If ``source_uri`` is omitted, the adapter materializes ``text`` into a
    deterministic snapshot under its ``source_root`` before exposing it as a
    source reference. This keeps downstream extraction file-based and
    reproducible without requiring callers to create temporary files.
    """

    text: str
    source_kind: str
    title: str = "evidence"
    source_uri: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    external_ids: Dict[str, str] = field(default_factory=dict)
    extension: str = ".txt"

    def __post_init__(self) -> None:
        if not self.text:
            raise ValueError("EvidenceDocument.text is required")
        if not self.source_kind:
            raise ValueError("EvidenceDocument.source_kind is required")
        if self.extension and not self.extension.startswith("."):
            object.__setattr__(self, "extension", f".{self.extension}")


class GenericEvidenceAdapter:
    """SourceAdapter for generic local evidence documents.

    Supported source kinds are intentionally broad and runtime-neutral:
    ``markdown_note``, ``raw_text``, ``chat_summary``, ``task_closeout``,
    ``issue_comment``, and ``tool_log``. Callers may pass other source kinds
    for public-safe experiments; ShyftR records the source kind and lets the
    regulator/review path decide whether candidate memory should be promoted.
    """

    adapter_id = "generic-evidence"
    version = _GENERIC_ADAPTER_VERSION

    def __init__(
        self,
        source_root: str | Path,
        documents: Sequence[EvidenceDocument],
        *,
        adapter_id: str = "generic-evidence",
        external_system: str = _DEFAULT_EXTERNAL_SYSTEM,
        external_scope: str = "default",
    ) -> None:
        if not documents:
            raise ValueError("at least one EvidenceDocument is required")
        self.source_root = Path(source_root).expanduser()
        self.source_root.mkdir(parents=True, exist_ok=True)
        self.adapter_id = adapter_id
        self.external_system = external_system
        self.external_scope = external_scope
        self._documents = list(documents)
        self._refs: list[ExternalSourceRef] | None = None

    @classmethod
    def from_markdown_note(
        cls,
        source_root: str | Path,
        markdown: str,
        *,
        title: str = "markdown-note",
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> "GenericEvidenceAdapter":
        return cls(
            source_root,
            [
                EvidenceDocument(
                    text=markdown,
                    title=title,
                    source_kind="markdown_note",
                    metadata=metadata or {},
                    extension=".md",
                )
            ],
            **kwargs,
        )

    @classmethod
    def from_raw_text(
        cls,
        source_root: str | Path,
        text: str,
        *,
        title: str = "raw-text",
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> "GenericEvidenceAdapter":
        return cls(
            source_root,
            [
                EvidenceDocument(
                    text=text,
                    title=title,
                    source_kind="raw_text",
                    metadata=metadata or {},
                    extension=".txt",
                )
            ],
            **kwargs,
        )

    @classmethod
    def from_chat_summary_json(
        cls,
        source_root: str | Path,
        payload: Dict[str, Any],
        *,
        title: str = "chat-summary",
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> "GenericEvidenceAdapter":
        return cls(
            source_root,
            [
                EvidenceDocument(
                    text=json.dumps(payload, sort_keys=True, indent=2) + "\n",
                    title=title,
                    source_kind="chat_summary",
                    metadata={"content_type": "application/json", **(metadata or {})},
                    external_ids={k: str(v) for k, v in payload.items() if k.endswith("_id") and v is not None},
                    extension=".json",
                )
            ],
            **kwargs,
        )

    @classmethod
    def from_task_closeout_markdown(
        cls,
        source_root: str | Path,
        markdown: str,
        *,
        title: str = "task-closeout",
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> "GenericEvidenceAdapter":
        return cls(
            source_root,
            [
                EvidenceDocument(
                    text=markdown,
                    title=title,
                    source_kind="task_closeout",
                    metadata=metadata or {},
                    extension=".md",
                )
            ],
            **kwargs,
        )

    @classmethod
    def from_issue_comment(
        cls,
        source_root: str | Path,
        text: str,
        *,
        title: str = "issue-comment",
        metadata: Optional[Dict[str, Any]] = None,
        external_ids: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> "GenericEvidenceAdapter":
        return cls(
            source_root,
            [
                EvidenceDocument(
                    text=text,
                    title=title,
                    source_kind="issue_comment",
                    metadata=metadata or {},
                    external_ids=external_ids or {},
                    extension=".md",
                )
            ],
            **kwargs,
        )

    @classmethod
    def from_tool_log(
        cls,
        source_root: str | Path,
        text: str,
        *,
        title: str = "tool-log",
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> "GenericEvidenceAdapter":
        return cls(
            source_root,
            [
                EvidenceDocument(
                    text=text,
                    title=title,
                    source_kind="tool_log",
                    metadata=metadata or {},
                    extension=".log",
                )
            ],
            **kwargs,
        )

    def discover_sources(self) -> List[ExternalSourceRef]:
        if self._refs is not None:
            return list(self._refs)
        refs: list[ExternalSourceRef] = []
        for index, document in enumerate(self._documents, start=1):
            path = self._materialize_document(document, index)
            refs.append(
                ExternalSourceRef(
                    adapter_id=self.adapter_id,
                    external_system=self.external_system,
                    external_scope=self.external_scope,
                    source_kind=document.source_kind,
                    source_uri=str(path),
                    external_ids=dict(document.external_ids),
                    metadata={
                        "adapter_version": self.version,
                        "title": document.title,
                        "document_index": index,
                        "materialized": document.source_uri is None,
                        **dict(document.metadata),
                    },
                )
            )
        self._refs = refs
        return list(refs)

    def read_source(self, ref: ExternalSourceRef) -> SourcePayload:
        if not ref.source_uri:
            raise IntegrationAdapterError("source_uri is required", details={"ref": ref.to_dict()})
        path = Path(ref.source_uri)
        if not path.exists():
            raise IntegrationAdapterError("source file does not exist", details={"source_uri": ref.source_uri})
        text = path.read_text(encoding="utf-8")
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        metadata = {
            "adapter_id": self.adapter_id,
            "adapter_version": self.version,
            "size_bytes": len(text.encode("utf-8")),
            "content_type": _guess_content_type(path),
            **(ref.metadata or {}),
        }
        return SourcePayload(
            content_hash=digest,
            kind=ref.source_kind,
            metadata=metadata,
            external_refs=[ref],
        )

    def source_metadata(self, ref: ExternalSourceRef) -> Dict[str, Any]:
        if not ref.source_uri:
            return {"error": "source_uri is required", "ref": ref.to_dict()}
        path = Path(ref.source_uri)
        if not path.exists():
            return {"error": f"source file does not exist: {ref.source_uri}"}
        stat = path.stat()
        return {
            "adapter_id": self.adapter_id,
            "source_kind": ref.source_kind,
            "size_bytes": stat.st_size,
            "modified_epoch": int(stat.st_mtime),
            "content_type": _guess_content_type(path),
            "external_refs": [ref.to_dict()],
        }

    def _materialize_document(self, document: EvidenceDocument, index: int) -> Path:
        if document.source_uri:
            path = Path(document.source_uri).expanduser()
            if not path.exists():
                raise IntegrationAdapterError("source_uri does not exist", details={"source_uri": document.source_uri})
            return path
        digest = hashlib.sha256(document.text.encode("utf-8")).hexdigest()
        slug = _slug(document.title or document.source_kind)
        path = self.source_root / f"{index:03d}-{slug}-{digest[:12]}{document.extension or '.txt'}"
        if not path.exists() or path.read_text(encoding="utf-8") != document.text:
            path.write_text(document.text, encoding="utf-8")
        return path


def evidence_adapter_metadata() -> Dict[str, Any]:
    """Return plugin metadata for the built-in generic evidence adapter."""

    return {
        "name": "generic-evidence",
        "version": _GENERIC_ADAPTER_VERSION,
        "description": "Built-in generic evidence SourceAdapter for notes, closeouts, issue comments, chat summaries, raw text, and tool logs.",
        "supported_input_kinds": [
            "markdown_note",
            "raw_text",
            "chat_summary",
            "task_closeout",
            "issue_comment",
            "tool_log",
        ],
        "capabilities": ["discover", "read", "metadata", "materialize", "idempotent"],
        "adapter_sdk_version": "1.0.0",
        "config_schema_version": "1.0.0",
        "entry_point_group": "builtin",
        "adapter_class": "shyftr.integrations.evidence_adapters.GenericEvidenceAdapter",
        "builtin": True,
    }


def _slug(value: str) -> str:
    slug = _SAFE_SLUG_RE.sub("-", value.strip()).strip("-._").lower()
    return slug or "evidence"


def _guess_content_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".md", ".markdown"}:
        return "text/markdown"
    if suffix == ".json":
        return "application/json"
    if suffix in {".log", ".txt"}:
        return "text/plain"
    return "application/octet-stream"


__all__ = [
    "EvidenceDocument",
    "GenericEvidenceAdapter",
    "evidence_adapter_metadata",
]
