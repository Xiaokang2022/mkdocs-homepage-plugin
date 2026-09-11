"""Render the Markdown written inside a block with the site's own extension set.

A homepage must not render the same text two different ways depending on whether
it sits in a card or in the page body -- ``pymdownx`` admonitions, ``attr_list``,
``snippets``, ``superfences`` and friends have to behave identically.  So the
fragment is rendered by a *second* :class:`markdown.Markdown` instance that is
built from the very same extension list the site uses, minus the few extensions
that only make sense for a whole page.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Iterable, Mapping, Sequence

import markdown
from markdown.treeprocessors import Treeprocessor

from .context import resolve_url
from .util import esc

log = logging.getLogger("mkdocs.plugins.homepage")

#: Extensions that must not run on a *fragment*:
#:
#: * ``toc`` -- would sprinkle permalink anchors over card headings and leave a
#:   stray page-level table of contents behind;
#: * ``meta`` -- would eat a leading ``key: value`` paragraph as front matter.
DEFAULT_EXCLUDE: tuple[str, ...] = ("toc", "meta")

#: Our own extension, excluded by import path so a fragment can never recurse.
OWN_PACKAGE = "mkdocs_homepage"

_PARAGRAPH_RE = re.compile(r"<p>(?P<body>.*)</p>\s*$", re.S)


class LinkResolver(Treeprocessor):
    """Resolve ``href``/``src`` in a fragment the way MkDocs resolves the page.

    A block's HTML is stashed, so MkDocs' own relative-link treeprocessor only
    ever sees the placeholder.  Without this, a `guide/index.md` link written in a
    block *body* would survive into the site verbatim while the identical link in
    the page body was rewritten -- the same text behaving two different ways,
    which is exactly the kind of asymmetry this plugin exists to avoid.
    """

    def run(self, root):
        for element in root.iter():
            if not hasattr(element, "get"):
                continue
            for attribute in ("href", "src"):
                value = element.get(attribute)
                if not value:
                    continue
                resolved = resolve_url(value)
                if resolved and resolved != value:
                    element.set(attribute, resolved)
        return root


def extension_name(entry: Any) -> str | None:
    """Return the extension name of a MkDocs ``markdown_extensions`` item."""
    if isinstance(entry, str):
        return entry
    if isinstance(entry, Mapping):
        for key in entry:
            return str(key)
    return None


def short_name(name: str) -> str:
    """``pymdownx.superfences`` -> ``superfences``; ``markdown.extensions.toc`` -> ``toc``."""
    module = name.split(":", 1)[0]
    return module.rsplit(".", 1)[-1].lower()


def is_own_extension(name: str) -> bool:
    module = name.split(":", 1)[0]
    return module.split(".", 1)[0] == OWN_PACKAGE


class MarkdownRunner:
    """A private Markdown instance for block bodies.

    ``markdown.Markdown`` objects are stateful -- and therefore not thread-safe --
    so MkDocs builds a fresh one per page; this runner follows the same lifetime
    and is created per :class:`~mkdocs_homepage.extension.HomepageExtension`
    instance, i.e. per page.
    """

    def __init__(
        self,
        extensions: Sequence[Any] = (),
        extension_configs: Mapping[str, Any] | None = None,
        exclude: Iterable[str] = DEFAULT_EXCLUDE,
    ) -> None:
        self._extensions = list(extensions)
        self._configs = dict(extension_configs or {})
        self._exclude = tuple(exclude)
        self._md: markdown.Markdown | None = None

    # -- configuration ---------------------------------------------------
    def configure(
        self,
        extensions: Sequence[Any] | None = None,
        extension_configs: Mapping[str, Any] | None = None,
    ) -> None:
        if extensions is not None:
            self._extensions = list(extensions)
        if extension_configs is not None:
            self._configs = dict(extension_configs)
        self._md = None

    def _is_excluded(self, name: str) -> bool:
        if is_own_extension(name):
            return True
        return short_name(name) in self._exclude

    def _resolved(self) -> tuple[list[str], dict]:
        names: list[str] = []
        configs: dict = {}
        for entry in self._extensions:
            name = extension_name(entry)
            if name is None or self._is_excluded(name):
                continue
            if name in names:
                continue
            names.append(name)
            if isinstance(entry, Mapping):
                options = entry.get(name)
                if isinstance(options, Mapping):
                    configs[name] = dict(options)
            elif name in self._configs:
                options = self._configs[name]
                if isinstance(options, Mapping):
                    configs[name] = dict(options)
        return names, configs

    def _instance(self) -> markdown.Markdown:
        if self._md is None:
            names, configs = self._resolved()
            instance = markdown.Markdown(extensions=names, extension_configs=configs)
            # Priority 0 so it runs after `attr_list` and friends have settled the
            # fragment's attributes.
            instance.treeprocessors.register(
                LinkResolver(instance), "homepage_link_resolver", 0
            )
            self._md = instance
        return self._md

    # -- rendering -------------------------------------------------------
    def convert(self, text: str | None) -> str:
        """Render a Markdown fragment to HTML (``""`` for empty input)."""
        if not text or not text.strip():
            return ""
        instance = self._instance()
        # `convert` is not self-resetting: without this, the previous fragment's
        # footnote/toc state leaks into the next block.
        instance.reset()
        return instance.convert(text)

    def inline(self, text: str | None) -> str:
        """Render a Markdown fragment with a single wrapping ``<p>`` unwrapped.

        Card titles and one-line descriptions live inside their own elements, so
        ending up with a ``<p>`` in them would break the layout.  When the input
        does *not* render to a single paragraph -- because the author started it
        with ``#`` or ``-``, say -- the raw text is escaped instead of being
        inlined, so a block element can never land inside a heading.
        """
        source = (text or "").strip()
        if not source:
            return ""
        html = self.convert(source).strip()
        match = _PARAGRAPH_RE.fullmatch(html)
        return match.group("body") if match else esc(source)
