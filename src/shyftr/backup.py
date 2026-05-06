from __future__ import annotations

import json
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Union

from shyftr.ledger import file_sha256, read_jsonl

PathLike = Union[str, Path]

EXCLUDED_PARTS = {
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    "dist",
    ".DS_Store",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _cell_id(cell: Path) -> str:
    manifest = json.loads((cell / "config" / "cell_manifest.json").read_text(encoding="utf-8"))
    return str(manifest.get("cell_id") or cell.name)


def _iter_backup_files(cell: Path):
    for path in sorted(p for p in cell.rglob("*") if p.is_file()):
        rel = path.relative_to(cell)
        if any(part in EXCLUDED_PARTS for part in rel.parts):
            continue
        # Grid/indexes are rebuildable acceleration state; preserve metadata but
        # exclude transient DB/cache payloads by default.
        if rel.parts and rel.parts[0] in {"grid", "indexes"} and rel.suffix not in {".json", ".jsonl", ".md"}:
            continue
        yield path, rel


def build_backup_manifest(cell_path: PathLike) -> Dict[str, Any]:
    cell = Path(cell_path)
    files: List[Dict[str, Any]] = []
    ledgers: Dict[str, Dict[str, Any]] = {}
    for path, rel in _iter_backup_files(cell):
        rel_s = rel.as_posix()
        entry = {"path": rel_s, "sha256": file_sha256(path), "bytes": path.stat().st_size}
        files.append(entry)
        if rel_s.endswith(".jsonl"):
            count = 0
            if path.exists():
                count = sum(1 for _ in read_jsonl(path))
            ledgers[rel_s] = {"rows": count, "sha256": entry["sha256"], "bytes": entry["bytes"]}
    return {
        "format": "shyftr.cell_backup.v1",
        "cell_id": _cell_id(cell),
        "created_at": _now(),
        "canonical_truth": "cell_ledgers",
        "includes_ledgers": True,
        "includes_grid_payloads": False,
        "grid_rebuild_required": True,
        "schema_version": json.loads((cell / "config" / "cell_manifest.json").read_text(encoding="utf-8")).get("schema_version", 1),
        "files": files,
        "ledgers": ledgers,
    }


def backup_cell(cell_path: PathLike, output_path: PathLike) -> Dict[str, Any]:
    cell = Path(cell_path)
    out = Path(output_path)
    if out.is_dir():
        out = out / f"{_cell_id(cell)}-backup.tar.gz"
    out.parent.mkdir(parents=True, exist_ok=True)
    manifest = build_backup_manifest(cell)
    with tempfile.TemporaryDirectory() as td:
        manifest_path = Path(td) / "backup_manifest.json"
        manifest_path.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        with tarfile.open(out, "w:gz") as tar:
            for path, rel in _iter_backup_files(cell):
                tar.add(path, arcname=f"cell/{rel.as_posix()}")
            tar.add(manifest_path, arcname="backup_manifest.json")
    return {"status": "ok", "backup_path": str(out), "manifest": manifest}


def _safe_extract(tar: tarfile.TarFile, target: Path) -> None:
    root = target.resolve()
    for member in tar.getmembers():
        dest = (target / member.name).resolve()
        if root != dest and root not in dest.parents:
            raise ValueError(f"unsafe archive path: {member.name}")
    tar.extractall(target)


def restore_cell(backup_path: PathLike, target_path: PathLike, *, force: bool = False) -> Dict[str, Any]:
    backup = Path(backup_path)
    target = Path(target_path)
    if target.exists() and any(target.iterdir()) and not force:
        raise FileExistsError(f"restore target exists and is not empty: {target}")
    target.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        with tarfile.open(backup, "r:gz") as tar:
            _safe_extract(tar, tmp)
        manifest = json.loads((tmp / "backup_manifest.json").read_text(encoding="utf-8"))
        cell_root = tmp / "cell"
        for src in sorted(p for p in cell_root.rglob("*") if p.is_file()):
            rel = src.relative_to(cell_root)
            dest = target / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(src.read_bytes())
    validation = validate_restored_cell(target, manifest)
    return {"status": "ok", "cell_path": str(target), "manifest": manifest, "validation": validation}


def validate_restored_cell(cell_path: PathLike, manifest: Dict[str, Any]) -> Dict[str, Any]:
    cell = Path(cell_path)
    missing: List[str] = []
    mismatched: List[str] = []
    for entry in manifest.get("files", []):
        rel = str(entry.get("path"))
        path = cell / rel
        if not path.exists():
            missing.append(rel)
            continue
        if file_sha256(path) != entry.get("sha256"):
            mismatched.append(rel)
    return {
        "valid": not missing and not mismatched,
        "missing": missing,
        "mismatched": mismatched,
        "ledger_counts": {
            rel: sum(1 for _ in read_jsonl(cell / rel)) if (cell / rel).exists() else 0
            for rel in sorted(manifest.get("ledgers", {}))
        },
        "grid_rebuild_required": bool(manifest.get("grid_rebuild_required", True)),
    }
