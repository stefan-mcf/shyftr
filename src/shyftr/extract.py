from __future__ import annotations

import hashlib
from pathlib import Path
import re
from typing import Dict, Iterable, List, Optional, Union
from uuid import uuid4

from .ledger import append_jsonl, read_jsonl
from .models import Fragment, Source
from .policy import check_source_boundary

PathLike = Union[str, Path]

_EXPLICIT_FIELD_RE = re.compile(r"^memory_fragment_([a-z_]+):\s*(.*)$", re.IGNORECASE)
_HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$")
_MAX_FRAGMENT_CHARS = 360


def extract_fragments(cell_path: PathLike, source: Source) -> List[Fragment]:
    """Extract bounded, untrusted Fragment records from a Source."""
    cell = Path(cell_path)
    fragments_ledger = cell / "ledger" / "fragments.jsonl"
    if not fragments_ledger.exists():
        raise ValueError(f"fragments ledger does not exist for Cell: {fragments_ledger}")
    if not source.uri:
        raise ValueError("Source uri is required for extraction")
    if source.cell_id != _read_cell_id_from_manifest(cell):
        raise ValueError("Source cell_id does not match Cell manifest")

    source_text = Path(source.uri).read_text(encoding="utf-8")
    existing = _existing_fragments_by_key(fragments_ledger)
    extracted: List[Fragment] = []

    for draft in _draft_fragments(source_text, source):
        fragment = _build_fragment(source, draft)
        key = _fragment_key(fragment.source_id, fragment.text)
        if key in existing:
            extracted.append(existing[key])
            continue
        if fragment.boundary_status != "boundary_failed":
            append_jsonl(fragments_ledger, fragment.to_dict())
            existing[key] = fragment
        extracted.append(fragment)

    return extracted


def _draft_fragments(source_text: str, source: Source) -> List[Dict[str, object]]:
    explicit = _parse_explicit_fragments(source_text)
    if explicit:
        return explicit
    return _parse_prose_fragments(source_text, default_kind=source.kind)


def _parse_explicit_fragments(source_text: str) -> List[Dict[str, object]]:
    fragments: List[Dict[str, object]] = []
    current: Dict[str, object] = {}
    for line in source_text.splitlines():
        match = _EXPLICIT_FIELD_RE.match(line.strip())
        if not match:
            continue
        key, value = match.groups()
        if key == "text" and current.get("text"):
            fragments.append(current)
            current = {}
        current[key] = _coerce_field_value(key, value)
    if current.get("text"):
        fragments.append(current)
    return fragments


def _parse_prose_fragments(source_text: str, *, default_kind: str) -> List[Dict[str, object]]:
    drafts: List[Dict[str, object]] = []
    heading: Optional[str] = None
    paragraph_lines: List[str] = []

    def flush() -> None:
        nonlocal paragraph_lines
        text = " ".join(line.strip() for line in paragraph_lines if line.strip()).strip()
        paragraph_lines = []
        if not text:
            return
        for chunk in _bounded_chunks(text):
            tags = [_slug(heading)] if heading else []
            drafts.append(
                {
                    "text": chunk,
                    "kind": default_kind,
                    "tags": tags,
                    "source_excerpt": _excerpt(chunk),
                }
            )

    for raw_line in source_text.splitlines():
        stripped = raw_line.strip()
        heading_match = _HEADING_RE.match(stripped)
        if heading_match:
            flush()
            heading = heading_match.group(1)
            continue
        if not stripped:
            flush()
            continue
        paragraph_lines.append(stripped)
    flush()
    return drafts


def _build_fragment(source: Source, draft: Dict[str, object]) -> Fragment:
    text = str(draft.get("text", "")).strip()
    boundary = check_source_boundary(text)
    boundary_status = "pending" if boundary.accepted else "boundary_failed"
    return Fragment(
        fragment_id=f"frag-{uuid4().hex}",
        source_id=source.source_id,
        cell_id=source.cell_id,
        kind=str(draft.get("kind") or source.kind),
        text=text,
        source_excerpt=str(draft.get("source_excerpt") or _excerpt(text)),
        boundary_status=boundary_status,
        review_status="pending",
        confidence=draft.get("confidence") if isinstance(draft.get("confidence"), (int, float)) else None,
        tags=list(draft.get("tags") or []),
    )


def _coerce_field_value(key: str, value: str) -> object:
    value = value.strip()
    if key == "tags":
        return [part.strip() for part in value.split(",") if part.strip()]
    if key == "confidence":
        return float(value)
    return value


def _existing_fragments_by_key(fragments_ledger: Path) -> Dict[str, Fragment]:
    existing: Dict[str, Fragment] = {}
    for _, record in read_jsonl(fragments_ledger):
        fragment = Fragment.from_dict(record)
        existing[_fragment_key(fragment.source_id, fragment.text)] = fragment
    return existing


def _fragment_key(source_id: str, text: str) -> str:
    return f"{source_id}:{hashlib.sha256(text.encode('utf-8')).hexdigest()}"


def _bounded_chunks(text: str) -> Iterable[str]:
    if len(text) <= _MAX_FRAGMENT_CHARS:
        yield text
        return
    sentences = re.split(r"(?<=[.!?])\s+", text)
    current = ""
    for sentence in sentences:
        candidate = f"{current} {sentence}".strip()
        if len(candidate) <= _MAX_FRAGMENT_CHARS:
            current = candidate
            continue
        if current:
            yield current
        current = sentence[:_MAX_FRAGMENT_CHARS]
    if current:
        yield current


def _excerpt(text: str) -> str:
    compact = " ".join(text.split())
    return compact[:120]


def _slug(value: Optional[str]) -> str:
    if not value:
        return ""
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "section"


def _read_cell_id_from_manifest(cell: Path) -> str:
    manifest_path = cell / "config" / "cell_manifest.json"
    if not manifest_path.exists():
        raise ValueError(f"Cell manifest does not exist: {manifest_path}")
    import json

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    cell_id = manifest.get("cell_id")
    if not cell_id:
        raise ValueError("Cell manifest is missing cell_id")
    return str(cell_id)
