from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Union


PathLike = Union[str, Path]

LEDGER_HEADS_REL = Path("ledger") / "ledger_heads.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ledger_files(cell: Path) -> List[Path]:
    paths: List[Path] = []
    for root_name in ("ledger", "charges", "traces", "coils", "rails", "alloys", "doctrine"):
        root = cell / root_name
        if root.exists():
            paths.extend(sorted(p for p in root.rglob("*.jsonl") if p.is_file()))
    return sorted(set(paths), key=lambda p: p.relative_to(cell).as_posix())


def _canonical_row_bytes(record: Dict[str, Any]) -> bytes:
    payload = {k: v for k, v in record.items() if k not in {"row_hash", "previous_row_hash"}}
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _read_jsonl_raw(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        for line_number, line in enumerate(fh, 1):
            stripped = line.strip()
            if stripped:
                yield line_number, json.loads(stripped)


def compute_ledger_chain(path: Path) -> Dict[str, Any]:
    previous = ""
    rows: List[Dict[str, Any]] = []
    for line_number, record in _read_jsonl_raw(path):
        digest = hashlib.sha256(previous.encode("utf-8") + b"\0" + _canonical_row_bytes(record)).hexdigest()
        embedded_row_hash = record.get("row_hash")
        embedded_previous = record.get("previous_row_hash")
        rows.append({
            "line_number": line_number,
            "row_hash": digest,
            "previous_row_hash": previous,
            "embedded_row_hash": embedded_row_hash,
            "embedded_previous_row_hash": embedded_previous,
            "embedded_matches": (embedded_row_hash in (None, digest)) and (embedded_previous in (None, previous)),
        })
        previous = digest
    return {
        "row_count": len(rows),
        "head_hash": previous,
        "rows": rows,
        "algorithm": "sha256(prev_hash + NUL + canonical_json_without_chain_fields)",
    }


def adopt_ledger_heads(cell_path: PathLike) -> Dict[str, Any]:
    cell = Path(cell_path)
    ledgers: Dict[str, Any] = {}
    for path in _ledger_files(cell):
        rel = path.relative_to(cell).as_posix()
        chain = compute_ledger_chain(path)
        ledgers[rel] = {"row_count": chain["row_count"], "head_hash": chain["head_hash"]}
    manifest = {
        "format": "shyftr.ledger_heads.v1",
        "created_at": _now(),
        "canonical_truth": "cell_ledgers",
        "ledgers": ledgers,
    }
    out = cell / LEDGER_HEADS_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return manifest


def verify_ledgers(cell_path: PathLike) -> Dict[str, Any]:
    cell = Path(cell_path)
    manifest_path = cell / LEDGER_HEADS_REL
    expected = None
    if manifest_path.exists():
        expected = json.loads(manifest_path.read_text(encoding="utf-8"))
    ledgers: Dict[str, Any] = {}
    tampered: List[str] = []
    seen: set[str] = set()
    for path in _ledger_files(cell):
        rel = path.relative_to(cell).as_posix()
        seen.add(rel)
        chain = compute_ledger_chain(path)
        stored = (expected or {}).get("ledgers", {}).get(rel, {}) if expected else {}
        row_count_matches = stored.get("row_count") in (None, chain["row_count"])
        head_matches = stored.get("head_hash") in (None, chain["head_hash"])
        embedded_ok = all(row["embedded_matches"] for row in chain["rows"])
        ok = row_count_matches and head_matches and embedded_ok
        if not ok:
            tampered.append(rel)
        ledgers[rel] = {
            "row_count": chain["row_count"],
            "head_hash": chain["head_hash"],
            "stored_row_count": stored.get("row_count"),
            "stored_head_hash": stored.get("head_hash"),
            "row_count_matches": row_count_matches,
            "head_matches": head_matches,
            "embedded_chain_fields_match": embedded_ok,
            "missing": False,
            "ok": ok,
        }
    for rel, stored in sorted(((expected or {}).get("ledgers", {}) if expected else {}).items()):
        if rel not in seen:
            tampered.append(rel)
            ledgers[rel] = {
                "row_count": None,
                "head_hash": None,
                "stored_row_count": stored.get("row_count"),
                "stored_head_hash": stored.get("head_hash"),
                "row_count_matches": False,
                "head_matches": False,
                "embedded_chain_fields_match": False,
                "missing": True,
                "ok": False,
            }
    return {
        "status": "ok" if not tampered else "tampered",
        "valid": not tampered,
        "adopted": expected is not None,
        "tampered_ledgers": tampered,
        "ledgers": ledgers,
        "canonical_truth": "cell_ledgers",
    }
