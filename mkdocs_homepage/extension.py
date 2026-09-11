"""The Markdown side of the plugin: a preprocessor for ``homepage`` fences.

Python-Markdown runs preprocessors in descending priority order and
``fenced_code``/``pymdownx.superfences`` sit at 25, so this one claims 30: it has
to see the raw document *before* the fence becomes a ``<pre><code>`` block.

Blocks are not injected as raw HTML into the document.  They are handed to
``md.htmlStash``, which swaps them back in after every tree processor has run --
that is what stops MkDocs' relative-link rewriting, the ``toc`` extension or an
admonition-aware treeprocessor from reaching into a card and mangling it.
"""

from __future__ import annotations

import logging
from typing import Any, Mapping

from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor

from .converter import MarkdownRunner
from .context import current_page_source
from .parser import Block, BlockError, split_blocks
from .render import BlockRenderer

log = logging.getLogger("mkdocs.plugins.homepage")

#: Higher than ``fenced_code`` (25) so the fences are still raw text.
PRIORITY = 30


class HomepagePreprocessor(Preprocessor):
    """Replace ``homepage-*`` fences with stashed HTML."""

    def __init__(self, md, extension: "HomepageExtension") -> None:
        super().__init__(md)
        self.extension = extension

    def run(self, lines: list) -> list:
        source = "\n".join(lines)
        if "homepage" not in source:  # cheap bail-out for the common case
            return lines

        segments = split_blocks(source, source=current_page_source())
        if not any(isinstance(segment, Block) for segment in segments):
            return lines

        rendered: list[str] = []
        for segment in segments:
            if isinstance(segment, Block):
                rendered.append(self.extension.render_block(segment))
            else:
                rendered.append(segment)
        return "\n".join(rendered).split("\n")


class HomepageExtension(Extension):
    """Render ``homepage-*`` fenced blocks.

    Configuration (usually filled in by :class:`~mkdocs_homepage.plugin.HomepagePlugin`
    from the site's own config, so authors never write it by hand):

    ``extensions``
        The site's ``markdown_extensions``.  Block bodies are rendered with them,
        so a card and the page body cannot render the same Markdown differently.

    ``extension_configs``
        The site's ``mdx_configs``, threaded through for the same reason.

    ``exclude_extensions``
        Extension names that must not run on a fragment (default: ``toc``, ``meta``).

    ``options``
        Behaviour switches shared with the stylesheet/script: ``tilt``,
        ``tilt_strength``, ``reveal``, ``lightbox``, ``count``.

    ``strict``
        Raise on a malformed block instead of logging a warning and rendering an
        inline error marker.
    """

    def __init__(self, **kwargs: Any) -> None:
        self.config: dict = {
            "extensions": [[], "The site's markdown_extensions, used for block bodies."],
            "extension_configs": [{}, "The site's mdx_configs, used for block bodies."],
            "exclude_extensions": [
                ("toc", "meta"),
                "Bodies are fragments; these must not run on them.",
            ],
            "options": [{}, "Behaviour switches shared with the stylesheet and script."],
            "strict": [False, "Raise on a malformed block instead of warning."],
        }
        super().__init__(**kwargs)
        self._runner: MarkdownRunner | None = None
        self._renderer: BlockRenderer | None = None
        self._used = False

    # -- lazily built collaborators (per page, see MarkdownRunner's docstring) --
    @property
    def runner(self) -> MarkdownRunner:
        if self._runner is None:
            self._runner = MarkdownRunner(
                extensions=self.getConfig("extensions") or [],
                extension_configs=self.getConfig("extension_configs") or {},
                exclude=self.getConfig("exclude_extensions") or (),
            )
        return self._runner

    @property
    def renderer(self) -> BlockRenderer:
        if self._renderer is None:
            self._renderer = BlockRenderer(self.runner, self.getConfig("options") or {})
        return self._renderer

    #: True once at least one block has been rendered for this page.
    @property
    def used(self) -> bool:
        return self._used

    # -- API -------------------------------------------------------------
    def render_block(self, block: Block) -> str:
        """Render one block, turning a malformed one into a warning or an error."""
        if block.issue:
            # Already reported by the parser, with its line number: logging it
            # again here would double every parse warning.
            return self.fail(block, block.issue, log_it=False)
        try:
            html = self.renderer.render(block)
        except BlockError as error:
            return self.fail(block, str(error))
        self._used = True
        return html

    def fail(self, block: Block, message: str, *, log_it: bool = True) -> str:
        """Report a broken block: fail the build, or warn and mark the spot."""
        if self.getConfig("strict"):
            where = f"{block.source}:{block.line}" if block.source else str(block.line)
            raise BlockError(f"{where}: {message}")
        if log_it:
            self.log_issue(block, message)
        return self._error_marker(block, message)

    def log_issue(self, block: Block, message: str) -> None:
        where = f"{block.source or '<page>'}:{block.line}"
        log.warning("homepage: %s: %s", where, message)

    @staticmethod
    def _error_marker(block: Block, message: str) -> str:
        """A visible, un-styleable marker so a broken block is never invisible."""
        from .util import esc  # local import keeps the module import graph flat

        return (
            f'<div class="md-home md-home--error" data-home-block="error"'
            f' data-home-line="{block.line}">'
            f'<p class="md-home__error-title">homepage {esc(block.info or block.kind)} block '
            f"(line {block.line})</p>"
            f"<p class=\"md-home__error-message\">{esc(message)}</p>"
            "</div>"
        )

    def extendMarkdown(self, md) -> None:
        md.preprocessors.register(HomepagePreprocessor(md, self), "homepage", PRIORITY)
        md.registerExtension(self)

    def reset(self) -> None:
        # `Markdown.reset()` calls this on every registered extension, so the
        # per-document flag is cleared here rather than in `extendMarkdown`.
        self._used = False


def makeExtension(**kwargs: Any) -> HomepageExtension:  # noqa: N802 (Markdown API)
    """Entry point used by ``markdown.Markdown(extensions=["..."])``."""
    return HomepageExtension(**kwargs)
