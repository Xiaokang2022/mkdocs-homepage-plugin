"""Shared helpers for the test suite."""

from __future__ import annotations

import markdown
import pytest

from mkdocs_homepage.extension import HomepageExtension
from mkdocs_homepage.parser import Block, split_blocks

#: Extensions used by the render tests.  Kept deliberately close to a real
#: `mkdocs.yml` so that the "same extensions as the page" rule is exercised:
#: `toc` and `meta` must be dropped by the runner, the rest must run.
SITE_EXTENSIONS = [
    "admonition",
    "attr_list",
    "md_in_html",
    "tables",
    "toc",
    "meta",
    "pymdownx.superfences",
]
SITE_CONFIGS = {"toc": {"permalink": True}}


def render(markdown_text: str, *, options=None, extensions=None, configs=None, strict=False) -> str:
    """Render a document through the real block pipeline, without MkDocs.

    Goes through :meth:`HomepageExtension.render_block` rather than the renderer
    directly, so the error/warning policy is exercised too.
    """
    extension = HomepageExtension(
        extensions=SITE_EXTENSIONS if extensions is None else extensions,
        extension_configs=SITE_CONFIGS if configs is None else configs,
        options=options or {},
        strict=strict,
    )
    pieces = []
    for segment in split_blocks(markdown_text, source="test.md"):
        pieces.append(extension.render_block(segment) if isinstance(segment, Block) else segment)
    return "\n".join(pieces)


def render_one(fence_body: str, *, options=None) -> str:
    """Render exactly one block and return its HTML."""
    return render(fence_body, options=options)


@pytest.fixture
def convert():
    """Convert a document the way MkDocs does, via the Markdown extension."""

    def _convert(text: str, **kwargs) -> str:
        extension = HomepageExtension(**kwargs)
        instance = markdown.Markdown(extensions=[extension, "fenced_code"])
        return instance.convert(text)

    return _convert


@pytest.fixture
def blocks():
    """Parse a document into its segments."""

    def _blocks(text: str):
        return split_blocks(text, source="test.md")

    return _blocks


def homepage(**props) -> str:
    """Build a fence body from keyword props (lists become YAML lists)."""
    lines = []
    for key, value in props.items():
        if isinstance(value, (list, tuple)):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        else:
            lines.append(f"{key}: {value}")
    return "\n".join(lines)
