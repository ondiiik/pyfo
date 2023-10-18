from __future__ import annotations

from rich.console import Console, Group, RenderableType  # :~PYFO~: public
from rich.markdown import Markdown  # :~PYFO~: public
from rich.padding import Padding  # :~PYFO~: public
from rich.panel import Panel  # :~PYFO~: public
from rich.table import Table  # :~PYFO~: public
from rich.text import Text  # :~PYFO~: public

USE_MARKUP = True

console = Console(markup=USE_MARKUP)
console_err = Console(markup=USE_MARKUP, stderr=True)

__all__ = (
    "Console",
    "Group",
    "Markdown",
    "Padding",
    "Panel",
    "RenderableType",
    "Table",
    "Text",
    "USE_MARKUP",
    "console",
    "console_err",
)
