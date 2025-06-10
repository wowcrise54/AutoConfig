from __future__ import annotations

from typing import Dict, Type


class ScenarioPlugin:
    """Base class for all scenario plugins."""

    def start(self, **params):
        """Start the scenario and yield events as dictionaries."""
        raise NotImplementedError


_PLUGINS: Dict[str, Type[ScenarioPlugin]] = {}


def register_plugin(name: str, cls: Type[ScenarioPlugin]) -> None:
    _PLUGINS[name] = cls


def get_plugin(name: str) -> Type[ScenarioPlugin] | None:
    return _PLUGINS.get(name)

# register built-in plugins
from . import noop  # noqa: F401
from . import ddos  # noqa: F401
