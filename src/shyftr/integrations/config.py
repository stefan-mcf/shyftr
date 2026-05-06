"""Runtime adapter configuration schema and validation.

Defines the declarative config model for runtime adapters, allowing
runtimes to attach through configuration rather than custom code
for every source.

Supports:
- Input definitions: file, glob, JSONL, directory
- Path validation (stay within allowed roots)
- Required source kind mapping validation
- Stable external ID mapping rule validation
- CLI-ready config loading helpers (JSON / optional YAML)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Sequence

from shyftr.integrations import IntegrationAdapterError

# ── Constants ─────────────────────────────────────────────────────────────────

ALLOWED_INPUT_KINDS: Sequence[str] = ("file", "glob", "jsonl", "directory")

VALID_SOURCE_KINDS: Sequence[str] = (
    "closeout",
    "log",
    "artifact",
    "message",
    "note",
    "review",
    "feedback",
    "outcome",
    "task",
    "report",
    "config",
)

# Supported stable external ID field names in identity mappings
VALID_EXTERNAL_ID_FIELDS: Sequence[str] = (
    "external_system",
    "external_scope",
    "external_run_id",
    "external_task_id",
    "external_trace_id",
    "external_session_id",
)

# Ingest option keys that are recognised
VALID_INGEST_OPTIONS: Sequence[str] = (
    "deduplicate",
    "dry_run",
    "max_sources",
    "include_hidden",
    "recursive",
    "allowed_roots",
)


# ── Exceptions ────────────────────────────────────────────────────────────────


class ConfigValidationError(IntegrationAdapterError):
    """Raised when an adapter configuration is invalid."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)


# ── Models ────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class InputDefinition:
    """A single input source definition within an adapter config.

    Fields:
        kind: Input source kind — "file", "glob", "jsonl", or "directory".
        path: Path or glob pattern for the input source.
        source_kind: Kind label assigned to discovered sources
            (e.g. "closeout", "log", "artifact").
        identity_mapping: Per-input overrides for the default identity
            mapping. Maps external ID field names to source metadata keys.
    """

    kind: str
    path: str
    source_kind: str
    identity_mapping: Dict[str, str] = field(default_factory=dict)

    _required_fields: ClassVar[Sequence[str]] = ("kind", "path", "source_kind")


@dataclass(frozen=True)
class RuntimeAdapterConfig:
    """Declarative configuration for a runtime integration adapter.

    Fields:
        adapter_id: Unique identifier for this adapter instance.
        cell_id: Target ShyftR Cell for ingested sources.
        external_system: Name of the external runtime system.
        external_scope: Scope or namespace within the external system.
        source_root: Base directory for resolving relative input paths.
        inputs: List of InputDefinition describing source discovery.
        identity_mapping: Default identity mapping for all inputs.
            Maps external ID field names to source metadata keys.
        ingest_options: Additional ingestion behaviour flags.
            Supported keys: deduplicate, dry_run, max_sources,
            include_hidden, recursive, allowed_roots.
    """

    adapter_id: str
    cell_id: str
    external_system: str
    external_scope: str
    source_root: str
    inputs: List[InputDefinition]
    identity_mapping: Dict[str, str] = field(default_factory=dict)
    ingest_options: Dict[str, Any] = field(default_factory=dict)

    _required_fields: ClassVar[Sequence[str]] = (
        "adapter_id",
        "cell_id",
        "external_system",
        "external_scope",
        "source_root",
        "inputs",
    )


# ── Public API ────────────────────────────────────────────────────────────────


def load_config(path: str) -> RuntimeAdapterConfig:
    """Load and validate a RuntimeAdapterConfig from a JSON or YAML file.

    Supports .json files directly via stdlib. For .yaml / .yml files,
    attempts to import PyYAML; raises a clear error if unavailable.

    Args:
        path: File path to the config.

    Returns:
        A validated RuntimeAdapterConfig instance.

    Raises:
        ConfigValidationError: If the config content is invalid.
        FileNotFoundError: If the file does not exist.
    """
    path_obj = Path(path)
    raw = _read_config_file(path_obj)
    return _parse_config(raw)


def validate_config(config: RuntimeAdapterConfig) -> None:
    """Validate a RuntimeAdapterConfig in place.

    Checks:
        - Required fields are present after parsing.
        - Input definitions have valid kinds and non-empty source_kind.
        - Identity mappings reference known external ID fields.
        - Ingest options reference known keys.
        - Paths stay within allowed roots (source_root is implicitly
          allowed).

    Args:
        config: The config to validate.

    Raises:
        ConfigValidationError: If validation fails.
    """
    errors: List[str] = []

    # --- input kind validation ---
    for idx, inp in enumerate(config.inputs):
        if inp.kind not in ALLOWED_INPUT_KINDS:
            errors.append(
                f"inputs[{idx}].kind: '{inp.kind}' is invalid. "
                f"Must be one of: {', '.join(ALLOWED_INPUT_KINDS)}"
            )
        if not inp.source_kind or not inp.source_kind.strip():
            errors.append(f"inputs[{idx}].source_kind must be a non-empty string")

    # --- source kind mapping validation ---
    _validate_source_kind_mappings(config, errors)

    # --- identity mapping validation ---
    _validate_identity_mappings(config, errors)

    # --- ingest options validation ---
    _validate_ingest_options(config, errors)

    # --- path validation ---
    _validate_paths(config, errors)

    if errors:
        raise ConfigValidationError(
            "Adapter config validation failed",
            details={"errors": errors},
        )


# ── Internal helpers ──────────────────────────────────────────────────────────


def _read_config_file(path: Path) -> Dict[str, Any]:
    """Read a config file, supporting JSON and YAML formats."""
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    suffix = path.suffix.lower()

    if suffix in (".yaml", ".yml"):
        try:
            import yaml  # type: ignore[import-untyped]
        except ImportError:
            raise ConfigValidationError(
                "YAML config files require PyYAML. "
                "Install it with: pip install PyYAML",
                details={"path": str(path), "suffix": suffix},
            )
        with open(path, "r") as f:
            raw = yaml.safe_load(f)
    elif suffix == ".json":
        import json

        with open(path, "r") as f:
            raw = json.load(f)
    else:
        import json

        with open(path, "r") as f:
            text = f.read()
        try:
            raw = json.loads(text)
        except json.JSONDecodeError:
            try:
                import yaml  # type: ignore[import-untyped]
            except ImportError:
                raise ConfigValidationError(
                    f"Cannot parse {path}: unknown format and PyYAML not available"
                )
            raw = yaml.safe_load(text)

    if not isinstance(raw, dict):
        raise ConfigValidationError(
            "Config file must contain a mapping (dictionary)"
        )

    return raw


def _parse_config(raw: Dict[str, Any]) -> RuntimeAdapterConfig:
    """Parse a validated dict into a RuntimeAdapterConfig."""
    required = {
        "adapter_id",
        "cell_id",
        "external_system",
        "external_scope",
        "source_root",
    }
    missing = required - set(raw)
    if missing:
        raise ConfigValidationError(
            f"Missing required config fields: {', '.join(sorted(missing))}"
        )

    inputs_raw = raw.get("inputs", [])
    if not isinstance(inputs_raw, list):
        raise ConfigValidationError("'inputs' must be a list")
    if not inputs_raw:
        raise ConfigValidationError("At least one input definition is required")

    inputs = [_parse_input(idx, item) for idx, item in enumerate(inputs_raw)]

    config = RuntimeAdapterConfig(
        adapter_id=raw["adapter_id"],
        cell_id=raw["cell_id"],
        external_system=raw["external_system"],
        external_scope=raw["external_scope"],
        source_root=raw["source_root"],
        inputs=inputs,
        identity_mapping=raw.get("identity_mapping", {}),
        ingest_options=raw.get("ingest_options", {}),
    )

    validate_config(config)
    return config


def _parse_input(idx: int, item: Any) -> InputDefinition:
    """Parse a single InputDefinition from a raw dict."""
    if not isinstance(item, dict):
        raise ConfigValidationError(f"inputs[{idx}] must be a mapping")

    missing = [k for k in ("kind", "path", "source_kind") if k not in item]
    if missing:
        raise ConfigValidationError(
            f"inputs[{idx}] missing required fields: {', '.join(missing)}"
        )

    return InputDefinition(
        kind=item["kind"],
        path=item["path"],
        source_kind=item["source_kind"],
        identity_mapping=item.get("identity_mapping", {}),
    )


def _validate_source_kind_mappings(
    config: RuntimeAdapterConfig,
    errors: List[str],
) -> None:
    """Validate that every input has a recognised source_kind."""
    for idx, inp in enumerate(config.inputs):
        if inp.source_kind not in VALID_SOURCE_KINDS:
            errors.append(
                f"inputs[{idx}].source_kind: '{inp.source_kind}' is unrecognised. "
                f"Known kinds: {', '.join(VALID_SOURCE_KINDS)}"
            )


def _validate_identity_mappings(
    config: RuntimeAdapterConfig,
    errors: List[str],
) -> None:
    """Validate identity mapping keys are known external ID fields."""

    def check_one(source: str, mapping: Dict[str, str]) -> None:
        for key in mapping:
            if key not in VALID_EXTERNAL_ID_FIELDS:
                errors.append(
                    f"{source}: identity mapping key '{key}' is unrecognised. "
                    f"Known fields: {', '.join(VALID_EXTERNAL_ID_FIELDS)}"
                )

    check_one("identity_mapping", config.identity_mapping)
    for idx, inp in enumerate(config.inputs):
        if inp.identity_mapping:
            check_one(f"inputs[{idx}].identity_mapping", inp.identity_mapping)


def _validate_ingest_options(
    config: RuntimeAdapterConfig,
    errors: List[str],
) -> None:
    """Validate ingest option keys are recognised."""
    for key in config.ingest_options:
        if key not in VALID_INGEST_OPTIONS:
            errors.append(
                f"ingest_options: unknown key '{key}'. "
                f"Supported keys: {', '.join(VALID_INGEST_OPTIONS)}"
            )


def _validate_paths(
    config: RuntimeAdapterConfig,
    errors: List[str],
) -> None:
    """Validate that input paths stay within allowed roots.

    Relative paths resolve under source_root and are implicitly allowed.
    Absolute paths must be under source_root or an explicitly listed
    allowed_root (from ingest_options).
    """
    source_root = Path(config.source_root)
    configured_allowed_roots: List[Any] = config.ingest_options.get("allowed_roots", [])
    allowed_roots = [source_root] + [Path(r) for r in configured_allowed_roots]

    for idx, inp in enumerate(config.inputs):
        path = Path(inp.path)
        if not path.is_absolute():
            continue  # Relative resolves under source_root, implicitly safe

        resolved = path.resolve()
        allowed = any(
            _is_under(resolved, root.resolve())
            for root in allowed_roots
        )
        if not allowed:
            errors.append(
                f"inputs[{idx}].path: absolute path '{inp.path}' is outside "
                f"allowed roots (source_root='{config.source_root}'"
                + (f", allowed_roots={config.ingest_options.get('allowed_roots', [])})" if config.ingest_options.get("allowed_roots") else ")")
            )


def _is_under(child: Path, parent: Path) -> bool:
    """Return True if *child* is *parent* or a descendant of *parent*."""
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


# ── Module exports ────────────────────────────────────────────────────────────

__all__ = [
    "ALLOWED_INPUT_KINDS",
    "ConfigValidationError",
    "InputDefinition",
    "RuntimeAdapterConfig",
    "VALID_EXTERNAL_ID_FIELDS",
    "VALID_INGEST_OPTIONS",
    "VALID_SOURCE_KINDS",
    "load_config",
    "validate_config",
]
