"""Per-page context, handed from the plugin to the Markdown extension.

The extension is instantiated by Python-Markdown inside MkDocs, so it has no way
to reach the page being converted.  ``on_page_markdown`` runs in the same thread,
immediately before ``md.convert()``, so a thread-local is a safe channel for the
two things the extension needs: the source path (so a malformed block is reported
as ``docs/index.md:42``) and enough page identity to resolve links the way MkDocs
would.

The second one exists because a block's HTML is stashed: MkDocs' relative-link
treeprocessor only ever sees the placeholder, never the markup.  Without this,
``link: guide/index.md`` -- the spelling every MkDocs author already uses -- would
produce a literal ``index.md`` href that 404s.  ``tests/test_build.py`` asserts
that no ``.md`` href survives into the built site.
"""

from __future__ import annotations

import logging
import posixpath
import re
import threading
from dataclasses import dataclass
from typing import Any
from urllib.parse import unquote, urlsplit, urlunsplit

log = logging.getLogger("mkdocs.plugins.homepage")

#: Anything with a scheme (`https:`, `mailto:`) is somebody else's problem.
_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*:")

_local = threading.local()


@dataclass
class PageContext:
    """What the renderer needs to know about the page being converted."""

    src_uri: str
    url: str
    files: Any = None


def set_page_context(context: "PageContext | None") -> None:
    _local.context = context


def current_page() -> "PageContext | None":
    return getattr(_local, "context", None)


def clear_page_context() -> None:
    _local.context = None


def current_page_source() -> str | None:
    """The source path of the page being converted, for diagnostics."""
    context = current_page()
    return context.src_uri if context is not None else None


def resolve_url(value: Any) -> str | None:
    """Resolve a link the way MkDocs resolves the ones in the page body.

    Returns the value unchanged when there is nothing to resolve -- an external
    URL, an absolute path, a bare anchor, or no page context at all.
    """
    if value is None:
        return None
    text = str(value).strip()
    if not text or _SCHEME_RE.match(text) or text.startswith(("//", "#", "/")):
        return text

    context = current_page()
    if context is None or context.files is None:
        return text

    _scheme, _netloc, path, query, anchor = urlsplit(text)
    if not path:
        return text

    target_uri = posixpath.normpath(
        posixpath.join(posixpath.dirname(context.src_uri), unquote(path)).lstrip("/")
    )
    target = context.files.get_file_from_path(target_uri)
    if target is None:
        if path.endswith((".md", ".markdown")):
            log.warning(
                "homepage: %s: link %r does not match any file in the docs directory",
                context.src_uri,
                text,
            )
        return text

    from mkdocs.utils import get_relative_url

    return urlunsplit(("", "", get_relative_url(target.url, context.url), query, anchor))
