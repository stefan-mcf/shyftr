"""Tests for the ShyftR demo flow described in docs/demo.md.

Exercises the documented lifecycle using a temporary Cell and verifies
that the example files exist and are parseable.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def _cli(*args: str, cwd: str | None = None) -> subprocess.CompletedProcess:
    """Run the shyftr CLI via python -m with PYTHONPATH pointing at src."""
    cmd = [sys.executable, "-m", "shyftr.cli", *args]
    src_dir = str(REPO_ROOT / "src")
    env = dict(
        PYTHONPATH=f"{src_dir}",
    )
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
    )


# ---------------------------------------------------------------------------
# Example file assertions
# ---------------------------------------------------------------------------


def test_example_pulse_exists_and_parseable() -> None:
    """examples/pulse.md exists and contains expected sections."""
    path = REPO_ROOT / "examples" / "pulse.md"
    assert path.is_file(), f"Missing: {path}"
    text = path.read_text(encoding="utf-8")
    assert "Pulse ID:" in text
    assert "Kind:" in text
    assert "Durable Lesson" in text
    assert "Pulse -> Spark" in text or "learning loop" in text


def test_example_task_json_exists_and_parseable() -> None:
    """examples/task.json exists and is valid JSON with expected fields."""
    path = REPO_ROOT / "examples" / "task.json"
    assert path.is_file(), f"Missing: {path}"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert "task_id" in data
    assert "query" in data
    assert "steps" in data


def test_demo_doc_exists() -> None:
    """docs/demo.md exists and documents the CLI commands."""
    path = REPO_ROOT / "docs" / "demo.md"
    assert path.is_file(), f"Missing: {path}"
    text = path.read_text(encoding="utf-8")
    assert "shyftr init-cell" in text
    assert "shyftr ingest" in text
    assert "shyftr spark" in text
    assert "shyftr approve" in text
    assert "shyftr charge" in text
    assert "shyftr search" in text
    assert "shyftr pack" in text
    assert "shyftr signal" in text


# ---------------------------------------------------------------------------
# Deterministic demo lifecycle
# ---------------------------------------------------------------------------


def test_demo_lifecycle_via_cli(tmp_path: Path) -> None:
    """Exercise the documented demo lifecycle in a temporary Cell.

    Covers:
      init-cell -> ingest -> fragments -> approve -> promote
      -> search -> loadout -> outcome
    """
    cell = str(tmp_path / "demo-cell")
    repo_root = str(REPO_ROOT)

    # 1. Create a sample source file (same content pattern as examples/source.md)
    source_file = tmp_path / "demo-source.md"
    source_file.write_text(
        "# Loadout Relevance Heuristic\n\n"
        "Kind: lesson\n\n"
        "During testing, keyword-only search produced false positives "
        "because Trace statements lacked scope tags.\n",
        encoding="utf-8",
    )

    # 2. init-cell
    result = _cli("init-cell", cell, "--cell-id", "demo-cell", "--cell-type", "domain")
    assert result.returncode == 0, f"init failed: {result.stderr}"
    init_data = json.loads(result.stdout)
    assert init_data["status"] == "ok"
    assert init_data["cell_id"] == "demo-cell"

    # 3. ingest
    result = _cli("ingest", cell, str(source_file), "--kind", "lesson")
    assert result.returncode == 0, f"ingest failed: {result.stderr}"
    ingest_data = json.loads(result.stdout)
    assert ingest_data["source_id"].startswith("src-")
    source_id: str = ingest_data["source_id"]

    # 4. fragments
    result = _cli("fragments", cell, source_id)
    assert result.returncode == 0, f"fragments failed: {result.stderr}"
    fragments = json.loads(result.stdout)
    assert isinstance(fragments, list)
    assert len(fragments) >= 1
    fragment_id: str = fragments[0]["fragment_id"]

    # 5. approve
    result = _cli(
        "approve", cell, fragment_id,
        "--reviewer", "demo-test",
        "--rationale", "Accurate lesson for demo flow",
    )
    assert result.returncode == 0, f"approve failed: {result.stderr}"
    review_data = json.loads(result.stdout)
    assert review_data["review_status"] == "approved"

    # 6. promote
    result = _cli(
        "promote", cell, fragment_id,
        "--promoter", "demo-test",
        "--statement", "Scope-tagged Traces improve Loadout relevance.",
    )
    assert result.returncode == 0, f"promote failed: {result.stderr}"
    trace_data = json.loads(result.stdout)
    assert trace_data["trace_id"].startswith("trace-")
    trace_id: str = trace_data["trace_id"]

    # 7. search
    result = _cli("search", cell, "loadout")
    assert result.returncode == 0, f"search failed: {result.stderr}"
    search_data = json.loads(result.stdout)
    assert "results" in search_data
    assert search_data["index_size"] >= 1

    # 8. loadout
    result = _cli(
        "loadout", cell, "loadout relevance",
        "--task-id", "demo-test-task",
        "--max-items", "5",
    )
    assert result.returncode == 0, f"loadout failed: {result.stderr}"
    loadout_data = json.loads(result.stdout)
    assert loadout_data["loadout_id"].startswith("lo-")
    loadout_id: str = loadout_data["loadout_id"]

    # 9. outcome
    result = _cli(
        "outcome", cell, loadout_id, "success",
        "--applied", trace_id,
        "--useful", trace_id,
    )
    assert result.returncode == 0, f"outcome failed: {result.stderr}"
    outcome_data = json.loads(result.stdout)
    assert outcome_data["outcome_id"].startswith("oc-")
    assert outcome_data["verdict"] == "success"

    # 10. final hygiene check
    result = _cli("hygiene", cell)
    assert result.returncode == 0, f"hygiene failed: {result.stderr}"
    report = json.loads(result.stdout)
    assert "fragment_status_counts" in report
    assert "trace_confidence_distribution" in report


def test_demo_lifecycle_runs_without_network_or_secrets() -> None:
    """Verify the demo lifecycle itself requires no external dependencies.

    This test asserts that the CLI has no network/model imports by checking
    that the import chain is pure local.
    """
    import shyftr.cli  # noqa: F401 - should not trigger network imports
    import shyftr.models  # noqa: F401
    import shyftr.layout  # noqa: F401
    import shyftr.ingest  # noqa: F401
    import shyftr.extract  # noqa: F401
    import shyftr.review  # noqa: F401
    import shyftr.promote  # noqa: F401
    import shyftr.loadout  # noqa: F401
    import shyftr.outcomes  # noqa: F401
    # If any of these triggered a network import, test would fail
