"""Alloy distillation — recursively distill related Traces into proposals.

Alloys are proposals only; this module must not silently promote Doctrine
or mutate durable Trace authority.  Alloys require at least two source
Trace IDs unless the caller explicitly opts into singleton handling.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, FrozenSet, List, Optional, Sequence, Set, Tuple, Union

from ..ledger import append_jsonl, read_jsonl
from ..models import Alloy, Trace

PathLike = Union[str, Path]


# ---------------------------------------------------------------------------
# Clustering helpers
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> Set[str]:
    """Lowercase alphanumeric token set for sparse overlap."""
    tokens: Set[str] = set()
    for word in text.lower().split():
        cleaned = "".join(ch for ch in word if ch.isalnum())
        if cleaned:
            tokens.add(cleaned)
    return tokens


def _jaccard(a: Set[str], b: Set[str]) -> float:
    """Jaccard similarity between two token sets."""
    if not a and not b:
        return 0.0
    intersection = a & b
    union = a | b
    return len(intersection) / len(union) if union else 0.0


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    """Cosine similarity between two dense vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


# ---------------------------------------------------------------------------
# Duplicate and conflict detection
# ---------------------------------------------------------------------------

def detect_duplicates(traces: List[Trace]) -> List[Tuple[str, str]]:
    """Return pairs of trace_ids with identical statements (duplicates)."""
    seen: Dict[str, str] = {}
    duplicates: List[Tuple[str, str]] = []
    for trace in traces:
        key = trace.statement.strip().lower()
        if key in seen:
            duplicates.append((seen[key], trace.trace_id))
        else:
            seen[key] = trace.trace_id
    return duplicates


def detect_conflicts(traces: List[Trace]) -> List[Tuple[str, str]]:
    """Return pairs of trace_ids with contradictory statements.

    Conflict detection uses a simple heuristic: two Traces conflict if
    they share at least one tag AND their statements contain negation
    patterns (e.g. 'never' vs positive, 'always' vs 'never').
    """
    negation_words = {"never", "not", "no", "must not", "should not", "cannot"}
    conflict_pairs: List[Tuple[str, str]] = []

    for i, t_a in enumerate(traces):
        tokens_a = _tokenize(t_a.statement)
        tags_a = set(t_a.tags)
        has_neg_a = bool(tokens_a & negation_words)

        for t_b in traces[i + 1 :]:
            tags_b = set(t_b.tags)
            if not (tags_a & tags_b):
                continue

            tokens_b = _tokenize(t_b.statement)
            has_neg_b = bool(tokens_b & negation_words)

            # Conflict: same tags, one negated, one positive, with overlap
            if has_neg_a != has_neg_b:
                overlap = _jaccard(tokens_a, tokens_b)
                if overlap > 0.3:
                    conflict_pairs.append((t_a.trace_id, t_b.trace_id))

    return conflict_pairs


# ---------------------------------------------------------------------------
# Clustering
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Cluster:
    """A cluster of related Traces ready for Alloy proposal."""
    trace_ids: FrozenSet[str]
    cell_id: str
    theme: str
    tags: FrozenSet[str]
    kind: Optional[str]
    avg_confidence: Optional[float]


def cluster_traces(
    traces: List[Trace],
    *,
    tag_overlap_threshold: float = 0.3,
    sparse_overlap_threshold: float = 0.2,
    vector_threshold: float = 0.0,
    vectors: Optional[Dict[str, Sequence[float]]] = None,
) -> List[Cluster]:
    """Cluster approved Traces by tags, sparse lexical overlap,
    and optional vector similarity.

    Returns a list of Cluster objects.  Each cluster has at least two
    Trace IDs (singletons are skipped as no-ops).
    """
    # Group by cell_id first
    by_cell: Dict[str, List[Trace]] = defaultdict(list)
    for trace in traces:
        if trace.status == "approved":
            by_cell[trace.cell_id].append(trace)

    all_clusters: List[Cluster] = []

    for cell_id, cell_traces in by_cell.items():
        # Union-find for clustering
        parent: Dict[str, str] = {t.trace_id: t.trace_id for t in cell_traces}

        def find(x: str) -> str:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x: str, y: str) -> None:
            rx, ry = find(x), find(y)
            if rx != ry:
                parent[rx] = ry

        # Precompute tokens
        tokens_by_id: Dict[str, Set[str]] = {}
        tags_by_id: Dict[str, Set[str]] = {}
        conf_by_id: Dict[str, Optional[float]] = {}

        for trace in cell_traces:
            tokens_by_id[trace.trace_id] = _tokenize(trace.statement)
            if trace.rationale:
                tokens_by_id[trace.trace_id] |= _tokenize(trace.rationale)
            tags_by_id[trace.trace_id] = set(trace.tags)
            conf_by_id[trace.trace_id] = trace.confidence

        # Merge by tag overlap
        id_list = [t.trace_id for t in cell_traces]
        for i, tid_a in enumerate(id_list):
            for tid_b in id_list[i + 1 :]:
                tags_a = tags_by_id[tid_a]
                tags_b = tags_by_id[tid_b]
                if tags_a and tags_b:
                    tag_j = _jaccard(tags_a, tags_b)
                    if tag_j >= tag_overlap_threshold:
                        union(tid_a, tid_b)

        # Merge by sparse lexical overlap
        for i, tid_a in enumerate(id_list):
            for tid_b in id_list[i + 1 :]:
                if find(tid_a) == find(tid_b):
                    continue
                sparse_j = _jaccard(
                    tokens_by_id[tid_a], tokens_by_id[tid_b]
                )
                if sparse_j >= sparse_overlap_threshold:
                    union(tid_a, tid_b)

        # Merge by vector similarity if provided
        if vectors and vector_threshold > 0.0:
            for i, tid_a in enumerate(id_list):
                vec_a = vectors.get(tid_a)
                if vec_a is None:
                    continue
                for tid_b in id_list[i + 1 :]:
                    if find(tid_a) == find(tid_b):
                        continue
                    vec_b = vectors.get(tid_b)
                    if vec_b is None:
                        continue
                    sim = _cosine(vec_a, vec_b)
                    if sim >= vector_threshold:
                        union(tid_a, tid_b)

        # Build clusters from connected components
        groups: Dict[str, List[str]] = defaultdict(list)
        for tid in id_list:
            groups[find(tid)].append(tid)

        for root, member_ids in groups.items():
            if len(member_ids) < 2:
                continue  # singletons are no-ops

            all_tags: Set[str] = set()
            confs: List[float] = []

            for tid in member_ids:
                all_tags |= tags_by_id[tid]
                c = conf_by_id[tid]
                if c is not None:
                    confs.append(c)

            avg_conf = sum(confs) / len(confs) if confs else None

            # Theme: join top tags
            theme_tags = sorted(all_tags)[:5] if all_tags else []
            theme = " / ".join(theme_tags) if theme_tags else "mixed"

            all_clusters.append(
                Cluster(
                    trace_ids=frozenset(member_ids),
                    cell_id=cell_id,
                    theme=theme,
                    tags=frozenset(all_tags),
                    kind=None,
                    avg_confidence=avg_conf,
                )
            )

    return all_clusters


# ---------------------------------------------------------------------------
# Alloy proposal generation
# ---------------------------------------------------------------------------

def _alloy_id_for(cluster: Cluster) -> str:
    """Deterministic alloy_id from cluster fingerprint."""
    seed = "|".join(sorted(cluster.trace_ids))
    digest = hashlib.sha256(seed.encode()).hexdigest()[:12]
    return f"alloy-{digest}"


def _build_summary(traces: List[Trace], theme: str) -> str:
    """Build a deterministic Alloy summary from constituent Traces."""
    statements = sorted(t.statement for t in traces)
    joined = "; ".join(statements)
    return f"Alloy proposal ({theme}): {joined}"


def propose_alloys(
    clusters: List[Cluster],
    traces_by_id: Dict[str, Trace],
    *,
    require_min_sources: int = 2,
) -> List[Alloy]:
    """Generate Alloy proposals from clusters.

    Each cluster with at least ``require_min_sources`` Traces produces
    one Alloy proposal.  Singletons are skipped (no-op).
    """
    proposals: List[Alloy] = []

    for cluster in clusters:
        member_traces = [
            traces_by_id[tid]
            for tid in sorted(cluster.trace_ids)
            if tid in traces_by_id
        ]

        if len(member_traces) < require_min_sources:
            continue

        alloy_id = _alloy_id_for(cluster)
        summary = _build_summary(member_traces, cluster.theme)

        alloy = Alloy(
            alloy_id=alloy_id,
            cell_id=cluster.cell_id,
            theme=cluster.theme,
            summary=summary,
            source_trace_ids=sorted(cluster.trace_ids),
            proposal_status="proposed",
            confidence=cluster.avg_confidence,
        )
        proposals.append(alloy)

    return proposals


# ---------------------------------------------------------------------------
# Ledger integration
# ---------------------------------------------------------------------------

def append_alloys_to_proposed(
    cell_path: PathLike,
    alloys: List[Alloy],
) -> int:
    """Append Alloy proposals to alloys/proposed.jsonl.

    Returns the number of Alloys appended.
    """
    ledger_path = Path(cell_path) / "alloys" / "proposed.jsonl"
    count = 0
    for alloy in alloys:
        append_jsonl(ledger_path, alloy.to_dict())
        count += 1
    return count


def read_approved_traces(cell_path: PathLike) -> List[Trace]:
    """Read all approved Traces from traces/approved.jsonl."""
    trace_path = Path(cell_path) / "traces" / "approved.jsonl"
    traces: List[Trace] = []
    for _line_num, record in read_jsonl(trace_path):
        traces.append(Trace.from_dict(record))
    return traces


# ---------------------------------------------------------------------------
# High-level distillation entry point
# ---------------------------------------------------------------------------

def distill_alloys(
    cell_path: PathLike,
    *,
    tag_overlap_threshold: float = 0.3,
    sparse_overlap_threshold: float = 0.2,
    vector_threshold: float = 0.0,
    vectors: Optional[Dict[str, Sequence[float]]] = None,
) -> Dict[str, Any]:
    """Full distillation pipeline for a single Cell.

    Reads approved Traces, clusters them, detects duplicates/conflicts,
    proposes Alloys, and appends them to alloys/proposed.jsonl.

    Returns a summary dict with cluster count, alloy count, duplicates,
    and conflicts.
    """
    traces = read_approved_traces(cell_path)
    traces_by_id = {t.trace_id: t for t in traces}

    clusters = cluster_traces(
        traces,
        tag_overlap_threshold=tag_overlap_threshold,
        sparse_overlap_threshold=sparse_overlap_threshold,
        vector_threshold=vector_threshold,
        vectors=vectors,
    )

    duplicates = detect_duplicates(traces)
    conflicts = detect_conflicts(traces)

    alloys = propose_alloys(clusters, traces_by_id)
    appended = append_alloys_to_proposed(cell_path, alloys)

    return {
        "trace_count": len(traces),
        "cluster_count": len(clusters),
        "alloy_count": appended,
        "duplicates": duplicates,
        "conflicts": conflicts,
    }
