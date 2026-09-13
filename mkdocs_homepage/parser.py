"""Turn ``homepage`` fenced blocks in a Markdown document into :class:`Block`s.

The grammar is deliberately small, because everything about the widget is authored
by hand in a ``.md`` file:

```
homepage-<kind>          <- the information string, e.g. ```homepage-cards
<yaml props>             <- optional, a YAML mapping
---                      <- optional separator (a line with nothing but ---)
<markdown body>          <- optional, rendered with the site's own extensions
```

The split is unambiguous and cheap to explain:

* If the fence body contains a line that is exactly ``---``, everything above it
  is YAML props and everything below it is the Markdown body.  Use ``***`` if you
  need a horizontal rule inside the body.
* Otherwise the whole body is *either* props *or* prose.  Props are assumed when
  the first paragraph is nothing but ``key: value`` lines (plus their indented
  continuation lines); anything else is treated as prose.

A parser that guesses is a parser that surprises people, so the fallback rule only
ever fires on the first paragraph and every mis-parse is reported with a line
number rather than swallowed.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Iterator, Union

import yaml

from .util import as_bool

log = logging.getLogger("mkdocs.plugins.homepage")

FENCE_TOKEN = "homepage"

#: Canonical block kinds, in documentation order.
BLOCK_KINDS: tuple[str, ...] = (
    "hero",
    "cards",
    "showcase",
    "features",
    "testimonials",
    "logos",
    "image",
    "gallery",
    "split",
    "text",
    "stats",
    "steps",
    "links",
    "cta",
    "anim",
    "divider",
)

#: ``homepage-<alias>`` spellings that resolve to a canonical kind.
KIND_ALIASES: dict[str, str] = {
    "hero": "hero",
    "banner": "hero",
    "cover": "hero",
    "cards": "cards",
    "card": "cards",
    "grid": "cards",
    "tiles": "cards",
    "showcase": "showcase",
    "sections": "showcase",
    "rows": "showcase",
    "alternating": "showcase",
    "spotlight": "showcase",
    "features": "features",
    "feature": "features",
    "highlights": "features",
    "testimonials": "testimonials",
    "testimonial": "testimonials",
    "quotes": "testimonials",
    "reviews": "testimonials",
    "users": "testimonials",
    "logos": "logos",
    "logo": "logos",
    "brands": "logos",
    "clients": "logos",
    "trust": "logos",
    "sponsors": "logos",
    "image": "image",
    "img": "image",
    "figure": "image",
    "picture": "image",
    "gallery": "gallery",
    "carousel": "gallery",
    "slider": "gallery",
    "strip": "gallery",
    "split": "split",
    "columns": "split",
    "cols": "split",
    "side": "split",
    "text": "text",
    "prose": "text",
    "paragraph": "text",
    "note": "text",
    "stats": "stats",
    "numbers": "stats",
    "metrics": "stats",
    "counters": "stats",
    "steps": "steps",
    "timeline": "steps",
    "links": "links",
    "link": "links",
    "quicklinks": "links",
    "shortcuts": "links",
    "cta": "cta",
    "callout": "cta",
    "promo": "cta",
    "insiders": "cta",
    "sponsor": "cta",
    "anim": "anim",
    "animate": "anim",
    "animation": "anim",
    "motion": "anim",
    "divider": "divider",
    "hr": "divider",
    "rule": "divider",
    "space": "divider",
    "spacer": "divider",
}

#: ``text-align`` style keywords accepted by the ``align`` prop.
ALIGNMENTS = frozenset({"start", "left", "center", "right", "end", "justify"})

#: ``reveal`` animation keywords understood by the stylesheet.
REVEALS = frozenset({"fade", "up", "down", "left", "right", "zoom", "flip"})

#: Decorative background layers a block can opt into.
PATTERNS = frozenset({"aurora", "grid", "dots", "rays", "none"})

#: Values that mean "no decorative layer at all".  Shared by the normaliser and
#: the validator, which have to tell "explicitly none" from "not a pattern".
PATTERN_OPTOUT = frozenset({"", "none", "off", "false", "0", "plain"})

#: Named colour themes.  Each one only sets a hue; the stylesheet derives the
#: accent, tint, hairline and shadow from it, so a new theme is a one-line change.
THEMES: tuple[str, ...] = (
    "indigo",
    "blue",
    "cyan",
    "teal",
    "green",
    "lime",
    "amber",
    "orange",
    "deep-orange",
    "pink",
    "purple",
    "deep-purple",
    "blue-grey",
    "slate",
)

_ALIGN_CANON = {"left": "start", "right": "end"}

_OPEN_RE = re.compile(r"^(?P<indent> {0,3})(?P<fence>`{3,}|~{3,})(?P<info>.*)$")
_YAML_HEAD_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*\s*:")
_HR_RE = re.compile(r"^-{3,}[ \t]*$")
_PANEL_RE = re.compile(r"^(?:={3,}|\+{3,})[ \t]*$")
_INFO_TOKEN_RE = re.compile(r"[\s{(\[]")


class BlockError(Exception):
    """A malformed ``homepage`` fence.

    Raised at parse time for structural problems and at render time for missing
    required data; the Markdown extension decides whether to fail the build
    (``strict``) or to log a warning and drop in a visible error marker.
    """


@dataclass(frozen=True)
class Block:
    """One parsed ``homepage-*`` fence."""

    kind: str
    """Canonical kind, see :data:`BLOCK_KINDS`."""

    props: dict
    """YAML props, always a mapping (possibly empty)."""

    body: str
    """Markdown body, possibly empty."""

    line: int
    """1-based line number of the opening fence, for diagnostics."""

    info: str = ""
    """The raw information string, echoed back in error messages."""

    source: str | None = None
    """Source path of the containing page, when known."""

    issue: str | None = None
    """A fatal problem with this fence, reported instead of rendering it.

    The block is still returned -- rather than dropped -- so the page can show a
    visible marker at the exact spot, carrying the real cause.  Silently removing
    a block from a homepage is the worst possible failure mode.
    """

    def __str__(self) -> str:  # pragma: no cover - debugging aid
        return f"homepage {self.kind} block at line {self.line}"

    def get(self, *keys: str, default: Any = None) -> Any:
        for key in keys:
            value = self.props.get(key)
            if value is not None:
                return value
        return default


@dataclass(frozen=True)
class ParseIssue:
    """A non-fatal problem found while parsing."""

    message: str
    line: int
    source: str | None = None

    def format(self) -> str:
        where = f"{self.source}:{self.line}" if self.source else f"line {self.line}"
        return f"{where}: {self.message}"


def canonical_kind(token: str) -> str | None:
    """Resolve ``homepage-<token>`` to a canonical kind, or ``None``."""
    key = re.sub(r"[-_ ]+", "", token.strip().lower())
    return KIND_ALIASES.get(key)


def is_fence_info(info: str) -> bool:
    """True when a fence information string opens a homepage block."""
    token = _INFO_TOKEN_RE.split(info.strip(), 1)[0]
    token = token.lower()
    return token == FENCE_TOKEN or token.startswith(FENCE_TOKEN + "-") or token.startswith(
        FENCE_TOKEN + "_"
    )


def _is_close(line: str, char: str, minimum: int) -> bool:
    text = line.rstrip()
    indent = len(text) - len(text.lstrip(" "))
    if indent > 3:
        return False
    body = text[indent:]
    if not body or set(body) != {char}:
        return False
    return len(body) >= minimum


def _find_close(lines: list, start: int, char: str, minimum: int) -> int | None:
    for index in range(start, len(lines)):
        if _is_close(lines[index], char, minimum):
            return index
    return None


def top_level_fence_offset(body: str) -> int | None:
    """Line offset of a homepage fence that *body* opens at its own level.

    This is the signature of the one mistake that is genuinely hard to see: a
    forgotten closing fence.  The block then swallows everything up to the next
    ``` ``` ```, so the following blocks silently stop existing and the page just
    looks shorter than it should.

    Fences are tracked properly rather than matched with a regex, so a block that
    *demonstrates* the syntax inside a longer fence is not reported.
    """
    lines = body.split("\n")
    index = 0
    while index < len(lines):
        match = _OPEN_RE.match(lines[index])
        if match is None:
            index += 1
            continue
        fence = match.group("fence")
        info = match.group("info").strip()
        close = _find_close(lines, index + 1, fence[0], len(fence))
        if is_fence_info(info):
            return index
        if close is None:
            return None
        index = close + 1
    return None


def _looks_like_props(text: str) -> bool:
    """True when the first paragraph is nothing but ``key: value`` material."""
    paragraph = []
    for line in text.split("\n"):
        if not line.strip():
            break
        paragraph.append(line)
    if not paragraph:
        return False
    for line in paragraph:
        stripped = line.lstrip()
        if line[:1] in (" ", "\t") or stripped.startswith(("#", "-")):
            continue
        if not _YAML_HEAD_RE.match(stripped):
            return False
    return True


def _load_yaml(text: str) -> tuple[dict, str | None]:
    """Parse props; return ``(props, error)``."""
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as error:
        mark = getattr(error, "problem_mark", None)
        where = f" (YAML line {mark.line + 1})" if mark is not None else ""
        detail = getattr(error, "problem", None) or str(error)
        return {}, f"invalid YAML front matter{where}: {detail}"
    if data is None:
        return {}, None
    if not isinstance(data, dict):
        return {}, f"props must be a mapping of keys to values, got {type(data).__name__}"
    if not all(isinstance(key, str) for key in data):
        return {}, "props keys must be strings"
    return data, None


def split_props_body(text: str) -> tuple[str, str]:
    """Split a fence body into ``(props_text, body_text)`` without parsing either.

    Only the first ``---`` line counts, and only when it sits at column 0.
    """
    lines = text.split("\n")
    for index, line in enumerate(lines):
        if _HR_RE.match(line):
            return "\n".join(lines[:index]), "\n".join(lines[index + 1 :])
    return "", text


def parse_props(text: str) -> tuple[dict, str]:
    """Parse a fence body into ``(props, markdown_body)``.

    Raises :class:`BlockError` when a props region is present but malformed.
    """
    return _split_props_and_body(text)


def _split_props_and_body(text: str) -> tuple[dict, str]:
    """Decide how a fence body splits into props and Markdown."""
    lines = text.split("\n")
    for index, line in enumerate(lines):
        if _HR_RE.match(line):
            props, error = _load_yaml("\n".join(lines[:index]))
            if error:
                raise BlockError(error)
            return props, "\n".join(lines[index + 1 :])

    # No explicit separator: the whole body is either props or prose.
    if _looks_like_props(text):
        props, error = _load_yaml(text)
        if error:
            raise BlockError(error)
        return props, ""

    if not text.strip():
        return {}, ""

    props, error = _load_yaml(text)
    if error is None and props:
        # YAML parsed cleanly into a mapping even though the first paragraph did
        # not look like one.  Trust the mapping -- a body that happens to be valid
        # YAML shorthand is far more likely to be props than a stray paragraph --
        # but leave a trace, because this is the one guessing branch.
        log.debug("homepage: treated a non-prose-looking body as a props mapping")
        return props, ""
    return {}, text


def parse_block(
    info: str, body: str, line: int, source: str | None = None
) -> tuple[Block | None, list[ParseIssue]]:
    """Build a :class:`Block` from a fence's information string and body."""
    issues: list[ParseIssue] = []
    token = _INFO_TOKEN_RE.split(info.strip(), 1)[0]
    rest = token[len(FENCE_TOKEN) :].strip("-_ ")

    try:
        props, markdown_body = _split_props_and_body(body)
    except BlockError as error:
        # Keep the block, remember why it is broken.  Dropping it would make a
        # homepage quietly lose a section; the renderer turns `issue` into a
        # marker that names the offending line.
        issues.append(ParseIssue(str(error), line, source))
        return (
            Block(
                kind="unknown",
                props={},
                body=body,
                line=line,
                info=info,
                source=source,
                issue=str(error),
            ),
            issues,
        )

    declared = props.pop("type", None)
    kind = canonical_kind(rest) if rest else None
    if kind is None and declared:
        kind = canonical_kind(str(declared))

    nested = top_level_fence_offset(body)
    if nested is not None:
        issues.append(
            ParseIssue(
                "this block contains another homepage fence at its own level, which "
                "almost always means a closing ``` is missing above",
                line + 1 + nested,
                source,
            )
        )

    if kind is None:
        wanted = rest or (declared if declared else "")
        if wanted:
            message = (
                f"unknown block type {str(wanted)!r}; expected one of: " + ", ".join(BLOCK_KINDS)
            )
        else:
            message = (
                "missing block type; write ```homepage-<kind> where <kind> is one of: "
                + ", ".join(BLOCK_KINDS)
            )
        issues.append(ParseIssue(message, line, source))
        return (
            Block(
                kind="unknown",
                props=props,
                body=markdown_body,
                line=line,
                info=info,
                source=source,
                issue=message,
            ),
            issues,
        )

    theme = props.get("theme")
    if theme is not None and normalize_theme(theme) is None:
        issues.append(
            ParseIssue(
                f"unknown theme {theme!r}; inheriting the surrounding theme "
                "(available: " + ", ".join(THEMES) + ")",
                line,
                source,
            )
        )
        props["theme"] = None
    elif theme is not None:
        props["theme"] = normalize_theme(theme)

    pattern = props.get("pattern")
    if pattern is not None:
        # `none` is a documented value and normalises to "no pattern", which is
        # indistinguishable from an unknown keyword by the return value alone.
        # Without this test the one spelling everybody reaches for to *remove* a
        # pattern warned that it was not a pattern -- and the warning listed
        # `none` as one of the valid choices.
        normalized = normalize_pattern(pattern)
        if normalized is None and not is_pattern_optout(pattern):
            issues.append(
                ParseIssue(
                    f"unknown pattern {pattern!r}; expected one of: "
                    + ", ".join(sorted(PATTERNS)),
                    line,
                    source,
                )
            )
        props["pattern"] = normalized

    return (
        Block(kind=kind, props=props, body=markdown_body, line=line, info=info, source=source),
        issues,
    )


def split_blocks(text: str, source: str | None = None) -> list:
    """Split a document into ``str`` chunks and :class:`Block`s.

    Plain chunks keep their text unchanged, so a document with no homepage fences
    comes back as a single identical string.  Line endings are normalised to
    ``\\n`` first, exactly as :meth:`markdown.Markdown.convert` does, so the
    function behaves the same whether or not it is called through the extension.
    """
    if "\r" in text:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    segments: list = []
    pending: list[ParseIssue] = []
    index = 0
    plain_start = 0
    length = len(lines)

    while index < length:
        match = _OPEN_RE.match(lines[index])
        if match is None:
            index += 1
            continue

        fence = match.group("fence")
        char = fence[0]
        info = match.group("info").strip()
        if char == "`" and "`" in info:
            index += 1
            continue

        close = _find_close(lines, index + 1, char, len(fence))
        if close is None:
            if is_fence_info(info):
                pending.append(
                    ParseIssue(
                        f"unterminated {info or 'code'} fence: expected a closing "
                        f"{fence} before the end of the file",
                        index + 1,
                        source,
                    )
                )
            break

        if not is_fence_info(info):
            # A regular code fence.  Skip over it wholesale so that fence bodies
            # which *demonstrate* the syntax are never mistaken for real blocks.
            index = close + 1
            continue

        if plain_start < index:
            # `"\n".join(lines[a:b])` reproduces the text of those lines but not
            # the newline that terminated the last one -- and the fence starts
            # right after it.  Without the extra character the paragraph above a
            # block would lose its blank line and merge into it.
            segments.append("\n".join(lines[plain_start:index]) + "\n")
        block, issues = parse_block(info, "\n".join(lines[index + 1 : close]), index + 1, source)
        pending.extend(issues)
        if block is not None:
            segments.append(block)
        index = close + 1
        plain_start = index

    if plain_start < length:
        segments.append("\n".join(lines[plain_start:]))

    for issue in pending:
        log.warning("homepage: %s", issue.format())

    return segments


def split_panels(body: str) -> list[str]:
    """Split a ``split`` body into panels on ``===`` / ``+++`` separator lines."""
    lines = body.split("\n")
    panels: list[list[str]] = [[]]
    for line in lines:
        if _PANEL_RE.match(line):
            panels.append([])
        else:
            panels[-1].append(line)
    return ["\n".join(panel).strip("\n") for panel in panels]


def normalize_theme(value: Any) -> str | None:
    """Return a valid theme name, or ``None`` to inherit."""
    if value is None:
        return None
    name = str(value).strip().lower().replace("_", "-")
    aliases = {"grey": "blue-grey", "gray": "blue-grey", "bluegray": "blue-grey", "default": None}
    if name in aliases:
        return aliases[name]
    return name if name in THEMES else None


def normalize_reveal(value: Any) -> str | None:
    """Return a reveal keyword, or ``None`` for "no animation"."""
    if value is None:
        return None
    if isinstance(value, bool):
        return "up" if value else None
    text = str(value).strip().lower()
    if not text or text in {"none", "false", "off", "0"}:
        return None
    if text in {"true", "on", "yes", "1"}:
        return "up"
    if text in REVEALS:
        return text
    return None


def normalize_align(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    if text not in ALIGNMENTS:
        return None
    return _ALIGN_CANON.get(text, text)


def normalize_pattern(value: Any) -> str | None:
    """Return a decorative background keyword, or ``None`` for a plain surface."""
    if value is None:
        return None
    if isinstance(value, bool):
        return "aurora" if value else None
    text = str(value).strip().lower()
    if text in PATTERN_OPTOUT:
        return None
    return text if text in PATTERNS else None


def is_pattern_optout(value: Any) -> bool:
    """Whether *value* asks for **no** pattern, as opposed to naming a bad one.

    ``normalize_pattern`` answers both questions with ``None``, so a caller that
    wants to warn about a typo has to ask this separately.
    """
    if isinstance(value, bool):
        return True
    return str(value).strip().lower() in PATTERN_OPTOUT


def as_bool_prop(props: dict, key: str, default: bool = False) -> bool:
    return as_bool(props.get(key), default)


def iter_kinds() -> Iterator[str]:
    """Yield the canonical kinds (kept for docs tooling)."""
    yield from BLOCK_KINDS
