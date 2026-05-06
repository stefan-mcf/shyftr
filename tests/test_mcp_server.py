from __future__ import annotations

import json
from pathlib import Path

from shyftr.layout import init_cell
from shyftr.mcp_server import (
    _handle_json_rpc_message,
    shyftr_pack_bridge,
    shyftr_profile_bridge,
    shyftr_record_feedback_bridge,
    shyftr_remember_bridge,
    shyftr_search_bridge,
    tool_names,
)
from shyftr.provider.memory import remember


def test_tool_names_are_stable() -> None:
    assert tool_names() == (
        "shyftr_search",
        "shyftr_pack",
        "shyftr_profile",
        "shyftr_remember",
        "shyftr_record_feedback",
    )


def test_search_and_profile_return_public_memory_ids(tmp_path: Path) -> None:
    cell = init_cell(tmp_path, "core", cell_type="user")
    remembered = remember(cell, "User prefers concise terminal updates.", "preference")

    search_result = shyftr_search_bridge({"cell_path": str(cell), "query": "concise updates"})
    assert search_result["status"] == "ok"
    assert search_result["results"][0]["memory_id"] == remembered.charge_id
    assert "charge_id" not in search_result["results"][0]

    profile_result = shyftr_profile_bridge({"cell_path": str(cell), "max_tokens": 100})
    assert profile_result["status"] == "ok"
    assert profile_result["source_memory_ids"] == [remembered.charge_id]


def test_pack_defaults_to_dry_run_without_retrieval_log(tmp_path: Path) -> None:
    cell = init_cell(tmp_path, "core", cell_type="user")
    remembered = remember(cell, "Use pytest before publishing Python changes.", "workflow")

    result = shyftr_pack_bridge(
        {"cell_path": str(cell), "query": "pytest publishing", "task_id": "task-1"}
    )

    assert result["status"] == "ok"
    assert result["write"] is False
    assert result["selected_memory_ids"] == [remembered.charge_id]
    assert result["items"][0]["memory_id"] == remembered.charge_id
    assert (cell / "ledger" / "retrieval_logs.jsonl").read_text(encoding="utf-8") == ""


def test_remember_requires_explicit_write(tmp_path: Path) -> None:
    cell = init_cell(tmp_path, "core", cell_type="user")

    preview = shyftr_remember_bridge(
        {"cell_path": str(cell), "statement": "User prefers local-first memory.", "kind": "preference"}
    )
    assert preview["status"] == "dry_run"
    assert not (cell / "traces" / "approved.jsonl").read_text(encoding="utf-8")

    committed = shyftr_remember_bridge(
        {
            "cell_path": str(cell),
            "statement": "User prefers local-first memory.",
            "kind": "preference",
            "write": True,
        }
    )
    assert committed["status"] == "approved"
    assert committed["memory_id"].startswith("trace-")


def test_feedback_requires_explicit_write(tmp_path: Path) -> None:
    cell = init_cell(tmp_path, "core", cell_type="user")
    preview = shyftr_record_feedback_bridge(
        {"cell_path": str(cell), "pack_id": "pack-1", "result": "success"}
    )
    assert preview["status"] == "dry_run"
    assert preview["write"] is False


def test_json_rpc_fallback_lists_and_calls_tools(tmp_path: Path) -> None:
    cell = init_cell(tmp_path, "core", cell_type="user")
    remember(cell, "User prefers concise terminal updates.", "preference")

    listed = _handle_json_rpc_message({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert listed is not None
    assert {tool["name"] for tool in listed["result"]["tools"]} == set(tool_names())

    called = _handle_json_rpc_message(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "shyftr_search",
                "arguments": {"cell_path": str(cell), "query": "concise"},
            },
        }
    )
    assert called is not None
    payload = json.loads(called["result"]["content"][0]["text"])
    assert payload["results"][0]["memory_id"].startswith("trace-")
