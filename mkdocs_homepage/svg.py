"""Inline icons for the widget's chrome and for brand marks.

Icons are inlined rather than referenced through ``material``'s ``icon()`` helper
so that the widget keeps working on other themes, and so that no icon font is
needed and no extra request is made.  Each icon is a plain ``currentColor`` path
wrapped in Material's own ``.md-icon`` span, which means the theme tints it -- the
palette and the dark scheme keep working for free.

Names are addressed the way Material itself addresses icons -- ``set/name``:

* ``rocket-launch-outline`` / ``material/rocket-launch-outline``: Material Design
  Icons, the set the theme ships and whose line weight matches it;
* ``simple/github``: Simple Icons, for the brand marks a "trusted by" row needs.
"""

from __future__ import annotations

import logging

from .icons import BRAND_PATHS, ICON_PATHS, ICON_SETS, ICON_SOURCE  # noqa: F401 (re-exported)
from .util import esc

log = logging.getLogger("mkdocs.plugins.homepage")

__all__ = [
    "BRAND_PATHS",
    "ICON_PATHS",
    "ICON_SETS",
    "ICON_SOURCE",
    "icon",
    "icon_names",
    "resolve",
]

#: The set a bare name resolves against.
DEFAULT_SET = "material"

_SVG_ATTRS = 'xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox}"'
_MISSING_CLASS = "md-home__icon--missing"


def icon_names(set_name: str | None = None) -> tuple:
    """Return the names of one set, or every set as ``set/name``."""
    if set_name is not None:
        return tuple(sorted(ICON_SETS.get(set_name, {})))
    names = []
    for name, table in ICON_SETS.items():
        names.extend(key if name == DEFAULT_SET else f"{name}/{key}" for key in table)
    return tuple(sorted(names))


def resolve(name: object) -> tuple:
    """Return ``(set_name, key, entry)`` for an icon name, or ``()`` if unknown.

    Accepts ``name``, ``set/name`` and ``set:name`` -- Material uses the slash in
    configuration, and a colon is what an author typing quickly will reach for.
    """
    if name is None:
        return ()
    text = str(name).strip()
    if not text:
        return ()

    set_name, _, key = text.replace(":", "/").rpartition("/")
    set_name = set_name.strip().lower()
    key = key.strip().lower()

    if set_name:
        table = ICON_SETS.get(set_name)
        if table is None or key not in table:
            return ()
        return set_name, key, table[key]

    table = ICON_SETS[DEFAULT_SET]
    if key in table:
        return DEFAULT_SET, key, table[key]
    return ()


def has_icon(name: object) -> bool:
    return bool(resolve(name))


def _hint(key: str) -> str:
    """``" — did you mean simple/github?"`` when only the set prefix is missing."""
    for set_name, table in ICON_SETS.items():
        if set_name != DEFAULT_SET and key in table:
            return f" — did you mean {set_name}/{key}?"
    return ""


def icon(name: object, label: str | None = None) -> str:
    """Render an icon as an inline ``currentColor`` SVG inside a ``.md-icon``.

    An unknown name is a bug, never a silent no-op: it is logged and rendered as a
    dashed placeholder box, because an unknown name would otherwise produce an
    empty ``<path>`` -- a valid SVG that renders nothing at all, with no console
    error and no failed assertion, just an invisible control.
    """
    if name is None or not str(name).strip():
        return ""

    found = resolve(name)
    if not found:
        key = str(name).strip().lower().replace(":", "/").rpartition("/")[2]
        log.warning(
            "homepage: unknown icon %r; available: %s%s",
            name,
            ", ".join(icon_names()),
            _hint(key),
        )
        return (
            f'<span class="md-icon {_MISSING_CLASS}" title="unknown icon: {esc(name)}"'
            ' aria-hidden="true"></span>'
        )

    set_name, key, entry = found
    viewbox, paths = entry
    if isinstance(paths, str):
        # Defensive: a single path written without a surrounding tuple is
        # iterated character by character, emitting `<path d="m"/>`,
        # `<path d="1"/>`, ... -- a valid SVG that draws nothing at all.
        paths = (paths,)

    body = "".join(f'<path d="{path}"/>' for path in paths)
    role = f'role="img" aria-label="{esc(label)}"' if label else 'aria-hidden="true"'
    extra = f" md-home__icon--{esc(set_name)}" if set_name != DEFAULT_SET else ""
    return (
        f'<span class="md-icon{extra}" {role}>'
        f'<svg {_SVG_ATTRS.format(viewbox=viewbox)}>{body}</svg>'
        "</span>"
    )
