"""Plugin discovery for optional ShyftR runtime adapters.

ShyftR ships built-in adapter metadata for the file/JSONL adapter and can also
list third-party adapters exposed through the ``shyftr.adapters`` Python entry
point group. Discovery is introspection-only: listing plugins does not ingest
Pulses, mutate Cell ledgers, or edit external runtime configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib import metadata as importlib_metadata
from typing import Any, Callable, Iterable, List, Optional, Sequence

ADAPTER_ENTRY_POINT_GROUP = "shyftr.adapters"
CONFIG_SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True)
class AdapterPluginMeta:
    """Serializable metadata describing a runtime adapter plugin."""

    name: str
    version: str
    supported_input_kinds: Sequence[str]
    config_schema_version: str = CONFIG_SCHEMA_VERSION
    description: str = ""
    entry_point_group: str = ADAPTER_ENTRY_POINT_GROUP
    adapter_class: Optional[str] = None
    builtin: bool = False

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("adapter plugin name is required")
        if not self.version:
            raise ValueError("adapter plugin version is required")
        if not self.config_schema_version:
            raise ValueError("config_schema_version is required")
        object.__setattr__(self, "supported_input_kinds", tuple(str(v) for v in self.supported_input_kinds))

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": self.name,
            "version": self.version,
            "supported_input_kinds": list(self.supported_input_kinds),
            "config_schema_version": self.config_schema_version,
            "description": self.description,
            "entry_point_group": self.entry_point_group,
            "builtin": self.builtin,
        }
        if self.adapter_class:
            payload["adapter_class"] = self.adapter_class
        return payload


EntryPointProvider = Callable[..., Iterable[Any]]


def builtin_file_adapter() -> AdapterPluginMeta:
    """Return metadata for ShyftR's built-in file/JSONL adapter."""

    return AdapterPluginMeta(
        name="file",
        version="0.0.0",
        description="Built-in file, glob, JSONL, and directory-tree Pulse adapter.",
        supported_input_kinds=("file", "glob", "jsonl", "directory"),
        config_schema_version=CONFIG_SCHEMA_VERSION,
        entry_point_group="builtin",
        adapter_class="shyftr.integrations.file_adapter.FileSourceAdapter",
        builtin=True,
    )


def builtin_adapters() -> list[AdapterPluginMeta]:
    """Return built-in adapters that are available without optional plugins."""

    return [builtin_file_adapter()]


def _select_entry_points(entry_points: Any, group: str) -> list[Any]:
    """Return entry points for ``group`` across importlib.metadata APIs."""

    if hasattr(entry_points, "select"):
        return list(entry_points.select(group=group))
    if isinstance(entry_points, dict):
        return list(entry_points.get(group, ()))
    return [ep for ep in entry_points if getattr(ep, "group", None) == group]


def _metadata_from_loaded(name: str, loaded: Any) -> list[AdapterPluginMeta]:
    """Normalize an entry-point load result into metadata objects."""

    value = loaded() if callable(loaded) and not isinstance(loaded, AdapterPluginMeta) else loaded
    if isinstance(value, AdapterPluginMeta):
        return [value]
    if isinstance(value, dict):
        return [AdapterPluginMeta(**value)]
    if isinstance(value, (list, tuple)):
        metas: list[AdapterPluginMeta] = []
        for item in value:
            metas.extend(_metadata_from_loaded(name, item))
        return metas
    return [
        AdapterPluginMeta(
            name=name,
            version="0.0.0",
            description="Third-party ShyftR adapter plugin without explicit metadata.",
            supported_input_kinds=(),
        )
    ]


def discover_adapter_plugins(
    *,
    entry_point_provider: Optional[EntryPointProvider] = None,
    group: str = ADAPTER_ENTRY_POINT_GROUP,
) -> list[AdapterPluginMeta]:
    """Discover optional adapter plugins through Python entry points.

    Optional plugin modules are imported only when this function is called and
    their entry point is loaded. ShyftR core imports do not require optional
    adapter dependencies to be installed.
    """

    provider = entry_point_provider or importlib_metadata.entry_points
    try:
        raw_entry_points = provider()
        entry_points = _select_entry_points(raw_entry_points, group)
    except Exception:
        return []

    plugins: list[AdapterPluginMeta] = []
    for entry_point in entry_points:
        try:
            loaded = entry_point.load()
            plugins.extend(_metadata_from_loaded(getattr(entry_point, "name", ""), loaded))
        except Exception:
            continue
    return plugins


def list_adapter_plugins(
    *,
    include_builtins: bool = True,
    entry_point_provider: Optional[EntryPointProvider] = None,
) -> list[AdapterPluginMeta]:
    """List built-in and optional runtime adapter plugins with deduplication."""

    plugins: list[AdapterPluginMeta] = []
    if include_builtins:
        plugins.extend(builtin_adapters())
    plugins.extend(discover_adapter_plugins(entry_point_provider=entry_point_provider))

    by_name: dict[str, AdapterPluginMeta] = {}
    for plugin in plugins:
        existing = by_name.get(plugin.name)
        if existing is None or (existing.builtin and not plugin.builtin):
            by_name[plugin.name] = plugin
    return list(by_name.values())


def adapter_plugins_payload(
    *,
    entry_point_provider: Optional[EntryPointProvider] = None,
) -> dict[str, Any]:
    """Return the JSON payload used by ``shyftr adapter list``."""

    plugins = list_adapter_plugins(entry_point_provider=entry_point_provider)
    return {
        "status": "ok",
        "entry_point_group": ADAPTER_ENTRY_POINT_GROUP,
        "builtin_count": sum(1 for plugin in plugins if plugin.builtin),
        "plugin_count": sum(1 for plugin in plugins if not plugin.builtin),
        "total": len(plugins),
        "plugins": [plugin.to_dict() for plugin in plugins],
    }


# Backward-friendly aliases for callers/tests that prefer shorter names.
discover_plugins = discover_adapter_plugins
list_plugins = list_adapter_plugins


__all__ = [
    "ADAPTER_ENTRY_POINT_GROUP",
    "CONFIG_SCHEMA_VERSION",
    "AdapterPluginMeta",
    "adapter_plugins_payload",
    "builtin_adapters",
    "builtin_file_adapter",
    "discover_adapter_plugins",
    "discover_plugins",
    "list_adapter_plugins",
    "list_plugins",
]
