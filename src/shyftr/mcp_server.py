"""MCP bridge for ShyftR.

The bridge keeps ShyftR's ledger-first safety model intact. Read/pack tools
prefer dry-run behavior, while memory and feedback writes require an explicit
``write=True`` flag.
"""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, TextIO

from shyftr.pack import LoadoutTaskInput, assemble_loadout
from shyftr.provider.memory import profile, record_signal, remember, search

TOOL_NAMES = (
    "shyftr_search",
    "shyftr_pack",
    "shyftr_profile",
    "shyftr_remember",
    "shyftr_record_feedback",
)

JsonArgs = str | bytes | bytearray | Mapping[str, Any]


def shyftr_search_bridge(args: JsonArgs) -> dict[str, Any]:
    payload = _load_payload(args)
    cell_path = _require_cell_path(payload)
    query = _require_text(payload.get("query"), "query")
    items = search(
        cell_path,
        query,
        top_k=_bounded_int(payload.get("limit", 10), "limit", minimum=1, maximum=50),
        trust_tiers=_optional_str_list(payload.get("trust_tiers")),
        kinds=_optional_str_list(payload.get("kinds")),
    )
    return {
        "tool": "shyftr_search",
        "status": "ok",
        "cell_path": str(cell_path),
        "query": query,
        "results": [_search_result_to_public(item) for item in items],
    }


def shyftr_pack_bridge(args: JsonArgs) -> dict[str, Any]:
    payload = _load_payload(args)
    cell_path = _require_cell_path(payload)
    query = _require_text(payload.get("query"), "query")
    task_id = _require_text(payload.get("task_id"), "task_id")
    write = bool(payload.get("write", False))
    runtime_id = str(payload.get("runtime_id") or "mcp")
    task = LoadoutTaskInput(
        cell_path=str(cell_path),
        query=query,
        task_id=task_id,
        runtime_id=runtime_id,
        max_items=_bounded_int(payload.get("max_items", 10), "max_items", minimum=0, maximum=50),
        max_tokens=_bounded_int(payload.get("max_tokens", 2000), "max_tokens", minimum=1, maximum=12000),
        dry_run=not write,
        include_fragments=bool(payload.get("include_candidates", False)),
        requested_trust_tiers=_optional_str_list(payload.get("trust_tiers")),
        query_kind=_optional_text(payload.get("kind")),
        query_tags=_optional_str_list(payload.get("tags")),
        retrieval_mode=str(payload.get("retrieval_mode") or "balanced"),
    )
    assembled = assemble_loadout(task)
    result = assembled.to_dict()
    return {
        "tool": "shyftr_pack",
        "status": "ok",
        "write": write,
        "cell_path": str(cell_path),
        "pack_id": result.get("loadout_id"),
        "task_id": result.get("task_id"),
        "total_items": result.get("total_items"),
        "total_tokens": result.get("total_tokens"),
        "selected_memory_ids": list(result.get("retrieval_log", {}).get("selected_ids", [])),
        "items": [_memory_item_to_public(item) for item in result.get("items", [])],
        "retrieval": _retrieval_to_public(result.get("retrieval_log", {})),
    }


def shyftr_profile_bridge(args: JsonArgs) -> dict[str, Any]:
    payload = _load_payload(args)
    cell_path = _require_cell_path(payload)
    projected = profile(
        cell_path,
        max_tokens=_bounded_int(payload.get("max_tokens", 2000), "max_tokens", minimum=1, maximum=12000),
    )
    return {
        "tool": "shyftr_profile",
        "status": "ok",
        "cell_path": str(cell_path),
        "projection_id": projected.projection_id,
        "source_memory_ids": list(projected.source_charge_ids),
        "entry_count": len(projected.source_charge_ids),
        "markdown": projected.markdown,
        "compact_markdown": projected.compact_markdown,
    }


def shyftr_remember_bridge(args: JsonArgs) -> dict[str, Any]:
    payload = _load_payload(args)
    cell_path = _require_cell_path(payload)
    statement = _require_text(payload.get("statement"), "statement")
    kind = _require_text(payload.get("kind"), "kind")
    write = bool(payload.get("write", False))
    metadata = _optional_mapping(payload.get("metadata"))
    actor = _optional_text(payload.get("actor"))
    if actor:
        metadata = dict(metadata or {})
        metadata.setdefault("actor", actor)
    if not write:
        return {
            "tool": "shyftr_remember",
            "status": "dry_run",
            "write": False,
            "cell_path": str(cell_path),
            "kind": kind,
            "statement_preview": statement[:240],
            "message": "No memory was written. Re-run with write=true to commit after reviewing the statement.",
        }
    result = remember(cell_path, statement, kind, metadata=metadata)
    return {
        "tool": "shyftr_remember",
        "status": result.status,
        "write": True,
        "cell_path": str(cell_path),
        "memory_id": result.charge_id,
        "source_id": result.pulse_id,
        "candidate_id": result.spark_id,
        "trust_tier": result.trust_tier,
    }


def shyftr_record_feedback_bridge(args: JsonArgs) -> dict[str, Any]:
    payload = _load_payload(args)
    cell_path = _require_cell_path(payload)
    pack_id = _require_text(payload.get("pack_id"), "pack_id")
    result = _require_text(payload.get("result"), "result")
    write = bool(payload.get("write", False))
    if not write:
        return {
            "tool": "shyftr_record_feedback",
            "status": "dry_run",
            "write": False,
            "cell_path": str(cell_path),
            "pack_id": pack_id,
            "result": result,
            "message": "No feedback was written. Re-run with write=true to commit after reviewing the payload.",
        }
    payload_result = record_signal(
        cell_path,
        pack_id,
        result=result,
        applied_charge_ids=_optional_str_list(payload.get("applied_memory_ids")),
        useful_charge_ids=_optional_str_list(payload.get("useful_memory_ids")),
        harmful_charge_ids=_optional_str_list(payload.get("harmful_memory_ids")),
        ignored_charge_ids=_optional_str_list(payload.get("ignored_memory_ids")),
        missing_memory_notes=_optional_str_list(payload.get("missing_memory_notes")),
        runtime_id=str(payload.get("runtime_id") or "mcp"),
        task_id=_optional_text(payload.get("task_id")),
    )
    return {
        "tool": "shyftr_record_feedback",
        "status": payload_result.get("status", "ok"),
        "write": True,
        "cell_path": str(cell_path),
        "feedback": _json_safe(payload_result),
    }


def create_mcp_server() -> Any:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:  # pragma: no cover - optional runtime dependency
        raise RuntimeError("ShyftR MCP bridge requires optional package 'mcp'.") from exc

    server = FastMCP("shyftr")

    @server.tool(name="shyftr_search")
    def shyftr_search_tool(
        cell_path: str,
        query: str,
        limit: int = 10,
        trust_tiers: list[str] | None = None,
        kinds: list[str] | None = None,
    ) -> dict[str, Any]:
        return shyftr_search_bridge(
            {"cell_path": cell_path, "query": query, "limit": limit, "trust_tiers": trust_tiers, "kinds": kinds}
        )

    @server.tool(name="shyftr_pack")
    def shyftr_pack_tool(
        cell_path: str,
        query: str,
        task_id: str,
        runtime_id: str = "mcp",
        max_items: int = 10,
        max_tokens: int = 2000,
        write: bool = False,
    ) -> dict[str, Any]:
        return shyftr_pack_bridge(
            {
                "cell_path": cell_path,
                "query": query,
                "task_id": task_id,
                "runtime_id": runtime_id,
                "max_items": max_items,
                "max_tokens": max_tokens,
                "write": write,
            }
        )

    @server.tool(name="shyftr_profile")
    def shyftr_profile_tool(cell_path: str, max_tokens: int = 2000) -> dict[str, Any]:
        return shyftr_profile_bridge({"cell_path": cell_path, "max_tokens": max_tokens})

    @server.tool(name="shyftr_remember")
    def shyftr_remember_tool(
        cell_path: str,
        statement: str,
        kind: str,
        actor: str | None = None,
        write: bool = False,
    ) -> dict[str, Any]:
        return shyftr_remember_bridge(
            {"cell_path": cell_path, "statement": statement, "kind": kind, "actor": actor, "write": write}
        )

    @server.tool(name="shyftr_record_feedback")
    def shyftr_record_feedback_tool(
        cell_path: str,
        pack_id: str,
        result: str,
        runtime_id: str = "mcp",
        task_id: str | None = None,
        applied_memory_ids: list[str] | None = None,
        useful_memory_ids: list[str] | None = None,
        harmful_memory_ids: list[str] | None = None,
        ignored_memory_ids: list[str] | None = None,
        missing_memory_notes: list[str] | None = None,
        write: bool = False,
    ) -> dict[str, Any]:
        return shyftr_record_feedback_bridge(
            {
                "cell_path": cell_path,
                "pack_id": pack_id,
                "result": result,
                "runtime_id": runtime_id,
                "task_id": task_id,
                "applied_memory_ids": applied_memory_ids,
                "useful_memory_ids": useful_memory_ids,
                "harmful_memory_ids": harmful_memory_ids,
                "ignored_memory_ids": ignored_memory_ids,
                "missing_memory_notes": missing_memory_notes,
                "write": write,
            }
        )

    return server


def tool_names() -> tuple[str, ...]:
    return TOOL_NAMES


def main() -> None:
    if os.getenv("SHYFTR_FORCE_STDIO_FALLBACK") == "1":
        _run_json_rpc_stdio(sys.stdin, sys.stdout)
        return
    try:
        server = create_mcp_server()
    except RuntimeError:
        _run_json_rpc_stdio(sys.stdin, sys.stdout)
        return
    server.run()


def _load_payload(args: JsonArgs) -> dict[str, Any]:
    if isinstance(args, Mapping):
        return dict(args)
    if isinstance(args, str | bytes | bytearray):
        decoded = json.loads(args)
        if not isinstance(decoded, dict):
            raise ValueError("args must decode to a JSON object")
        return decoded
    raise TypeError("args must be a JSON object string or mapping")


def _require_cell_path(payload: Mapping[str, Any]) -> Path:
    raw = _require_text(payload.get("cell_path"), "cell_path")
    path = Path(raw).expanduser()
    manifest = path / "config" / "cell_manifest.json"
    if not manifest.exists():
        raise ValueError(f"cell_path is not a ShyftR cell: {path}")
    return path


def _require_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required")
    return " ".join(value.split())


def _optional_text(value: Any) -> str | None:
    if value is None or value == "":
        return None
    return _require_text(value, "value")


def _optional_str_list(value: Any) -> list[str] | None:
    if value is None or value == "":
        return None
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, Sequence) and not isinstance(value, bytes | bytearray):
        return [str(item) for item in value if str(item).strip()]
    raise ValueError("expected a list of strings")


def _optional_mapping(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ValueError("metadata must be an object")
    return dict(value)


def _bounded_int(value: Any, field_name: str, *, minimum: int, maximum: int) -> int:
    parsed = int(value)
    if parsed < minimum or parsed > maximum:
        raise ValueError(f"{field_name} must be between {minimum} and {maximum}")
    return parsed


def _search_result_to_public(item: Any) -> dict[str, Any]:
    return {
        "memory_id": item.charge_id,
        "statement": item.statement,
        "trust_tier": item.trust_tier,
        "kind": item.kind,
        "confidence": item.confidence,
        "score": item.score,
        "lifecycle_status": item.lifecycle_status,
        "selection_rationale": item.selection_rationale,
        "provenance": _json_safe(item.provenance),
    }


def _memory_item_to_public(item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "memory_id": item.get("item_id"),
        "trust_tier": item.get("trust_tier"),
        "statement": item.get("statement"),
        "rationale": item.get("rationale"),
        "tags": item.get("tags", []),
        "kind": item.get("kind"),
        "confidence": item.get("confidence"),
        "score": item.get("score"),
        "pack_role": item.get("loadout_role"),
        "graph_context": item.get("graph_context", []),
    }


def _retrieval_to_public(log: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "retrieval_id": log.get("retrieval_id"),
        "pack_id": log.get("loadout_id"),
        "selected_memory_ids": log.get("selected_ids", []),
        "candidate_memory_ids": log.get("candidate_ids", []),
        "caution_memory_ids": log.get("caution_ids", []),
        "suppressed_memory_ids": log.get("suppressed_ids", []),
        "query": log.get("query"),
        "generated_at": log.get("generated_at"),
    }


def _json_safe(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str))


def _run_json_rpc_stdio(stdin: TextIO, stdout: TextIO) -> None:
    for line in stdin:
        if not line.strip():
            continue
        response = _handle_json_rpc_message(json.loads(line))
        if response is not None:
            stdout.write(json.dumps(response, sort_keys=True) + "\n")
            stdout.flush()


def _handle_json_rpc_message(message: dict[str, Any]) -> dict[str, Any] | None:
    request_id = message.get("id")
    method = message.get("method")
    try:
        if method == "initialize":
            return _json_rpc_result(
                request_id,
                {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {"name": "shyftr", "version": "0.0.0"},
                    "capabilities": {"tools": {}},
                },
            )
        if method == "notifications/initialized":
            return None
        if method == "tools/list":
            return _json_rpc_result(request_id, {"tools": _tool_descriptors()})
        if method == "tools/call":
            params = message.get("params") or {}
            name = params.get("name")
            arguments = params.get("arguments") or {}
            call_map = {
                "shyftr_search": shyftr_search_bridge,
                "shyftr_pack": shyftr_pack_bridge,
                "shyftr_profile": shyftr_profile_bridge,
                "shyftr_remember": shyftr_remember_bridge,
                "shyftr_record_feedback": shyftr_record_feedback_bridge,
            }
            if name not in call_map:
                raise ValueError(f"unknown tool: {name}")
            payload = call_map[name](arguments)
            return _json_rpc_result(
                request_id,
                {"content": [{"type": "text", "text": json.dumps(payload, sort_keys=True)}], "isError": False},
            )
        raise ValueError(f"unsupported method: {method}")
    except Exception as exc:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32000, "message": str(exc)}}


def _json_rpc_result(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _tool_descriptors() -> list[dict[str, Any]]:
    return [
        _tool_descriptor("shyftr_search", "Search reviewed ShyftR memory.", ["cell_path", "query"]),
        _tool_descriptor("shyftr_pack", "Build a bounded ShyftR pack; dry-run unless write=true.", ["cell_path", "query", "task_id"]),
        _tool_descriptor("shyftr_profile", "Build a compact profile projection from reviewed memory.", ["cell_path"]),
        _tool_descriptor("shyftr_remember", "Preview or write explicit memory through ShyftR policy.", ["cell_path", "statement", "kind"]),
        _tool_descriptor("shyftr_record_feedback", "Preview or record ShyftR pack feedback.", ["cell_path", "pack_id", "result"]),
    ]


def _tool_descriptor(name: str, description: str, required: list[str]) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "inputSchema": {"type": "object", "properties": {}, "required": required},
    }


if __name__ == "__main__":  # pragma: no cover
    main()
