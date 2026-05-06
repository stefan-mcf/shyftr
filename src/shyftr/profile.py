from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from shyftr.models import Trace
from shyftr.mutations import active_charge_ids, approved_traces

PathLike = Union[str, Path]

PROFILE_ARTIFACTS = {
    "json": "summaries/profile.json",
    "markdown": "summaries/profile.md",
    "compact_markdown": "summaries/profile.compact.md",
    "index": "summaries/profile.index.json",
}


@dataclass(frozen=True)
class ProfileProjection:
    """Rebuildable profile projection derived from Cell ledger truth."""

    projection_id: str
    cell_id: str
    profile_json: Dict[str, Any]
    markdown: str
    compact_markdown: str
    index_json: Dict[str, Any]
    source_charge_ids: List[str]
    max_tokens: int
    artifact_paths: Dict[str, str] = field(default_factory=lambda: dict(PROFILE_ARTIFACTS))


def build_profile(cell_path: PathLike, max_tokens: int = 2000) -> ProfileProjection:
    """Build profile projections from reviewed memory without mutating Cell truth.

    The returned artifacts are derived summaries. They are safe to delete and
    rebuild because canonical truth remains in append-only Cell ledgers.
    """

    cell = Path(cell_path)
    cell_id = _read_cell_id(cell)
    active_ids = active_charge_ids(cell, projection="profile")
    entries = [_entry_from_trace(trace) for trace in approved_traces(cell) if trace.trace_id in active_ids]
    source_charge_ids = [entry["charge_id"] for entry in entries]
    projection_seed = json.dumps(
        {"cell_id": cell_id, "source_charge_ids": source_charge_ids, "entries": entries},
        sort_keys=True,
        separators=(",", ":"),
    )
    projection_id = f"profile-{hashlib.sha256(projection_seed.encode('utf-8')).hexdigest()[:16]}"

    profile_json: Dict[str, Any] = {
        "projection_id": projection_id,
        "cell_id": cell_id,
        "projection_status": "rebuildable",
        "canonical_truth": "cell_ledgers",
        "source_charge_ids": source_charge_ids,
        "entry_count": len(entries),
        "entries": entries,
    }
    markdown = _render_markdown(cell_id, entries, projection_id)
    compact_markdown = _render_compact_markdown(cell_id, entries, max_tokens=max_tokens)
    index_json: Dict[str, Any] = {
        "projection_id": projection_id,
        "cell_id": cell_id,
        "projection_status": "rebuildable",
        "canonical_truth": "cell_ledgers",
        "source_charge_ids": source_charge_ids,
        "source_count": len(source_charge_ids),
        "artifacts": dict(PROFILE_ARTIFACTS),
    }
    return ProfileProjection(
        projection_id=projection_id,
        cell_id=cell_id,
        profile_json=profile_json,
        markdown=markdown,
        compact_markdown=compact_markdown,
        index_json=index_json,
        source_charge_ids=source_charge_ids,
        max_tokens=max_tokens,
    )


def write_profile_projections(cell_path: PathLike, max_tokens: int = 2000) -> Dict[str, Path]:
    """Write rebuildable profile projection artifacts under summaries/."""

    cell = Path(cell_path)
    projection = build_profile(cell, max_tokens=max_tokens)
    paths = {name: cell / relative for name, relative in PROFILE_ARTIFACTS.items()}
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    paths["json"].write_text(_json_dump(projection.profile_json), encoding="utf-8")
    paths["markdown"].write_text(projection.markdown, encoding="utf-8")
    paths["compact_markdown"].write_text(projection.compact_markdown, encoding="utf-8")
    paths["index"].write_text(_json_dump(projection.index_json), encoding="utf-8")
    return paths


def _entry_from_trace(trace: Trace) -> Dict[str, Any]:
    return {
        "charge_id": trace.trace_id,
        "statement": trace.statement,
        "kind": trace.kind,
        "confidence": round(trace.confidence, 4) if isinstance(trace.confidence, float) else trace.confidence,
        "status": trace.status,
        "tags": list(trace.tags),
        "source_fragment_ids": list(trace.source_fragment_ids),
    }


def _render_markdown(cell_id: str, entries: List[Dict[str, Any]], projection_id: str) -> str:
    lines = [
        "# ShyftR Memory Profile",
        "",
        f"Cell: `{cell_id}`",
        f"Projection: `{projection_id}`",
        "Status: rebuildable projection; canonical truth remains in Cell ledgers.",
        "",
        "## Charges",
    ]
    if not entries:
        lines.extend(["", "No reviewed Charges are available for this profile."])
    for entry in entries:
        kind = entry.get("kind") or "memory"
        confidence = entry.get("confidence")
        confidence_text = "" if confidence is None else f" confidence={confidence:.2f}"
        lines.append("")
        lines.append(f"- ({kind}) {entry['statement']} [{entry['charge_id']}]{confidence_text}")
        tags = entry.get("tags") or []
        if tags:
            lines.append(f"  - tags: {', '.join(str(tag) for tag in tags)}")
    return "\n".join(lines).rstrip() + "\n"


def _render_compact_markdown(cell_id: str, entries: List[Dict[str, Any]], max_tokens: int) -> str:
    budget = max(max_tokens, 0)
    lines = ["# ShyftR Compact Profile", "", f"Cell: `{cell_id}`", ""]
    used = _token_count("\n".join(lines))
    emitted = False
    for entry in entries:
        kind = entry.get("kind") or "memory"
        line = f"- {kind}: {entry['statement']} [{entry['charge_id']}]"
        lines.append(line)
        used += _token_count(line)
        emitted = True
    if not emitted:
        lines.append("No reviewed Charges are available for this compact profile.")
    return "\n".join(lines).rstrip() + "\n"


def _read_cell_id(cell: Path) -> str:
    manifest_path = cell / "config" / "cell_manifest.json"
    if not manifest_path.exists():
        raise ValueError(f"Cell manifest does not exist: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    cell_id = manifest.get("cell_id")
    if not cell_id:
        raise ValueError("Cell manifest is missing cell_id")
    return str(cell_id)


def _json_dump(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _token_count(text: str) -> int:
    return len(text.split()) if text else 0


def _truncate_words(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    if max_words <= 1:
        return words[0]
    return " ".join(words[:max_words])
