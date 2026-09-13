"""Small, dependency-free helpers shared by the parser, renderer and plugin."""

from __future__ import annotations

import html
import logging
import re
from typing import Any, Iterable, Mapping

log = logging.getLogger("mkdocs.plugins.homepage")

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

#: The smallest bare number that can only be a ``a:b`` mangled by YAML's
#: sexagesimal reading.  ``1:1`` is the smallest unquoted ratio an author could
#: write that YAML would fold into a number, and it comes out as 61.  See
#: :func:`css_ratio`.
_SEXAGESIMAL_FLOOR = 61

#: URL schemes that must never end up in an ``href``/``src``.
_SCHEME_RE = re.compile(r"^(?:javascript|vbscript|data|blob|file)\s*:", re.I)

#: A hex colour: ``#abc``, ``#abcd``, ``#aabbcc``, ``#aabbccdd``.
_HEX_COLOR_RE = re.compile(r"^#(?:[0-9a-f]{3,4}|[0-9a-f]{6}|[0-9a-f]{8})$", re.I)

#: A colour function.  The character class is the whole guard: no ``;``, ``{``,
#: ``}``, quotes or backslashes can survive it, so the value cannot close the
#: declaration or the style attribute and start another one.
_COLOR_FUNCTION_RE = re.compile(
    r"^(?:rgb|rgba|hsl|hsla|hwb|lab|lch|oklab|oklch|color|color-mix|light-dark)"
    r"\([^;{}<>\"'\\]*\)$",
    re.I,
)

#: The CSS named colours.  A whitelist rather than `[a-z]+` on purpose: an
#: unknown name is a *typo*, and a typo that produces an invalid declaration is
#: dropped by the browser without a word.  ``transparent`` and ``currentcolor``
#: are included because they are legitimate values, not colours.
NAMED_COLORS = frozenset(
    """
    aliceblue antiquewhite aqua aquamarine azure beige bisque black blanchedalmond
    blue blueviolet brown burlywood cadetblue chartreuse chocolate coral
    cornflowerblue cornsilk crimson cyan darkblue darkcyan darkgoldenrod darkgray
    darkgreen darkgrey darkkhaki darkmagenta darkolivegreen darkorange darkorchid
    darkred darksalmon darkseagreen darkslateblue darkslategray darkslategrey
    darkturquoise darkviolet deeppink deepskyblue dimgray dimgrey dodgerblue
    firebrick floralwhite forestgreen fuchsia gainsboro ghostwhite gold goldenrod
    gray green greenyellow grey honeydew hotpink indianred indigo ivory khaki
    lavender lavenderblush lawngreen lemonchiffon lightblue lightcoral lightcyan
    lightgoldenrodyellow lightgray lightgreen lightgrey lightpink lightsalmon
    lightseagreen lightskyblue lightslategray lightslategrey lightsteelblue
    lightyellow lime limegreen linen magenta maroon mediumaquamarine mediumblue
    mediumorchid mediumpurple mediumseagreen mediumslateblue mediumspringgreen
    mediumturquoise mediumvioletred midnightblue mintcream mistyrose moccasin
    navajowhite navy oldlace olive olivedrab orange orangered orchid palegoldenrod
    palegreen paleturquoise palevioletred papayawhip peachpuff peru pink plum
    powderblue purple rebeccapurple red rosybrown royalblue saddlebrown salmon
    sandybrown seagreen seashell sienna silver skyblue slateblue slategray
    slategrey snow springgreen steelblue tan teal thistle tomato transparent
    turquoise violet wheat white whitesmoke yellow yellowgreen currentcolor
    """.split()
)


def css_color(value: Any) -> str | None:
    """Validate a CSS colour, or return ``None``.

    Same contract as :func:`css_length`: the value is destined for an inline
    custom property, so nothing may escape the declaration.  Three shapes are
    accepted -- a hex literal, one of the standard colour functions, and a named
    colour from :data:`NAMED_COLORS`.  Anything else is a typo or an injection
    attempt, and either way the caller reports it instead of emitting a
    declaration the browser will silently drop.
    """
    if value is None or isinstance(value, bool):
        return None
    text = str(value).strip()
    if not text:
        return None
    if _HEX_COLOR_RE.match(text) or _COLOR_FUNCTION_RE.match(text):
        return text
    lowered = text.lower()
    return lowered if lowered in NAMED_COLORS else None

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

    The one shape that is NOT accepted is a bare number large enough to be a
    ``a:b`` that YAML already evaluated.  YAML 1.1 reads ``4:3`` as *sexagesimal*
    -- ``4 * 60 + 3`` -- so ``ratio: 4:3`` (unquoted, the way anyone would type
    it) arrives here as ``243``, and ``243`` is a perfectly valid CSS ratio: the
    card rendered 243 times taller than it was wide, with no warning anywhere.
    Since no one sizes a card at 61:1 or beyond, that range is treated as the
    authoring mistake it is, and the prop falls back to its default instead.
    """
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        if float(value).is_integer() and value >= _SEXAGESIMAL_FLOOR:
            log.warning(
                "homepage: ratio %r looks like a `a:b` that YAML read as a number "
                "(YAML reads `4:3` as 4*60+3 == 243); quote it or use a slash, e.g. "
                '"4/3"',
                value,
            )
            return None
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
