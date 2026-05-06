"""In-memory cosine vector index for ShyftR retrieval.

Defines the ``VectorIndex`` protocol and ships an in-memory implementation
that stores vectors with provenance metadata and supports cosine-similarity
nearest-neighbour queries.  A sqlite-vec adapter placeholder is included
but does not require sqlite-vec to be installed for tests.
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Sequence, Tuple, Union, runtime_checkable

from ..ledger import read_jsonl

PathLike = Union[str, Path]


# ---------------------------------------------------------------------------
# Result model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VectorResult:
    """A single vector retrieval result with provenance and score."""

    trace_id: str
    cell_id: str
    statement: str
    rationale: Optional[str]
    tags: List[str]
    kind: Optional[str]
    status: str
    confidence: Optional[float]
    cosine_score: float


# ---------------------------------------------------------------------------
# VectorIndex protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class VectorIndex(Protocol):
    """Protocol that every vector index backend must satisfy."""

    def rebuild(
        self,
        cell_path: PathLike,
        provider: Any,
        *,
        include_statuses: Optional[Sequence[str]] = None,
    ) -> int:
        """Rebuild this acceleration index from canonical Cell ledgers."""
        ...

    def add(
        self,
        doc_id: str,
        vector: Sequence[float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a vector with associated metadata."""
        ...

    def query(
        self,
        vector: Sequence[float],
        *,
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Return (doc_id, score, metadata) tuples sorted by score descending."""
        ...

    def status(self, cell_path: Optional[PathLike] = None, provider: Any = None) -> Dict[str, Any]:
        """Return index status and staleness against Cell ledgers/embedding metadata."""
        ...

    def export_metadata(self) -> Dict[str, Any]:
        """Return serialisable index metadata."""
        ...

    def size(self) -> int:
        """Return the number of stored vectors."""
        ...

    def clear(self) -> None:
        """Remove all stored vectors."""
        ...


# ---------------------------------------------------------------------------
# In-memory cosine index
# ---------------------------------------------------------------------------

@dataclass
class _Entry:
    doc_id: str
    vector: List[float]
    metadata: Dict[str, Any]


class InMemoryVectorIndex:
    """In-memory vector index with Grid metadata and cosine similarity search.

    Suitable for tests and local MVP use. The vectors live in memory; metadata can
    be exported to disk so the Grid remains a rebuildable acceleration layer over
    canonical Cell ledgers rather than a source of truth.
    """

    def __init__(
        self,
        *,
        index_id: str = "grid-default",
        backend: str = "in-memory",
        embedding_model: str = "unknown",
        embedding_version: str = "unknown",
    ) -> None:
        self.index_id = index_id
        self.backend = backend
        self.embedding_model = embedding_model
        self.embedding_version = embedding_version
        self._entries: List[_Entry] = []
        self._metadata: Dict[str, Any] = _empty_grid_metadata(
            index_id=index_id,
            backend=backend,
            embedding_model=embedding_model,
            embedding_dimension=None,
            embedding_version=embedding_version,
        )

    def rebuild(
        self,
        cell_path: PathLike,
        provider: Any,
        *,
        include_statuses: Optional[Sequence[str]] = None,
    ) -> int:
        self.clear()
        count = rebuild_vector_index(
            self,
            cell_path,
            provider,
            include_statuses=include_statuses,
        )
        cell = Path(cell_path)
        provider_model = _provider_model(provider, self.embedding_model)
        provider_version = _provider_version(provider, self.embedding_version)
        self.embedding_model = provider_model
        self.embedding_version = provider_version
        self._metadata = _build_grid_metadata(
            cell,
            index_id=self.index_id,
            backend=self.backend,
            embedding_model=provider_model,
            embedding_dimension=_provider_dimension(provider),
            embedding_version=provider_version,
            charge_count=count,
        )
        return count

    def add(
        self,
        doc_id: str,
        vector: Sequence[float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._entries.append(
            _Entry(
                doc_id=doc_id,
                vector=list(vector),
                metadata=metadata or {},
            )
        )

    def query(
        self,
        vector: Sequence[float],
        *,
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        results: List[Tuple[str, float, Dict[str, Any]]] = []
        for entry in self._entries:
            if filter_metadata:
                if not all(
                    entry.metadata.get(k) == v
                    for k, v in filter_metadata.items()
                ):
                    continue
            score = _cosine_similarity(vector, entry.vector)
            results.append((entry.doc_id, score, entry.metadata))
        results.sort(key=lambda r: r[1], reverse=True)
        return results[:top_k]

    def status(self, cell_path: Optional[PathLike] = None, provider: Any = None) -> Dict[str, Any]:
        metadata = self.export_metadata()
        stale_reasons: List[str] = []
        if cell_path is not None and metadata.get("cell_id"):
            current = _current_grid_fingerprint(Path(cell_path))
            if current["ledger_offsets"] != metadata.get("ledger_offsets", {}):
                stale_reasons.append("ledger_offsets")
            if current["ledger_hashes"] != metadata.get("ledger_hashes", {}):
                stale_reasons.append("ledger_hashes")
            if current["charge_count"] != metadata.get("charge_count"):
                stale_reasons.append("charge_count")
        if provider is not None:
            current_dimension = _provider_dimension(provider)
            if current_dimension != metadata.get("embedding_dimension"):
                stale_reasons.append("embedding_dimension")
            current_model = _provider_model(provider, self.embedding_model)
            if current_model != metadata.get("embedding_model"):
                stale_reasons.append("embedding_model")
            current_version = _provider_version(provider, self.embedding_version)
            if current_version != metadata.get("embedding_version"):
                stale_reasons.append("embedding_version")
        return {
            "index_id": metadata.get("index_id"),
            "backend": metadata.get("backend"),
            "size": self.size(),
            "stale": bool(stale_reasons),
            "stale_reasons": sorted(set(stale_reasons)),
            "metadata": metadata,
            "canonical_truth": "cell_ledgers",
        }

    def export_metadata(self) -> Dict[str, Any]:
        return json.loads(json.dumps(self._metadata, sort_keys=True))

    def size(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        self._entries.clear()


# ---------------------------------------------------------------------------
# Cell-level rebuild and query helpers
# ---------------------------------------------------------------------------

def rebuild_vector_index(
    index: VectorIndex,
    cell_path: PathLike,
    provider: Any,
    *,
    include_statuses: Optional[Sequence[str]] = None,
) -> int:
    """Rebuild a VectorIndex from a Cell's ``traces/approved.jsonl``.

    Parameters
    ----------
    index : VectorIndex
        The index to populate.
    cell_path : PathLike
        Path to the Cell directory.
    provider : EmbeddingProvider
        Provider used to embed trace text.
    include_statuses : sequence of str, optional
        If provided, include Traces with these statuses.  By default
        only ``approved`` Traces are indexed.

    Returns
    -------
    int
        Number of Traces indexed.
    """
    cell = Path(cell_path)
    ledger = cell / "traces" / "approved.jsonl"
    if not ledger.exists():
        return 0

    # Read cell_id from manifest
    manifest_path = cell / "config" / "cell_manifest.json"
    if not manifest_path.exists():
        raise ValueError(f"Cell manifest does not exist: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    cell_id = manifest.get("cell_id", "")

    count = 0
    for _, record in read_jsonl(ledger):
        status = record.get("status", "approved")
        if include_statuses is not None:
            if status not in include_statuses:
                continue
        else:
            if status != "approved":
                continue

        # Build text to embed: statement + rationale + tags
        parts = [record.get("statement", "")]
        if record.get("rationale"):
            parts.append(record["rationale"])
        tags = record.get("tags", [])
        if tags:
            parts.append(" ".join(tags))
        text = " ".join(parts)

        vector = provider.embed(text)
        metadata = {
            "trace_id": record.get("trace_id", ""),
            "cell_id": record.get("cell_id", cell_id),
            "statement": record.get("statement", ""),
            "rationale": record.get("rationale") or "",
            "tags": tags,
            "kind": record.get("kind") or "",
            "status": status,
            "confidence": record.get("confidence"),
        }
        index.add(
            doc_id=record.get("trace_id", ""),
            vector=vector,
            metadata=metadata,
        )
        count += 1

    return count


def query_vector(
    index: VectorIndex,
    query_text: str,
    provider: Any,
    *,
    cell_id: Optional[str] = None,
    top_k: int = 10,
) -> List[VectorResult]:
    """Query a VectorIndex with natural-language text.

    Parameters
    ----------
    index : VectorIndex
        The index to search.
    query_text : str
        Natural-language query.
    provider : EmbeddingProvider
        Provider used to embed the query.
    cell_id : str, optional
        Restrict results to a specific Cell.
    top_k : int
        Maximum results to return.

    Returns
    -------
    list of VectorResult
        Results ordered by cosine score descending.
    """
    if not query_text or not query_text.strip():
        return []

    query_vector = provider.embed(query_text)
    filter_meta: Optional[Dict[str, Any]] = None
    if cell_id:
        filter_meta = {"cell_id": cell_id}

    raw = index.query(query_vector, top_k=top_k, filter_metadata=filter_meta)

    results: List[VectorResult] = []
    for doc_id, score, meta in raw:
        results.append(
            VectorResult(
                trace_id=meta.get("trace_id", doc_id),
                cell_id=meta.get("cell_id", ""),
                statement=meta.get("statement", ""),
                rationale=meta.get("rationale") or None,
                tags=meta.get("tags", []),
                kind=meta.get("kind") or None,
                status=meta.get("status", "approved"),
                confidence=meta.get("confidence"),
                cosine_score=score,
            )
        )
    return results


# ---------------------------------------------------------------------------
# Disk-backed Grid metadata helpers
# ---------------------------------------------------------------------------

GRID_METADATA_PATH = Path("indexes") / "grid_metadata.json"
LEDGER_PATHS = (
    Path("traces") / "approved.jsonl",
    Path("charges") / "approved.jsonl",
)


def grid_metadata_path(cell_path: PathLike) -> Path:
    return Path(cell_path) / GRID_METADATA_PATH


def rebuild_grid_metadata(
    cell_path: PathLike,
    provider: Any = None,
    *,
    index_id: str = "grid-default",
    backend: str = "in-memory",
    embedding_model: str = "deterministic-test",
    embedding_version: str = "v1",
) -> Dict[str, Any]:
    """Rebuild Grid acceleration metadata from canonical Cell ledgers."""
    if provider is None:
        from shyftr.retrieval.embeddings import DeterministicEmbeddingProvider
        provider = DeterministicEmbeddingProvider()
    if backend == "in-memory":
        index: VectorIndex = InMemoryVectorIndex(
            index_id=index_id,
            backend=backend,
            embedding_model=embedding_model,
            embedding_version=embedding_version,
        )
    elif backend == "lancedb":
        from shyftr.retrieval.lancedb_adapter import LanceDBVectorIndex
        index = LanceDBVectorIndex(
            Path(cell_path) / "grid" / "lancedb",
            index_id=index_id if index_id != "grid-default" else "grid-lancedb",
            embedding_model=embedding_model,
            embedding_version=embedding_version,
        )
    else:
        raise ValueError(f"Unsupported Grid backend: {backend}")
    index.rebuild(cell_path, provider)
    metadata = index.export_metadata()
    path = grid_metadata_path(cell_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metadata, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return metadata


def load_grid_metadata(cell_path: PathLike) -> Optional[Dict[str, Any]]:
    path = grid_metadata_path(cell_path)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def grid_status(
    cell_path: PathLike,
    provider: Any = None,
    *,
    embedding_model: str = "deterministic-test",
    embedding_version: str = "v1",
) -> Dict[str, Any]:
    if provider is None:
        from shyftr.retrieval.embeddings import DeterministicEmbeddingProvider
        provider = DeterministicEmbeddingProvider()
    stored = load_grid_metadata(cell_path)
    if stored is None:
        return {
            "present": False,
            "stale": True,
            "stale_reasons": ["missing_metadata"],
            "metadata_path": str(grid_metadata_path(cell_path)),
            "metadata": None,
            "canonical_truth": "cell_ledgers",
        }
    current = _build_grid_metadata(
        Path(cell_path),
        index_id=str(stored.get("index_id") or "grid-default"),
        backend=str(stored.get("backend") or "in-memory"),
        embedding_model=_provider_model(provider, embedding_model),
        embedding_dimension=_provider_dimension(provider),
        embedding_version=_provider_version(provider, embedding_version),
        charge_count=_current_grid_fingerprint(Path(cell_path))["charge_count"],
        created_at=str(stored.get("created_at") or ""),
    )
    stale_reasons: List[str] = []
    for key in ("embedding_model", "embedding_dimension", "embedding_version", "ledger_offsets", "ledger_hashes", "charge_count"):
        if stored.get(key) != current.get(key):
            stale_reasons.append(key)
    return {
        "present": True,
        "stale": bool(stale_reasons),
        "stale_reasons": stale_reasons,
        "metadata_path": str(grid_metadata_path(cell_path)),
        "metadata": stored,
        "current": current,
        "canonical_truth": "cell_ledgers",
    }


# ---------------------------------------------------------------------------
# sqlite-vec adapter placeholder
# ---------------------------------------------------------------------------

class SqliteVecVectorIndex:
    """Placeholder adapter for sqlite-vec backed vector index.

    This class satisfies the VectorIndex protocol but raises
    ``RuntimeError`` on any operation unless sqlite-vec is installed
    and a valid connection is provided.  It exists so downstream code
    can reference the adapter without requiring sqlite-vec at import time.
    """

    def __init__(self, db_path: Optional[PathLike] = None) -> None:
        self._db_path = db_path
        self._available = False
        self._metadata = _empty_grid_metadata(
            index_id="grid-sqlite-vec",
            backend="sqlite-vec",
            embedding_model="unknown",
            embedding_dimension=None,
            embedding_version="unknown",
        )
        try:
            import sqlite_vec  # noqa: F401
            self._available = True
        except ImportError:
            self._available = False

    def rebuild(
        self,
        cell_path: PathLike,
        provider: Any,
        *,
        include_statuses: Optional[Sequence[str]] = None,
    ) -> int:
        if not self._available:
            raise RuntimeError(
                "sqlite-vec is not installed; use InMemoryVectorIndex for tests"
            )
        return 0

    def add(
        self,
        doc_id: str,
        vector: Sequence[float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not self._available:
            raise RuntimeError(
                "sqlite-vec is not installed; use InMemoryVectorIndex for tests"
            )

    def query(
        self,
        vector: Sequence[float],
        *,
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        if not self._available:
            raise RuntimeError(
                "sqlite-vec is not installed; use InMemoryVectorIndex for tests"
            )
        return []

    def status(self, cell_path: Optional[PathLike] = None, provider: Any = None) -> Dict[str, Any]:
        return {
            "index_id": self._metadata.get("index_id"),
            "backend": self._metadata.get("backend"),
            "size": self.size(),
            "stale": True,
            "stale_reasons": ["unavailable"] if not self._available else [],
            "metadata": self.export_metadata(),
            "canonical_truth": "cell_ledgers",
        }

    def export_metadata(self) -> Dict[str, Any]:
        return json.loads(json.dumps(self._metadata, sort_keys=True))

    def size(self) -> int:
        return 0

    def clear(self) -> None:
        pass


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _empty_grid_metadata(
    *,
    index_id: str,
    backend: str,
    embedding_model: str,
    embedding_dimension: Optional[int],
    embedding_version: str,
) -> Dict[str, Any]:
    return {
        "index_id": index_id,
        "cell_id": "",
        "backend": backend,
        "embedding_model": embedding_model,
        "embedding_dimension": embedding_dimension,
        "embedding_version": embedding_version,
        "ledger_offsets": {},
        "ledger_hashes": {},
        "charge_count": 0,
        "created_at": "",
        "canonical_truth": "cell_ledgers",
    }


def _build_grid_metadata(
    cell: Path,
    *,
    index_id: str,
    backend: str,
    embedding_model: str,
    embedding_dimension: Optional[int],
    embedding_version: str,
    charge_count: int,
    created_at: Optional[str] = None,
) -> Dict[str, Any]:
    fingerprint = _current_grid_fingerprint(cell)
    return {
        "index_id": index_id,
        "cell_id": _read_cell_id(cell),
        "backend": backend,
        "embedding_model": embedding_model,
        "embedding_dimension": embedding_dimension,
        "embedding_version": embedding_version,
        "ledger_offsets": fingerprint["ledger_offsets"],
        "ledger_hashes": fingerprint["ledger_hashes"],
        "charge_count": charge_count,
        "created_at": created_at or datetime.now(timezone.utc).isoformat(),
        "canonical_truth": "cell_ledgers",
    }


def _current_grid_fingerprint(cell: Path) -> Dict[str, Any]:
    ledger_offsets: Dict[str, int] = {}
    ledger_hashes: Dict[str, str] = {}
    charge_count = 0
    for rel in LEDGER_PATHS:
        path = cell / rel
        key = rel.as_posix()
        if not path.exists():
            ledger_offsets[key] = 0
            ledger_hashes[key] = _sha256_bytes(b"")
            continue
        data = path.read_bytes()
        ledger_offsets[key] = len(data)
        ledger_hashes[key] = _sha256_bytes(data)
        if rel.as_posix() in {"traces/approved.jsonl", "charges/approved.jsonl"}:
            for line in data.decode("utf-8").splitlines():
                if line.strip():
                    charge_count += 1
    return {
        "ledger_offsets": ledger_offsets,
        "ledger_hashes": ledger_hashes,
        "charge_count": charge_count,
    }


def _read_cell_id(cell: Path) -> str:
    manifest_path = cell / "config" / "cell_manifest.json"
    if not manifest_path.exists():
        return ""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return str(manifest.get("cell_id") or "")


def _provider_dimension(provider: Any) -> Optional[int]:
    dimension = getattr(provider, "dimension", None)
    if callable(dimension):
        dimension = dimension()
    return int(dimension) if dimension is not None else None


def _provider_model(provider: Any, default: str) -> str:
    return str(
        getattr(provider, "model", None)
        or getattr(provider, "model_name", None)
        or default
    )


def _provider_version(provider: Any, default: str) -> str:
    return str(
        getattr(provider, "version", None)
        or getattr(provider, "embedding_version", None)
        or default
    )


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:

    """Compute cosine similarity between two equal-length vectors."""
    if len(a) != len(b):
        raise ValueError(f"Vector lengths differ: {len(a)} vs {len(b)}")
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)
