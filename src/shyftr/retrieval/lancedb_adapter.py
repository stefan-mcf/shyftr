"""Optional LanceDB-backed VectorIndex adapter for the ShyftR Grid.

LanceDB is an optional acceleration backend. Importing this module must not
require LanceDB to be installed; operations that need LanceDB raise actionable
RuntimeError messages when the optional extra is missing.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .vector import (
    PathLike,
    _build_grid_metadata,
    _current_grid_fingerprint,
    _empty_grid_metadata,
    _provider_dimension,
    _provider_model,
    _provider_version,
    rebuild_vector_index,
)


OPTIONAL_EXTRA_ERROR = (
    "optional LanceDB Grid adapter is not installed; install ShyftR with "
    "the 'lancedb' extra to use --backend lancedb"
)


def lancedb_available() -> bool:
    """Return True when the optional LanceDB package can be imported."""
    try:
        import lancedb  # noqa: F401
    except ImportError:
        return False
    return True


class LanceDBVectorIndex:
    """LanceDB-backed VectorIndex implementation.

    The table stores vectors and JSON-serialised ShyftR metadata. The canonical
    Cell ledgers remain the source of truth; this adapter is rebuildable Grid
    acceleration only.
    """

    def __init__(
        self,
        db_path: Optional[PathLike] = None,
        *,
        table_name: str = "vectors",
        index_id: str = "grid-lancedb",
        embedding_model: str = "unknown",
        embedding_version: str = "unknown",
    ) -> None:
        self.db_path = Path(db_path) if db_path is not None else None
        self.table_name = table_name
        self.index_id = index_id
        self.embedding_model = embedding_model
        self.embedding_version = embedding_version
        self._metadata: Dict[str, Any] = _empty_grid_metadata(
            index_id=index_id,
            backend="lancedb",
            embedding_model=embedding_model,
            embedding_dimension=None,
            embedding_version=embedding_version,
        )
        self._row_count = 0

    @property
    def available(self) -> bool:
        return lancedb_available()

    def rebuild(
        self,
        cell_path: PathLike,
        provider: Any,
        *,
        include_statuses: Optional[Sequence[str]] = None,
    ) -> int:
        self._require_lancedb()
        cell = Path(cell_path)
        if self.db_path is None:
            self.db_path = cell / "grid" / "lancedb"
        self.clear()
        count = rebuild_vector_index(
            self,
            cell,
            provider,
            include_statuses=include_statuses,
        )
        provider_model = _provider_model(provider, self.embedding_model)
        provider_version = _provider_version(provider, self.embedding_version)
        self.embedding_model = provider_model
        self.embedding_version = provider_version
        self._metadata = _build_grid_metadata(
            cell,
            index_id=self.index_id,
            backend="lancedb",
            embedding_model=provider_model,
            embedding_dimension=_provider_dimension(provider),
            embedding_version=provider_version,
            charge_count=count,
        )
        self._row_count = count
        return count

    def add(
        self,
        doc_id: str,
        vector: Sequence[float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._require_lancedb()
        row = {
            "doc_id": doc_id,
            "vector": [float(v) for v in vector],
            "metadata_json": json.dumps(metadata or {}, sort_keys=True),
        }
        table = self._open_table()
        if table is None:
            db = self._connect()
            db.create_table(self.table_name, data=[row], mode="overwrite")
        else:
            table.add([row])
        self._row_count += 1

    def query(
        self,
        vector: Sequence[float],
        *,
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        self._require_lancedb()
        table = self._open_table()
        if table is None:
            return []
        rows = table.search([float(v) for v in vector]).limit(max(top_k, 1)).to_list()
        results: List[Tuple[str, float, Dict[str, Any]]] = []
        for row in rows:
            metadata = json.loads(row.get("metadata_json") or "{}")
            if filter_metadata and any(metadata.get(k) != v for k, v in filter_metadata.items()):
                continue
            score = _score_from_row(row)
            results.append((str(row.get("doc_id") or metadata.get("trace_id") or ""), score, metadata))
        results.sort(key=lambda item: item[1], reverse=True)
        return results[:top_k]

    def status(self, cell_path: Optional[PathLike] = None, provider: Any = None) -> Dict[str, Any]:
        metadata = self.export_metadata()
        stale_reasons: List[str] = []
        if not self.available:
            stale_reasons.append("unavailable")
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
            "index_id": self.index_id,
            "backend": "lancedb",
            "available": self.available,
            "size": self.size(),
            "stale": bool(stale_reasons),
            "stale_reasons": sorted(set(stale_reasons)),
            "metadata": metadata,
            "db_path": str(self.db_path) if self.db_path is not None else None,
            "canonical_truth": "cell_ledgers",
        }

    def export_metadata(self) -> Dict[str, Any]:
        return json.loads(json.dumps(self._metadata, sort_keys=True))

    def size(self) -> int:
        if not self.available:
            return self._row_count
        table = self._open_table()
        if table is None:
            return 0
        try:
            return int(table.count_rows())
        except Exception:
            return self._row_count

    def clear(self) -> None:
        self._require_lancedb()
        db = self._connect()
        try:
            db.drop_table(self.table_name, ignore_missing=True)
        except TypeError:
            try:
                db.drop_table(self.table_name)
            except Exception:
                pass
        except Exception:
            pass
        self._row_count = 0

    def _require_lancedb(self) -> None:
        if not self.available:
            raise RuntimeError(OPTIONAL_EXTRA_ERROR)

    def _connect(self) -> Any:
        self._require_lancedb()
        if self.db_path is None:
            raise RuntimeError("LanceDBVectorIndex requires db_path before use")
        self.db_path.mkdir(parents=True, exist_ok=True)
        import lancedb
        return lancedb.connect(str(self.db_path))

    def _open_table(self) -> Any:
        db = self._connect()
        try:
            return db.open_table(self.table_name)
        except Exception:
            return None


def _score_from_row(row: Dict[str, Any]) -> float:
    if "_distance" in row:
        return 1.0 / (1.0 + float(row["_distance"]))
    if "_score" in row:
        return float(row["_score"])
    if "score" in row:
        return float(row["score"])
    return 0.0
