"""Regenerate :mod:`mkdocs_homepage.icons` from the installed Material theme.

The widget never loads an icon font and never requests an icon at runtime: every
glyph is an inline ``<path>`` copied out of Material's own MDI set, so it inherits
``currentColor`` and therefore the active palette.  This script is the only thing
that is allowed to write ``icons.py``; ``tests/test_icons.py`` re-derives the same
data and compares it token by token, so a stale or hand-edited copy fails the suite.

Usage::

    python scripts/generate_icons.py            # print to stdout
    python scripts/generate_icons.py --write    # overwrite the module
"""

from __future__ import annotations

import argparse
import os
import re
import sys

#: Curated Material Design Icons.  Keep it small and purposeful: every name here
#: is referenced by the built-in defaults or by the documentation examples.
ICON_NAMES = (
    # navigation / chrome
    "arrow-right",
    "arrow-up-right",
    "chevron-left",
    "chevron-right",
    "chevron-up",
    "chevron-down",
    "close",
    "plus",
    "minus",
    "check",
    "magnify",
    "open-in-new",
    "download-outline",
    "refresh",
    "play-circle-outline",
    "dots-horizontal",
    # generic content
    "rocket-launch-outline",
    "book-open-page-variant-outline",
    "bookmark-outline",
    "file-document-outline",
    "text-box-outline",
    "code-tags",
    "console",
    "server",
    "cloud-outline",
    "database-outline",
    "api",
    "package-variant-closed",
    "language-python",
    "language-javascript",
    "palette-outline",
    "puzzle-outline",
    "shape-outline",
    "layers-outline",
    "auto-fix",
    "tools",
    "lightbulb-outline",
    "lightning-bolt-outline",
    "fire",
    "star",
    "star-outline",
    "heart-outline",
    "thumb-up-outline",
    "format-quote-open",
    # media
    "image-outline",
    "view-gallery-outline",
    "movie-open-outline",
    # data / process
    "chart-line",
    "speedometer",
    "view-dashboard-outline",
    "calendar-blank-outline",
    "clock-outline",
    "timeline-outline",
    # people / meta
    "account-group-outline",
    "account-outline",
    "compass-outline",
    "earth",
    "translate",
    "shield-check-outline",
    "link-variant",
    "email-outline",
    "information-outline",
    "alert-outline",
    "check-circle-outline",
)

#: Brand marks from the bundled Simple Icons set.  These are what a "trusted by"
#: row needs, and MDI has almost none of them -- `fastapi`, `docker`, `pypi` and
#: friends only exist here.  A curated subset keeps the generated module readable;
#: `simple:<name>` is the escape hatch for anything else already installed.
BRAND_NAMES = (
    "android",
    "apple",
    "cloudflare",
    "discord",
    "docker",
    "fastapi",
    "git",
    "github",
    "go",
    "javascript",
    "kubernetes",
    "linux",
    "markdown",
    "mastodon",
    "materialdesign",
    "netlify",
    "nginx",
    "npm",
    "postgresql",
    "pydantic",
    "pypi",
    "python",
    "react",
    "readthedocs",
    "redis",
    "rust",
    "sqlite",
    "svelte",
    "typescript",
    "vercel",
    "x",
)

_PATH_RE = re.compile(r'<path\b[^>]*\bd="([^"]*)"', re.S)
_VIEWBOX_RE = re.compile(r'viewBox="([^"]*)"')


def set_directories() -> dict:
    """Return the bundled icon sets as ``{name: directory}``.

    ``material`` is Material Design Icons, which is what the widget's own chrome
    is built from (and whose line weight matches the theme).  ``simple`` is Simple
    Icons, the brand marks a "trusted by" row needs.
    """
    try:
        import material  # noqa: PLC0415  (optional dependency, imported lazily)
    except ImportError:
        return {}
    root = os.path.join(os.path.dirname(material.__file__), "templates", ".icons")
    return {
        name: path
        for name in ("material", "simple")
        if os.path.isdir(path := os.path.join(root, name))
    }


def material_icon_dir() -> str | None:
    """Return Material's bundled MDI directory, or ``None`` if not installed."""
    return set_directories().get("material")


def read_icon(directory: str, name: str) -> tuple[str, tuple[str, ...]]:
    with open(os.path.join(directory, name + ".svg"), encoding="utf-8") as handle:
        svg = handle.read()
    viewbox = _VIEWBOX_RE.search(svg)
    paths = _PATH_RE.findall(svg)
    if not paths:
        raise ValueError(f"no <path d=...> found in {name}.svg")
    return (viewbox.group(1) if viewbox else "0 0 24 24"), tuple(paths)


def _entry(name: str, viewbox: str, paths: tuple) -> str:
    # The paths are *always* a tuple, even for the common single-path icon.  A
    # bare string here would be iterated character by character at render time,
    # producing one `<path d="m"/>` per letter of the path data: a valid SVG, no
    # console error, and an invisible glyph.
    body = "\n".join(f'            "{path}",' for path in paths)
    return f'    "{name}": (\n        "{viewbox}",\n        (\n{body}\n        ),\n    ),'


def build_set(directory: str, names) -> str:
    entries = []
    for name in names:
        viewbox, paths = read_icon(directory, name)
        entries.append(_entry(name, viewbox, paths))
    return "\n".join(entries)


HEADER = '''"""Inline SVG paths for the widget's chrome and for brand marks.

Generated by ``scripts/generate_icons.py`` from the Material theme's bundled icon
sets -- do not edit by hand.

Two sets, addressed the way Material itself addresses icons (``set/name``):

* ``material`` (Material Design Icons) -- the widget's own chrome.  Its line
  weight matches the theme, so a bare name resolves here first.
* ``simple`` (Simple Icons) -- brand marks, for "trusted by" rows.

Each entry is ``name -> (viewBox, (path_data, ...))``.  Two details are load
bearing:

* ``path_data`` is **always** a tuple, even for a single-path icon.  A bare
  string would be iterated character by character when rendering, emitting one
  ``<path d="m"/>`` per letter -- a valid SVG that draws nothing.
* a ``d`` attribute is kept as **one** string literal on purpose: SVG path data
  uses whitespace as a *separator*, so re-wrapping a long path across
  ``"..." + "..."`` silently turns ``c5 0 9.27`` into ``c5 09.27``, a different
  and wrong shape that no reviewer can spot.

``tests/test_icons.py`` re-derives both from the installed theme.
"""

from __future__ import annotations

ICON_SOURCE = "Material for MkDocs, templates/.icons"

#: Material Design Icons: the widget's chrome.  Referenced bare or as
#: ``material/<name>``.
ICON_PATHS: dict[str, tuple[str, tuple[str, ...]]] = {
'''

MIDDLE = '''}

#: Simple Icons: brand marks.  Always referenced as ``simple/<name>``.
BRAND_PATHS: dict[str, tuple[str, tuple[str, ...]]] = {
'''

FOOTER = '''}

#: All sets by their ``set/name`` prefix, as used in an ``icon:`` prop.
ICON_SETS: dict[str, dict[str, tuple[str, tuple[str, ...]]]] = {
    "material": ICON_PATHS,
    "simple": BRAND_PATHS,
}
'''


def build_module(directory: str, brand_directory: str | None) -> str:
    parts = [HEADER, build_set(directory, ICON_NAMES), MIDDLE]
    if brand_directory:
        parts.append(build_set(brand_directory, BRAND_NAMES))
    parts.append(FOOTER)
    return "\n".join(parts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="overwrite mkdocs_homepage/icons.py")
    args = parser.parse_args(argv)

    directory = material_icon_dir()
    if directory is None:
        print("mkdocs-material is not installed; cannot regenerate icons.", file=sys.stderr)
        return 1

    text = build_module(directory, set_directories().get("simple"))
    if not args.write:
        sys.stdout.write(text)
        return 0

    target = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "mkdocs_homepage",
        "icons.py",
    )
    with open(target, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    total = len(ICON_NAMES) + len(BRAND_NAMES)
    print(f"wrote {target} ({total} icons)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
