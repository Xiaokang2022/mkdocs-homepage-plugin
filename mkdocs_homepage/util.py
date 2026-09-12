"""Small, dependency-free helpers shared by the parser, renderer and plugin."""

from __future__ import annotations

import html
import re
from typing import Any, Iterable, Mapping

_TRUTHY = frozenset({"1", "true", "yes", "y", "t", "on", "enable", "enabled"})
_FALSY = frozenset({"", "0", "false", "no", "n", "f", "off", "disable", "disabled", "none"})

#: Characters that survive into an HTML ``id``.  CJK is kept on purpose: Material
#: ships a Unicode-capable slugify and Chinese anchors must stay linkable.
_SLUG_DROP = re.compile(r"[^\w\u3000-\u9fff\uff00-\uffef\-\s]", re.UNICODE)
_SLUG_SPACE = re.compile(r"[\s_]+")
_CLASS_DROP = re.compile(r"[^A-Za-z0-9_\-\s]")

_LENGTH_RE = re.compile(r"^(\d+(?:\.\d+)?)\s*(em|rem|px|%|vh|vw|ch|fr)?$")

#: ``16/10``, ``16 / 9``, ``4:3`` -- the aspect ratios authors actually type.
_RATIO_RE = re.compile(r"^(\d+(?:\.\d+)?)\s*[/:]\s*(\d+(?:\.\d+)?)$")

#: URL schemes that must never end up in an ``href``/``src``.
_SCHEME_RE = re.compile(r"^(?:javascript|vbscript|data|blob|file)\s*:", re.I)

#: Picture formats an ``icon:`` value may point at instead of naming a glyph.
IMAGE_SUFFIXES = frozenset(
    {"svg", "png", "jpg", "jpeg", "webp", "gif", "avif", "bmp", "ico"}
)


def image_suffix(value: Any) -> str | None:
    """The picture extension of a URL-ish string, lower-cased, or ``None``.

    Query strings and fragments are dropped first, because
    ``logo.svg?v=2`` is a picture too.
    """
    text = str(value or "").strip()
    if not text:
        return None
    tail = text.split("?", 1)[0].split("#", 1)[0]
    name = tail.rpartition("/")[2]
    if "." not in name:
        return None
    suffix = name.rpartition(".")[2].lower()
    return suffix or None


def is_image_ref(value: Any) -> bool:
    """Whether an ``icon:`` value points at a picture rather than naming a glyph.

    Every slot that draws an icon draws a picture too, and the most forgiving way
    to say so is to let the *same* key take either: ``icon: rocket-launch-outline``
    is a glyph, ``icon: assets/logo.svg`` is a file.  The extension is the whole
    test -- a slash cannot be used, because icon sets address their marks as
    ``simple/github``.  That is only unambiguous because **no bundled icon name
    contains a dot**, which a test pins.
    """
    return image_suffix(value) in IMAGE_SUFFIXES


def css_ratio(value: Any) -> str | None:
    """Validate an aspect ratio, returning it as ``"a / b"`` for CSS.

    ``ratio: 16/10``, ``16 / 9``, ``4:3`` and a bare number all mean the same
    thing to an author; a length validator rejects every one of them, which is
    how a silently-ignored ``ratio:`` prop is born.
    """
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return f"{float(value):g}" if value > 0 else None
    match = _RATIO_RE.match(str(value).strip())
    if not match:
        return None
    width, height = float(match.group(1)), float(match.group(2))
    if width <= 0 or height <= 0:
        return None
    return f"{width:g} / {height:g}"


def esc(value: Any) -> str:
    """HTML-escape *value* (attribute-safe)."""
    return html.escape("" if value is None else str(value), quote=True)


def slugify(value: Any, fallback: str = "section") -> str:
    """Turn arbitrary text into a URL-safe, Unicode-preserving fragment id."""
    slug = _SLUG_DROP.sub("", str(value or "").strip().lower())
    slug = _SLUG_SPACE.sub("-", slug).strip("-")
    return slug or fallback


def css_class(value: Any) -> str:
    """Sanitise a user-supplied class list down to safe class names."""
    if not value:
        return ""
    if isinstance(value, (list, tuple, set)):
        value = " ".join(str(item) for item in value)
    return " ".join(_CLASS_DROP.sub("", str(value)).split())


def css_length(value: Any) -> str | None:
    """Return a safe CSS length for an inline custom property, or ``None``.

    Only numbers with a known unit survive, so a prop can never smuggle arbitrary
    CSS (or a ``;``) into an inline style attribute.
    """
    if value is None or value == "":
        return None
    match = _LENGTH_RE.match(str(value).strip())
    if not match:
        return None
    number, unit = match.group(1), match.group(2)
    return f"{number}{unit or 'px'}"


def safe_url(value: Any) -> str | None:
    """Return a URL that is safe to place in an ``href``/``src``, else ``None``.

    A homepage is authored by the site owner, so this is not a security boundary
    for untrusted input -- it is a guard against a props block that silently
    produces a script URL.  Scheme-relative and relative URLs pass through.
    """
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if _SCHEME_RE.match(text):
        return None
    return text


def as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in _TRUTHY:
        return True
    if text in _FALSY:
        return False
    return default


def as_list(value: Any) -> list:
    """Normalise ``None`` / scalar / sequence into a list."""
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def as_text(value: Any) -> str:
    """Flatten a scalar-or-list of scalars into one line of escaped text."""
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return " · ".join(esc(item) for item in value if item not in (None, ""))
    return esc(value)


def attrs(**kwargs: Any) -> str:
    """Render keyword arguments as HTML attributes.

    ``None``/``False`` drop the attribute, ``True`` renders a bare attribute and
    underscores become hyphens (``data_home_tilt`` -> ``data-home-tilt``).
    """
    parts = []
    for key, value in kwargs.items():
        if value is None or value is False:
            continue
        key = key.rstrip("_").replace("_", "-")
        if value is True:
            parts.append(key)
        else:
            parts.append(f'{key}="{esc(value)}"')
    return (" " + " ".join(parts)) if parts else ""


def props_to_style(props: Mapping[str, Any], mapping: Mapping[str, str]) -> str:
    """Build an inline ``style`` attribute from ``prop -> css var`` pairs."""
    declarations = []
    for prop, variable in mapping.items():
        value = css_length(props.get(prop))
        if value:
            declarations.append(f"{variable}:{value}")
    return f' style="{"".join(d + ";" for d in declarations)}"' if declarations else ""


def first_of(props: Mapping[str, Any], *keys: str, default: Any = None) -> Any:
    """Return the first key present in *props* (in the order given)."""
    for key in keys:
        if key in props and props[key] is not None:
            return props[key]
    return default


def dedupe(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def split_pipe(value: Any, maxparts: int = 0) -> list[str]:
    """Split ``"a | b | c"`` into trimmed parts ('|' is the inline shorthand)."""
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value]
    parts = [part.strip() for part in str(value).split("|")]
    if maxparts and len(parts) > maxparts:
        head = parts[: maxparts - 1]
        head.append(" | ".join(parts[maxparts - 1 :]))
        parts = head
    return parts
