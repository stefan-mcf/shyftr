"""Generic file and JSONL Source adapter for ShyftR runtime integration.

Implements the SourceAdapter protocol from :mod:`shyftr.integrations.protocols`
using the RI-2 declarative config model (:class:`RuntimeAdapterConfig`).

Discovers sources by:
  - Single file (``kind: file``)
  - Glob pattern (``kind: glob``)
  - JSONL rows (``kind: jsonl``) — each row is a separate source with
    file-path, line-number, and row-hash identity
  - Directory tree (``kind: directory``)

Supports dry-run discovery summaries and idempotent deduplication by
content hash and external reference.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from shyftr.integrations import IntegrationAdapterError, IntegrationAdapterWarning
from shyftr.integrations.config import (
    InputDefinition,
    RuntimeAdapterConfig,
)
from shyftr.integrations.protocols import (
    ExternalSourceRef,
    SourceAdapter,
    SourcePayload,
)


# ── Exceptions ──────────────────────────────────────────────────────────────


class FileAdapterError(IntegrationAdapterError):
    """Raised when a file adapter operation fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)


# ── Discovery result model ──────────────────────────────────────────────────


@dataclass(frozen=True)
class FileDiscoveryResult:
    """Result of a single file or JSONL row discovery.

    Fields:
        ref: External source reference for the discovered item.
        content_hash: Deterministic SHA-256 hash of the source content.
        size_bytes: Size of the content in bytes.
        kind: The input kind that produced this result (file/glob/jsonl/directory).
        is_jsonl_row: True if this came from a JSONL row, False for file-level.
    """

    ref: ExternalSourceRef
    content_hash: str
    size_bytes: int
    kind: str
    is_jsonl_row: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ref": self.ref.to_dict(),
            "content_hash": self.content_hash,
            "size_bytes": self.size_bytes,
            "kind": self.kind,
            "is_jsonl_row": self.is_jsonl_row,
        }


# ── Dry-run summary ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class DiscoverySummary:
    """Summary of a dry-run discovery operation.

    Fields:
        adapter_id: The adapter that performed discovery.
        total_sources: Total number of discovered sources.
        by_kind: Count of sources broken down by source_kind.
        by_input_kind: Count of sources broken down by input kind (file/glob/jsonl/directory).
        inputs_processed: Number of input definitions processed.
        errors: Any errors encountered during discovery (non-fatal).
    """

    adapter_id: str
    total_sources: int
    by_kind: Dict[str, int] = field(default_factory=dict)
    by_input_kind: Dict[str, int] = field(default_factory=dict)
    inputs_processed: int = 0
    errors: List[str] = field(default_factory=list)


# ── File source adapter ─────────────────────────────────────────────────────


class FileSourceAdapter:
    """Source adapter that discovers ShyftR sources from files and JSONL logs.

    Implements the :class:`SourceAdapter` protocol by reading config-driven
    input definitions, discovering files/rows, and producing
    :class:`ExternalSourceRef` and :class:`SourcePayload` instances.

    Args:
        config: A validated ``RuntimeAdapterConfig`` instance.

    Raises:
        FileAdapterError: If the config's source_root does not exist or
            must be a directory.
    """

    def __init__(self, config: RuntimeAdapterConfig) -> None:
        self._config = config
        self._source_root = Path(config.source_root)
        if not self._source_root.exists():
            raise FileAdapterError(
                f"source_root does not exist: {config.source_root}",
                details={"adapter_id": config.adapter_id},
            )
        if not self._source_root.is_dir():
            raise FileAdapterError(
                f"source_root must be a directory: {config.source_root}",
                details={"adapter_id": config.adapter_id},
            )
        self._deduplicate: bool = config.ingest_options.get("deduplicate", True)
        self._seen_hashes: set = set()
        self._seen_refs: set = set()

    # ── Public API ─────────────────────────────────────────────────────────

    def discover_sources(self) -> List[ExternalSourceRef]:
        """Discover all external source references from configured inputs.

        Returns:
            A list of :class:`ExternalSourceRef` items for every file
            and JSONL row matched by the input definitions.

        Raises:
            FileAdapterError: If an input definition has an unsupported kind.
        """
        results: List[ExternalSourceRef] = []
        for inp in self._config.inputs:
            if inp.kind == "file":
                results.extend(self._discover_file(inp))
            elif inp.kind == "glob":
                results.extend(self._discover_glob(inp))
            elif inp.kind == "jsonl":
                results.extend(self._discover_jsonl(inp))
            elif inp.kind == "directory":
                results.extend(self._discover_directory(inp))
            else:
                raise FileAdapterError(
                    f"Unsupported input kind: {inp.kind}",
                    details={"input_kind": inp.kind, "path": inp.path},
                )
        return results

    def read_source(self, ref: ExternalSourceRef) -> SourcePayload:
        """Read a file or JSONL row and return a SourcePayload.

        Args:
            ref: An :class:`ExternalSourceRef` previously returned by
                :meth:`discover_sources`.

        Returns:
            A :class:`SourcePayload` with the content hash, kind, metadata,
            and external provenance.

        Raises:
            FileAdapterError: If the file cannot be read or the JSONL row
                cannot be loaded.
        """
        uri = ref.source_uri
        if not uri:
            raise FileAdapterError("source_uri is required", details={"ref": ref.to_dict()})

        path = self._resolve(uri)
        line_offset = ref.source_line_offset

        if line_offset is not None and line_offset >= 0:
            # Row-level: read a single JSONL line
            text = self._read_jsonl_line(path, line_offset)
            kind = self._infer_kind_for_row(ref.source_kind)
        else:
            # File-level: read the entire file
            text = self._read_file_text(path)
            kind = ref.source_kind

        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

        return SourcePayload(
            content_hash=content_hash,
            kind=kind,
            metadata={
                "size_bytes": len(text.encode("utf-8")),
                "adapter_id": self._config.adapter_id,
            },
            external_refs=[ref],
        )

    def source_metadata(self, ref: ExternalSourceRef) -> Dict[str, Any]:
        """Return metadata about a source without reading full content.

        Args:
            ref: An :class:`ExternalSourceRef` identifying the source.

        Returns:
            A dictionary with size, modified time (epoch), and content type.
        """
        uri = ref.source_uri
        if not uri:
            return {"error": "source_uri is required", "ref": ref.to_dict()}

        path = self._resolve(uri)
        if not path.exists():
            return {"error": f"File not found: {path}"}

        stat = path.stat()
        return {
            "size_bytes": stat.st_size,
            "modified_epoch": int(stat.st_mtime),
            "content_type": self._guess_content_type(path),
            "is_jsonl_row": ref.source_line_offset is not None,
        }

    # ── Dry-run support ────────────────────────────────────────────────────

    def dry_run_discovery(self) -> DiscoverySummary:
        """Run discovery without reading content, returning a summary.

        Resets internal dedup state so each call produces a fresh summary.

        Returns:
            A :class:`DiscoverySummary` with counts and details.
        """
        self._reset_dedup()
        by_kind: Dict[str, int] = {}
        by_input_kind: Dict[str, int] = {}
        errors: List[str] = []
        total = 0

        for inp in self._config.inputs:
            try:
                count = 0
                if inp.kind == "file":
                    count = len(self._discover_file(inp, dry_run=True))
                elif inp.kind == "glob":
                    count = len(self._discover_glob(inp, dry_run=True))
                elif inp.kind == "jsonl":
                    count = len(self._discover_jsonl(inp, dry_run=True))
                elif inp.kind == "directory":
                    count = len(self._discover_directory(inp, dry_run=True))
                else:
                    errors.append(f"Unsupported kind '{inp.kind}' for path '{inp.path}'")
                    continue

                by_input_kind[inp.kind] = by_input_kind.get(inp.kind, 0) + count
                by_kind[inp.source_kind] = by_kind.get(inp.source_kind, 0) + count
                total += count
            except FileAdapterError as e:
                errors.append(str(e))

        return DiscoverySummary(
            adapter_id=self._config.adapter_id,
            total_sources=total,
            by_kind=by_kind,
            by_input_kind=by_input_kind,
            inputs_processed=len(self._config.inputs),
            errors=errors,
        )

    # ── Input kind handlers ─────────────────────────────────────────────────

    def _discover_file(
        self,
        inp: InputDefinition,
        dry_run: bool = False,
    ) -> List[ExternalSourceRef]:
        """Discover a single file as a source."""
        path = self._resolve(inp.path)
        if not path.exists():
            return []
        if not path.is_file():
            return []

        return self._make_file_refs(path, inp, dry_run=dry_run)

    def _discover_glob(
        self,
        inp: InputDefinition,
        dry_run: bool = False,
    ) -> List[ExternalSourceRef]:
        """Discover sources matching a glob pattern."""
        pattern_path = self._resolve(inp.path)
        # Determine the parent directory for globbing
        parent = pattern_path.parent if pattern_path.is_absolute() else self._source_root
        resolved_parent = parent.resolve()
        glob_pattern = pattern_path.name if pattern_path.is_absolute() else inp.path

        results: List[ExternalSourceRef] = []
        if resolved_parent.is_dir():
            for matched_path in sorted(resolved_parent.glob(glob_pattern)):
                if matched_path.is_file():
                    results.extend(
                        self._make_file_refs(matched_path, inp, dry_run=dry_run)
                    )
        return results

    def _discover_jsonl(
        self,
        inp: InputDefinition,
        dry_run: bool = False,
    ) -> List[ExternalSourceRef]:
        """Discover each row in a JSONL file as a separate source."""
        path = self._resolve(inp.path)
        if not path.exists() or not path.is_file():
            return []

        if path.stat().st_size == 0:
            return []

        results: List[ExternalSourceRef] = []
        try:
            with path.open("r", encoding="utf-8") as f:
                for line_number, line in enumerate(f, start=1):
                    stripped = line.strip()
                    if not stripped:
                        continue

                    # Compute row hash for dedup
                    row_hash = hashlib.sha256(stripped.encode("utf-8")).hexdigest()

                    dedup_key = f"{str(path)}:{line_number}:{row_hash}"
                    if self._is_duplicate(dedup_key, row_hash, inp, dry_run=dry_run):
                        continue

                    results.append(
                        ExternalSourceRef(
                            adapter_id=self._config.adapter_id,
                            external_system=self._config.external_system,
                            external_scope=self._config.external_scope,
                            source_kind=inp.source_kind,
                            source_uri=str(path),
                            source_line_offset=line_number,
                            external_ids=self._build_external_ids(inp, stripped),
                            metadata={
                                "row_hash": row_hash,
                                "input_path": inp.path,
                                "input_kind": "jsonl",
                            },
                        )
                    )
        except (OSError, json.JSONDecodeError) as e:
            raise FileAdapterError(
                f"Failed to read JSONL file: {path}",
                details={"path": str(path), "error": str(e)},
            )

        return results

    def _discover_directory(
        self,
        inp: InputDefinition,
        dry_run: bool = False,
    ) -> List[ExternalSourceRef]:
        """Discover all files in a directory tree as sources."""
        path = self._resolve(inp.path)
        if not path.exists() or not path.is_dir():
            return []

        recursive = self._config.ingest_options.get("recursive", True)
        include_hidden = self._config.ingest_options.get("include_hidden", False)
        max_sources: Optional[int] = self._config.ingest_options.get("max_sources")

        results: List[ExternalSourceRef] = []
        walk_fn = os_walk if recursive else os_scandir_top

        for file_path in walk_fn(path, include_hidden=include_hidden):
            if max_sources is not None and len(results) >= max_sources:
                break
            results.extend(self._make_file_refs(file_path, inp, dry_run=dry_run))

        return results

    # ── Internal helpers ────────────────────────────────────────────────────


    def resolve_source_path(self, path_str: str) -> Path:
        """Resolve an adapter input path relative to source_root.

        This public wrapper supports incremental-sync code without reaching into
        private adapter internals.
        """
        return self._resolve(path_str)

    def external_ids_for_input(self, inp: InputDefinition, source_text: str) -> Dict[str, str]:
        """Build stable external IDs for an input/source payload.

        This public wrapper keeps incremental sync provenance identical to normal
        JSONL discovery.
        """
        return self._build_external_ids(inp, source_text)

    def _resolve(self, path_str: str) -> Path:
        """Resolve a path string relative to source_root if relative."""
        p = Path(path_str)
        if p.is_absolute():
            return p
        return (self._source_root / p).resolve()

    def _make_file_refs(
        self,
        path: Path,
        inp: InputDefinition,
        dry_run: bool = False,
    ) -> List[ExternalSourceRef]:
        """Create ExternalSourceRef entries for a single file."""
        if not path.is_file():
            return []
        if path.stat().st_size == 0 and not self._config.ingest_options.get("include_empty", False):
            return []

        # Only compute hash for dedup check (skip for dry_run where dedup may not apply)
        content_hash = self._file_sha256(path) if not dry_run else ""
        dedup_key = str(path)
        if self._is_duplicate(dedup_key, content_hash, inp, dry_run=dry_run):
            return []

        return [
            ExternalSourceRef(
                adapter_id=self._config.adapter_id,
                external_system=self._config.external_system,
                external_scope=self._config.external_scope,
                source_kind=inp.source_kind,
                source_uri=str(path),
                source_line_offset=None,
                external_ids=self._build_external_ids(inp, str(path)),
                metadata={
                    "size_bytes": path.stat().st_size,
                    "input_path": inp.path,
                    "input_kind": inp.kind,
                },
            )
        ]

    def _is_duplicate(
        self,
        dedup_key: str,
        content_hash: str,
        inp: InputDefinition,
        dry_run: bool = False,
    ) -> bool:
        """Check if a source is a duplicate by ref or content hash.

        During dry_run, only check ref dedup (no content hash computed).
        """
        if not self._deduplicate or dry_run:
            return False

        if dedup_key in self._seen_refs:
            return True
        if content_hash and content_hash in self._seen_hashes:
            return True

        self._seen_refs.add(dedup_key)
        if content_hash:
            self._seen_hashes.add(content_hash)
        return False

    def _reset_dedup(self) -> None:
        """Clear deduplication tracking state."""
        self._seen_hashes.clear()
        self._seen_refs.clear()

    def _build_external_ids(
        self,
        inp: InputDefinition,
        source_text: str,
    ) -> Dict[str, str]:
        """Build external ID dict from identity mapping rules.

        Currently extracts simple field values from the source context.
        Future: support configurable metadata key extraction.
        """
        mapping = {**self._config.identity_mapping, **inp.identity_mapping}
        ids: Dict[str, str] = {}

        # For JSONL rows, try to extract external IDs from the row JSON
        if inp.kind == "jsonl" and source_text:
            try:
                row = json.loads(source_text)
                for ext_field, source_key in mapping.items():
                    val = row.get(source_key)
                    if val is not None:
                        ids[ext_field] = str(val)
            except (json.JSONDecodeError, TypeError):
                pass

        return ids

    def _read_file_text(self, path: Path) -> str:
        """Read a file's full text content."""
        try:
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            raise FileAdapterError(
                f"Failed to read file: {path}",
                details={"path": str(path), "error": str(e)},
            )

    def _read_jsonl_line(self, path: Path, line_number: int) -> str:
        """Read a specific line from a JSONL file."""
        try:
            with path.open("r", encoding="utf-8") as f:
                for current_line, line in enumerate(f, start=1):
                    if current_line == line_number:
                        return line.strip()
            raise FileAdapterError(
                f"Line {line_number} not found in JSONL file: {path}",
                details={"path": str(path), "line_number": line_number},
            )
        except OSError as e:
            raise FileAdapterError(
                f"Failed to read JSONL line: {path}:{line_number}",
                details={"path": str(path), "line_number": line_number, "error": str(e)},
            )

    def _file_sha256(self, path: Path) -> str:
        """Compute SHA-256 hash of file contents."""
        digest = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _infer_kind_for_row(self, source_kind: str) -> str:
        """Infer the payload kind for a JSONL row."""
        if source_kind == "outcome":
            return "json"
        return "text"

    def _guess_content_type(self, path: Path) -> str:
        """Guess content type from file extension."""
        suffix = path.suffix.lower()
        content_types = {
            ".md": "text/markdown",
            ".log": "text/plain",
            ".txt": "text/plain",
            ".jsonl": "application/jsonl",
            ".json": "application/json",
            ".yaml": "text/yaml",
            ".yml": "text/yaml",
            ".csv": "text/csv",
        }
        return content_types.get(suffix, "application/octet-stream")


# ── Utility functions ───────────────────────────────────────────────────────


def os_walk(
    directory: Path,
    include_hidden: bool = False,
) -> List[Path]:
    """Walk a directory tree, returning file paths in sorted order."""
    results: List[Path] = []
    for root, dirs, files in os_walk_iter(directory):
        if not include_hidden:
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            files = [f for f in files if not f.startswith(".")]
        for name in sorted(files):
            results.append(Path(root) / name)
    return results


def os_walk_iter(directory: Path):
    """Yield (root, dirs, files) tuples like os.walk."""
    from os import walk as os_walk_fn
    return os_walk_fn(str(directory))


def os_scandir_top(
    directory: Path,
    include_hidden: bool = False,
) -> List[Path]:
    """Scan only the top-level directory, returning file paths."""
    results: List[Path] = []
    for entry in sorted(directory.iterdir()):
        if entry.is_file():
            if not include_hidden and entry.name.startswith("."):
                continue
            results.append(entry)
    return results


# ── Convenience function ────────────────────────────────────────────────────


def create_file_adapter(config: RuntimeAdapterConfig) -> FileSourceAdapter:
    """Create a FileSourceAdapter from a validated config.

    This is the recommended entry point for adapter creation.
    """
    return FileSourceAdapter(config)


# ── Module exports ──────────────────────────────────────────────────────────

__all__ = [
    "DiscoverySummary",
    "FileAdapterError",
    "FileDiscoveryResult",
    "FileSourceAdapter",
    "create_file_adapter",
]
