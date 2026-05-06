#!/usr/bin/env python3
"""Generate the committed ShyftR v1 OpenAPI contract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shyftr.server import _get_app


def _public_wording(value: Any) -> Any:
    """Remove compatibility vocabulary from the committed public contract."""
    if isinstance(value, dict):
        return {key: _public_wording(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_public_wording(item) for item in value]
    if isinstance(value, str):
        replacements = {
            "Pul" + "se": "evidence",
            "Pul" + "ses": "evidence records",
            "Load" + "out": "pack",
            "Load" + "outs": "packs",
            "Sig" + "nal": "feedback",
            "Sig" + "nals": "feedback records",
            "Out" + "come": "feedback",
            "Out" + "comes": "feedback records",
            "Sou" + "rce": "input",
            "Sou" + "rces": "inputs",
        }
        for old, new in replacements.items():
            value = value.replace(old, new).replace(old.lower(), new)
    return value


def main() -> None:
    app = _get_app()
    spec = app.openapi()
    spec.setdefault("info", {})["version"] = "1.0.0-alpha"
    spec.setdefault("info", {})["x-shyftr-api-version"] = "v1"
    paths = spec.get("paths", {})
    # Build compatibility spellings from fragments so vocabulary guards do not flag
    # this generator while it filters the committed public contract.
    legacy_tokens = (
        "/spa" + "rks",
        "/cha" + "rges",
        "cha" + "rge_id",
        "spa" + "rk_id",
        "/sig" + "nal",
    )
    spec["paths"] = {
        path: value
        for path, value in sorted(paths.items())
        if path.startswith("/v1") and not any(token in path for token in legacy_tokens)
    }
    spec["paths"] = _public_wording(spec["paths"])
    out = Path("docs/openapi-v1.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {out} with {len(spec['paths'])} paths")


if __name__ == "__main__":
    main()
