"""Synthetic public-safe evaluation task generator."""
from .evolution import evolution_eval_tasks
from .frontier import export_eval_tasks as _frontier_export_eval_tasks, generate_eval_tasks as _frontier_generate_eval_tasks


def generate_eval_tasks(cell_path=None):
    tasks = list(_frontier_generate_eval_tasks(cell_path))
    tasks.extend(evolution_eval_tasks())
    return sorted(tasks, key=lambda item: str(item.get("task_id") or ""))


def export_eval_tasks(cell_path, output_path=None, jsonl=False):
    from pathlib import Path
    import json

    tasks = generate_eval_tasks(cell_path)
    payload = {"status": "ok", "tasks": tasks, "total": len(tasks), "public_safe": True}
    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if jsonl:
            path.write_text("".join(json.dumps(task, sort_keys=True) + "\n" for task in tasks), encoding="utf-8")
        else:
            path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        payload["output_path"] = str(path)
    return payload


__all__ = ["export_eval_tasks", "generate_eval_tasks"]
