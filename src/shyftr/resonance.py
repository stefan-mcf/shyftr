"""Cross-Cell resonance detection and scoring for ShyftR.

Resonance is an advisory signal: it detects repeated Fragment, Trace, and
Alloy patterns across Cells and scores them for possible Doctrine proposal.
This module is intentionally read-only; review-gated Doctrine promotion lives
in ``shyftr.distill.doctrine``.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from .models import Alloy, Fragment, Outcome, Trace

FragmentMatch = Tuple[str, str, str, str, float]
TraceMatch = Tuple[str, str, str, str, float]
AlloyMatch = Tuple[str, str, str, str, float]


def _tokenize(text: str) -> Set[str]:
    """Return lowercase alphanumeric token set for sparse overlap."""
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
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def _bounded(value: float) -> float:
    return min(max(value, 0.0), 1.0)


def _pairwise_cross_cell_matches(
    ids: Sequence[str],
    cell_by_id: Dict[str, str],
    text_by_id: Dict[str, str],
    threshold: float,
) -> List[Tuple[str, str, str, str, float]]:
    matches: List[Tuple[str, str, str, str, float]] = []
    tokens_by_id = {item_id: _tokenize(text_by_id.get(item_id, "")) for item_id in ids}
    for index, left_id in enumerate(ids):
        for right_id in ids[index + 1 :]:
            left_cell = cell_by_id[left_id]
            right_cell = cell_by_id[right_id]
            if left_cell == right_cell:
                continue
            similarity = _jaccard(tokens_by_id[left_id], tokens_by_id[right_id])
            if similarity >= threshold:
                matches.append((left_id, right_id, left_cell, right_cell, similarity))
    return matches


def detect_similar_fragments(
    fragments: Sequence[Fragment], *, threshold: float = 0.25
) -> List[FragmentMatch]:
    """Detect similar Fragments across Cells by sparse token overlap."""
    ids = [fragment.fragment_id for fragment in fragments]
    return _pairwise_cross_cell_matches(
        ids,
        {fragment.fragment_id: fragment.cell_id for fragment in fragments},
        {fragment.fragment_id: fragment.text for fragment in fragments},
        threshold,
    )


def detect_similar_traces(
    traces: Sequence[Trace], *, threshold: float = 0.25
) -> List[TraceMatch]:
    """Detect similar Traces across Cells by statement overlap."""
    ids = [trace.trace_id for trace in traces]
    return _pairwise_cross_cell_matches(
        ids,
        {trace.trace_id: trace.cell_id for trace in traces},
        {trace.trace_id: trace.statement for trace in traces},
        threshold,
    )


def detect_similar_alloys(
    alloys: Sequence[Alloy], *, threshold: float = 0.20
) -> List[AlloyMatch]:
    """Detect similar Alloys across Cells by summary overlap."""
    ids = [alloy.alloy_id for alloy in alloys]
    return _pairwise_cross_cell_matches(
        ids,
        {alloy.alloy_id: alloy.cell_id for alloy in alloys},
        {alloy.alloy_id: alloy.summary for alloy in alloys},
        threshold,
    )


@dataclass(frozen=True)
class ResonanceScore:
    """Composite multi-Cell resonance score for one Alloy."""

    alloy_id: str
    recurrence_count: int
    cell_diversity: int
    avg_confidence: Optional[float] = None
    success_ratio: Optional[float] = None
    score: float = 0.0


def _successful_outcome(outcome: Outcome) -> bool:
    verdict = outcome.verdict.lower()
    return verdict == "success" or (outcome.score is not None and outcome.score >= 0.7)


def compute_resonance(
    traces: Sequence[Trace],
    alloys: Sequence[Alloy],
    fragments: Optional[Sequence[Fragment]] = None,
    outcomes: Optional[Sequence[Outcome]] = None,
    *,
    trace_threshold: float = 0.25,
    alloy_threshold: float = 0.20,
    fragment_threshold: float = 0.25,
    require_cross_cell: bool = True,
) -> List[ResonanceScore]:
    """Score Alloy resonance from recurrence, diversity, confidence, success.

    The function only reads supplied objects and never writes ledgers.  Cross-Cell
    evidence may come from similar source Traces, similar Alloys, or similar
    source Fragments.  Returned scores are deterministic and sorted by score
    descending, then Alloy ID ascending.
    """
    traces_by_id = {trace.trace_id: trace for trace in traces}
    fragments_by_id = {fragment.fragment_id: fragment for fragment in fragments or []}

    trace_matches = detect_similar_traces(traces, threshold=trace_threshold)
    alloy_matches = detect_similar_alloys(alloys, threshold=alloy_threshold)
    fragment_matches = detect_similar_fragments(
        fragments or [], threshold=fragment_threshold
    )

    related_cells_by_alloy: Dict[str, Set[str]] = defaultdict(set)
    recurrence_by_alloy: Dict[str, Set[str]] = defaultdict(set)
    confidence_by_alloy: Dict[str, List[float]] = defaultdict(list)

    for alloy in alloys:
        related_cells_by_alloy[alloy.alloy_id].add(alloy.cell_id)
        recurrence_by_alloy[alloy.alloy_id].add(alloy.alloy_id)
        if alloy.confidence is not None:
            confidence_by_alloy[alloy.alloy_id].append(alloy.confidence)

    for left_id, right_id, left_cell, right_cell, _similarity in trace_matches:
        for alloy in alloys:
            source_ids = set(alloy.source_trace_ids)
            if left_id in source_ids or right_id in source_ids:
                related_cells_by_alloy[alloy.alloy_id].update((left_cell, right_cell))
                recurrence_by_alloy[alloy.alloy_id].update((left_id, right_id))

    alloys_by_id = {alloy.alloy_id: alloy for alloy in alloys}
    for left_id, right_id, left_cell, right_cell, _similarity in alloy_matches:
        for alloy_id, peer_id in ((left_id, right_id), (right_id, left_id)):
            related_cells_by_alloy[alloy_id].update((left_cell, right_cell))
            recurrence_by_alloy[alloy_id].update((left_id, right_id))
            peer = alloys_by_id.get(peer_id)
            if peer and peer.confidence is not None:
                confidence_by_alloy[alloy_id].append(peer.confidence)

    fragment_ids_by_trace_id = {
        trace.trace_id: set(trace.source_fragment_ids) for trace in traces
    }
    for left_id, right_id, left_cell, right_cell, _similarity in fragment_matches:
        for alloy in alloys:
            source_fragment_ids: Set[str] = set()
            for trace_id in alloy.source_trace_ids:
                source_fragment_ids.update(fragment_ids_by_trace_id.get(trace_id, set()))
            if left_id in source_fragment_ids or right_id in source_fragment_ids:
                related_cells_by_alloy[alloy.alloy_id].update((left_cell, right_cell))
                recurrence_by_alloy[alloy.alloy_id].update((left_id, right_id))

    successful_by_trace: Dict[str, int] = defaultdict(int)
    total_by_trace: Dict[str, int] = defaultdict(int)
    for outcome in outcomes or []:
        for trace_id in outcome.trace_ids:
            total_by_trace[trace_id] += 1
            if _successful_outcome(outcome):
                successful_by_trace[trace_id] += 1

    scores: List[ResonanceScore] = []
    for alloy in alloys:
        cells = related_cells_by_alloy.get(alloy.alloy_id, {alloy.cell_id})
        if require_cross_cell and len(cells) < 2:
            continue

        confidences = confidence_by_alloy.get(alloy.alloy_id, [])
        avg_confidence = sum(confidences) / len(confidences) if confidences else None

        total_outcomes = sum(total_by_trace[trace_id] for trace_id in alloy.source_trace_ids)
        if total_outcomes:
            success_ratio = (
                sum(successful_by_trace[trace_id] for trace_id in alloy.source_trace_ids)
                / total_outcomes
            )
        else:
            success_ratio = None

        recurrence_count = len(recurrence_by_alloy.get(alloy.alloy_id, {alloy.alloy_id}))
        cell_diversity = len(cells)
        recurrence_factor = min(recurrence_count / 5.0, 1.0) * 0.30
        diversity_factor = min(cell_diversity / 3.0, 1.0) * 0.20
        confidence_factor = (avg_confidence if avg_confidence is not None else 0.5) * 0.25
        success_factor = (success_ratio if success_ratio is not None else 0.5) * 0.25
        score = _bounded(recurrence_factor + diversity_factor + confidence_factor + success_factor)

        scores.append(
            ResonanceScore(
                alloy_id=alloy.alloy_id,
                recurrence_count=recurrence_count,
                cell_diversity=cell_diversity,
                avg_confidence=avg_confidence,
                success_ratio=success_ratio,
                score=round(score, 4),
            )
        )

    scores.sort(key=lambda item: (-item.score, item.alloy_id))
    return scores


def get_high_resonance_alloys(
    resonance_scores: Iterable[ResonanceScore], *, threshold: float = 0.50
) -> List[ResonanceScore]:
    """Return resonance scores that meet the Doctrine proposal threshold."""
    return [score for score in resonance_scores if score.score >= threshold]
