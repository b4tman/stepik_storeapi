"""Config functions."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig

    from mkapi.plugins import MkAPIPlugin


def before_on_config(config: MkDocsConfig, plugin: MkAPIPlugin) -> None:  # noqa: ARG001
    """Called before `on_config` event of MkAPI plugin."""
    if "src" not in sys.path:
        sys.path.insert(0, "src")
