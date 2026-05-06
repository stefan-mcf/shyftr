"""Minimal copy-friendly source adapter template for third-party integrations.

This adapter reads Markdown files from a local folder. It is deliberately simple:
adapter authors can copy the class, preserve provenance fields, and replace the
folder scan with their own local export format.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, List

from shyftr.integrations import IntegrationAdapterError
from shyftr.integrations.protocols import ExternalSourceRef, SourcePayload


class MarkdownFolderTemplateAdapter:
    """Reference SourceAdapter implementation for a folder of Markdown files."""

    def __init__(self, source_root: str | Path, *, adapter_id: str = "markdown-template", external_scope: str = "local-export") -> None:
        self.source_root = Path(source_root).expanduser()
        self.adapter_id = adapter_id
        self.external_scope = external_scope
        if not self.source_root.exists() or not self.source_root.is_dir():
            raise IntegrationAdapterError(f"source_root must be an existing directory: {self.source_root}")

    def discover_sources(self) -> List[ExternalSourceRef]:
        refs: list[ExternalSourceRef] = []
        for path in sorted(self.source_root.rglob("*.md")):
            rel = path.relative_to(self.source_root).as_posix()
            refs.append(
                ExternalSourceRef(
                    adapter_id=self.adapter_id,
                    external_system="local-markdown-folder",
                    external_scope=self.external_scope,
                    source_kind="markdown",
                    source_uri=rel,
                    external_ids={"relative_path": rel},
                    metadata={"public_safe_template": True},
                )
            )
        return refs

    def read_source(self, ref: ExternalSourceRef) -> SourcePayload:
        path = self._resolve_ref(ref)
        text = path.read_text(encoding="utf-8")
        return SourcePayload(
            content_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
            kind="markdown",
            metadata={"relative_path": ref.source_uri, "size_bytes": len(text.encode("utf-8"))},
            external_refs=[ref],
        )

    def source_metadata(self, ref: ExternalSourceRef) -> Dict[str, Any]:
        path = self._resolve_ref(ref)
        stat = path.stat()
        return {"relative_path": ref.source_uri, "size_bytes": stat.st_size, "modified_epoch": int(stat.st_mtime), "content_type": "text/markdown"}

    def _resolve_ref(self, ref: ExternalSourceRef) -> Path:
        if not ref.source_uri:
            raise IntegrationAdapterError("source_uri is required")
        path = (self.source_root / ref.source_uri).resolve()
        root = self.source_root.resolve()
        if root not in path.parents and path != root:
            raise IntegrationAdapterError("source_uri escapes source_root")
        if not path.exists() or not path.is_file():
            raise IntegrationAdapterError(f"source not found: {ref.source_uri}")
        return path


__all__ = ["MarkdownFolderTemplateAdapter"]
