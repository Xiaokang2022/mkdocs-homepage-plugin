"""mkdocs-homepage-plugin.

Compose a MkDocs Material homepage out of themed content blocks, written entirely
in Markdown.  ``HomepagePlugin`` wires the Markdown extension, the stylesheet and
the behaviour script into a site; ``HomepageExtension`` is the Markdown side and
can be used on its own.
"""

from __future__ import annotations

from .extension import HomepageExtension
from .plugin import HomepagePlugin

__all__ = ["HomepageExtension", "HomepagePlugin", "__version__"]

__version__ = "0.1.0"
