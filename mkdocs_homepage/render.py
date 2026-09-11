"""Render parsed blocks into Material-native HTML.

Two rules govern everything in here.

**Stay inside the theme.**  Colour, border and shadow come either from Material's
own custom properties (``--md-default-fg-color``, ``--md-default-fg-color--lightest``,
``--md-shadow-z2``, ...) or from a *hue* declared as a plain custom property that
the stylesheet derives into an accent, a tint and a hairline.  A block therefore
never names a colour, and both colour schemes keep working without a single
``[data-md-color-scheme]`` branch in the markup.

**Escape or render, never concatenate.**  Every value that lands in an attribute
or a text node goes through :func:`~mkdocs_homepage.util.esc`; every value that is
allowed to contain Markdown goes through the site's own
:class:`~mkdocs_homepage.converter.MarkdownRunner`, so a card and the page body
can never disagree about how a fragment renders.
"""

from __future__ import annotations

import html as _html
import re
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from .converter import MarkdownRunner
from .context import resolve_url
from .parser import (
    Block,
    BlockError,
    normalize_align,
    normalize_pattern,
    normalize_reveal,
    normalize_theme,
    split_panels,
)
from .svg import icon
from .util import (
    as_bool,
    as_list,
    css_class,
    css_length,
    css_ratio,
    esc,
    first_of,
    safe_url,
    split_pipe,
)

#: Every block carries `.md-home`; the kind adds `.md-home--<kind>`.
ROOT = "md-home"

#: Animation names accepted by the ``anim`` block.
ANIM_EFFECTS = ("float", "pulse", "shimmer", "gradient", "marquee", "typetext")

#: Shapes for the ``features`` icon bubble.
ICON_STYLES = ("plain", "soft", "circle", "square", "solid")

#: Decorative frames a figure can wear.  One vocabulary, used by every block that
#: shows an image, so `frame: browser` means the same thing everywhere.
FRAME_STYLES = ("browser", "window", "screenshot", "shadow", "glow")


def as_frames(value: Any, *extra: Any) -> list:
    """Normalise the frame-ish props into a de-duplicated list of known frames.

    Three different props can ask for a frame -- ``frame``, ``image_frame`` and
    the ``shadow`` / ``glow`` booleans -- and they all end up as classes on the
    figure.  Keeping the vocabulary in one place is what makes `frame: browser`
    mean the same thing in a hero, a showcase row and a plain image.
    """
    names = []
    for item in as_list(value) + list(extra):
        if item is None or isinstance(item, bool):
            continue
        for part in str(item).replace(",", " ").split():
            name = part.strip().lower()
            if name in FRAME_STYLES and name not in names:
                names.append(name)
    return names

#: Kinds whose children get a staggered scroll-in when ``reveal`` is left on
#: ``auto``.  A one-off prose block has nothing to stagger, so it stays still.
STAGGER_KINDS = frozenset({"cards", "features", "stats", "steps", "links", "logos", "testimonials"})

#: Kinds that are a decorated band rather than an inset block, so ``pattern``
#: applies to them by default and they get the wider vertical rhythm.
BAND_KINDS = frozenset({"hero", "cta"})

#: Prop names that carry a URL, used by the link audit in the test suite.
LINK_PROPS = ("link", "url", "href", "src", "image", "img", "cover", "avatar", "logo")

#: Milliseconds between two staggered items, capped so a long list does not make
#: the last card wait for seconds.
STAGGER_STEP = 55
STAGGER_MAX = 8

_ATTR_RE = re.compile(r'([:\w-]+)\s*=\s*"([^"]*)"')
_IMG_RE = re.compile(r"<img\b[^>]*/?>", re.I)
_LINKED_IMG_RE = re.compile(r'<a\b[^>]*href="([^"]*)"[^>]*>\s*(<img\b[^>]*/?>)\s*</a>', re.I)
_NUMBER_RE = re.compile(r"^(?P<prefix>[^\d\s+-]*)\s*(?P<number>[+-]?[\d,]*\.?\d+)\s*(?P<suffix>.*)$")
_BARE_NUMBER_RE = re.compile(r"^\d+(?:\.\d+)?$")
_TRACK_TOKEN_RE = re.compile(
    r"^(?:auto|min-content|max-content|\d+(?:\.\d+)?(?:fr|px|em|rem|%|ch|vw|vh)?)$"
)
_INT_RE = re.compile(r"^\d+$")
_TAGS_RE = re.compile(r"<[^>]+>")


# ---------------------------------------------------------------------------
# prop coercion
# ---------------------------------------------------------------------------
def as_item(value: Any, fields: Sequence[str]) -> dict:
    """Coerce a list item into a mapping.

    Mapping items are taken as they are.  A plain string is split on ``|`` and
    zipped onto *fields*, which is what makes the compact form work::

        cards:
          - 使用指南 | /guide/ | 从一个空目录开始 | rocket-launch-outline
    """
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    if value is None:
        return {}
    if isinstance(value, str):
        parts = split_pipe(value)
        return {name: part for name, part in zip(fields, parts) if part}
    return {}


def as_items(value: Any, fields: Sequence[str]) -> list:
    """Coerce a list prop into a list of mappings, dropping empty entries."""
    return [item for item in (as_item(raw, fields) for raw in as_list(value)) if item]


def as_columns(value: Any) -> dict:
    """Normalise the ``columns`` prop into ``{"--md-home-cols": N}``.

    The value is a *maximum*: the stylesheet derives the minimum track size from
    it, so `columns: 3` fills with three columns when they fit and quietly drops
    to two or one when they do not.  A mapping is accepted and collapsed to its
    widest meaningful entry, because there is nothing left for a breakpoint to
    say once the grid is intrinsic.
    """
    if value is None:
        return {}
    if isinstance(value, Mapping):
        for key in ("base", "default", "lg", "md", "sm", "xs"):
            raw = value.get(key)
            if raw is not None and _INT_RE.match(str(raw).strip()):
                return {"--md-home-cols": int(raw)}
        return {}
    if _INT_RE.match(str(value).strip()):
        return {"--md-home-cols": int(value)}
    return {}


def as_tracks(value: Any) -> str | None:
    """Validate the ``ratio`` prop into a ``grid-template-columns`` fragment.

    Bare numbers become ``fr`` tracks, so ``ratio: 1.2 1`` reads naturally.  Any
    token that is not a track size aborts the whole value rather than being passed
    through -- this string ends up inside a style attribute.
    """
    if value is None:
        return None
    if isinstance(value, str):
        tokens = re.split(r"[|/\s]+", value.strip())
    elif isinstance(value, Sequence):
        tokens = [str(item).strip() for item in value]
    else:
        return None

    tracks = []
    for token in tokens:
        token = token.strip().lower()
        if not token:
            continue
        if not _TRACK_TOKEN_RE.match(token):
            return None
        tracks.append(token + "fr" if _BARE_NUMBER_RE.match(token) else token)
    return " ".join(tracks) if tracks else None


def as_number(value: Any) -> float | None:
    """Best-effort float, or ``None`` (used to keep unitless CSS numbers safe)."""
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def number_parts(value: Any) -> tuple[str, str, str] | None:
    """Split ``"98.6%"`` into ``("", "98.6", "%")``; ``None`` when not numeric."""
    if isinstance(value, bool) or value is None:
        return None
    match = _NUMBER_RE.match(str(value).strip())
    if not match:
        return None
    number = match.group("number").replace(",", "")
    try:
        float(number)
    except ValueError:
        return None
    return match.group("prefix"), number, match.group("suffix")


def style_attr(pairs: Mapping[str, Any]) -> str:
    """Build a ``style="..."`` attribute out of ``{css-variable: value}`` pairs.

    A value must be a length, a bare number, an aspect ratio or a
    :class:`Validated` string.  Everything else is dropped rather than passed
    through, so a prop can never smuggle a second declaration or a ``;`` into the
    attribute.  ``Validated`` is the single, greppable exception.
    """
    declarations = []
    for name, value in pairs.items():
        if value is None or value == "":
            continue
        if isinstance(value, Validated):
            text = str(value)
        elif isinstance(value, (int, float)):
            text = str(value)
        else:
            stripped = str(value).strip()
            text = css_length(stripped) or css_ratio(stripped)
        if text:
            declarations.append(f"{name}:{text};")
    return f' style="{"".join(declarations)}"' if declarations else ""


class Validated(str):
    """A style value that has already been checked and may be emitted verbatim."""


def url_attrs(props: Mapping[str, Any], url: Any, *, extra: str = "") -> str:
    """Build the attributes for a link, including safe external-link handling."""
    resolved = safe_url(resolve_url(url))
    parts = []
    if resolved is not None:
        parts.append(f'href="{esc(resolved)}"')
        external = props.get("external")
        is_external = bool(external) or (
            external is None and resolved.startswith(("http://", "https://", "//"))
        )
        if is_external:
            parts.append('target="_blank"')
            parts.append('rel="noopener"')
    if extra:
        parts.append(extra.strip())
    return " ".join(parts)


def classes(*values: Any) -> str:
    """Merge class names, sanitising and de-duplicating them."""
    collected: list[str] = []
    for value in values:
        if not value:
            continue
        text = css_class(value)
        if text:
            collected.extend(text.split())
    return " ".join(dict.fromkeys(collected))


# ---------------------------------------------------------------------------
# shared presentation
# ---------------------------------------------------------------------------
@dataclass
class Presentation:
    """Presentation props understood by every block."""

    theme: str | None = None
    classes: str = ""
    ident: str | None = None
    width: str | None = None
    background: str | None = None
    align: str | None = None
    reveal: str | None = None
    tilt: str | None = None
    pattern: str | None = None
    gradient: bool = False

    @classmethod
    def of(cls, block: Block, options: Mapping[str, Any]) -> "Presentation":
        props = block.props

        if "reveal" in props:
            reveal = normalize_reveal(props.get("reveal"))
        else:
            default = options.get("reveal", "auto")
            if default is True or str(default).strip().lower() in ("true", "auto"):
                reveal = "up" if block.kind in STAGGER_KINDS else None
            else:
                reveal = normalize_reveal(default)

        tilt = None
        if options.get("tilt", True):
            strength = props.get("tilt")
            if strength is None:
                strength = options.get("tilt_strength", 6)
            number = as_number(strength)
            if number is None:
                tilt = str(strength) if strength else None
            elif number != 0:
                tilt = f"{number:g}"

        pattern = normalize_pattern(props.get("pattern"))
        if pattern is None and "pattern" not in props and block.kind in BAND_KINDS:
            # A hero or a call to action is a band, not a card: it reads better
            # with a little atmosphere behind it, and `pattern: none` opts out.
            pattern = "aurora" if options.get("pattern", True) else None

        return cls(
            theme=normalize_theme(props.get("theme")),
            classes=css_class(props.get("class") or props.get("classes")),
            ident=props.get("id") or props.get("anchor"),
            width=str(props["width"]).strip().lower() if props.get("width") else None,
            background=str(props["background"]).strip().lower() if props.get("background") else None,
            align=normalize_align(props.get("align")),
            reveal=reveal,
            tilt=tilt,
            pattern=pattern,
            gradient=as_bool(props.get("gradient"), False),
        )

    def wrapper_classes(self, *extra: Any) -> str:
        names = [ROOT]
        if self.theme:
            names.append(f"{ROOT}--theme-{self.theme}")
        if self.background:
            names.append(f"{ROOT}--bg-{self.background}")
        if self.width:
            names.append(f"{ROOT}--{self.width}")
        if self.align:
            names.append(f"{ROOT}--align-{self.align}")
        if self.pattern:
            names.append(f"{ROOT}--pattern-{self.pattern}")
        if self.gradient:
            names.append(f"{ROOT}--gradient")
        names.append(self.classes)
        return classes(*names, *extra)

    def wrapper_attrs(self, block: Block) -> str:
        bits = [f'data-home-block="{esc(block.kind)}"']
        if self.ident:
            bits.append(f'id="{esc(self.ident)}"')
        # A staggered block animates its children, not itself: revealing the
        # container *and* each item makes the whole grid arrive twice.
        if self.reveal and block.kind not in STAGGER_KINDS:
            bits.append(f'data-home-reveal="{esc(self.reveal)}"')
        return " ".join(bits)


# ---------------------------------------------------------------------------
# renderer
# ---------------------------------------------------------------------------
class BlockRenderer:
    """Turn :class:`Block`s into HTML."""

    def __init__(self, runner: MarkdownRunner, options: Mapping[str, Any] | None = None) -> None:
        self.runner = runner
        self.options = dict(options or {})

    # -- small helpers ---------------------------------------------------
    def inline(self, value: Any) -> str:
        return "" if value is None else self.runner.inline(str(value))

    def block(self, value: Any) -> str:
        return "" if not value else self.runner.convert(str(value))

    def _presentation(self, block: Block) -> Presentation:
        return Presentation.of(block, self.options)

    def grid_attrs(self, block: Block) -> str:
        """Attributes for a grid container: the column count and its marker.

        ``data-home-cols`` is the switch the stylesheet needs, because
        ``repeat(auto-fit, minmax(0, 1fr))`` collapses to zero-width tracks -- an
        explicit count and an intrinsic auto-fit grid need different minimum
        track sizes, and only the markup knows which one this is.
        """
        columns = as_columns(block.props.get("columns"))
        variables = dict(columns)
        minimum = first_of(block.props, "min_cols", "min_column", "card_width")
        if minimum:
            variables["--md-home-min"] = minimum
        return style_attr(variables) + (" data-home-cols" if columns else "")

    def _item_attrs(self, presentation: Presentation, index: int) -> str:
        """Reveal attributes for one grid item (the stagger lives in the style)."""
        if not presentation.reveal:
            return ""
        delay = min(index, STAGGER_MAX) * STAGGER_STEP
        return (
            f' data-home-reveal="{esc(presentation.reveal)}"'
            f' data-home-index="{index}"'
            f' style="--md-home-reveal-delay:{delay}ms"'
        )

    def _wrap(
        self,
        block: Block,
        inner: str,
        presentation: Presentation,
        *extra_classes: Any,
        tag: str = "section",
        style: str = "",
        attrs: str = "",
    ) -> str:
        # `md-home--<kind>` is public API: it is how a site targets one kind of
        # block without guessing at the inner markup.
        classes_ = presentation.wrapper_classes(f"{ROOT}--{block.kind}", *extra_classes)
        attributes = [presentation.wrapper_attrs(block)]
        if attrs:
            attributes.append(attrs.strip())
        joined = " ".join(part for part in attributes if part)
        return f'<{tag} class="{classes_}" {joined}{style}>{inner}</{tag}>'

    def _header(self, block: Block, presentation: Presentation, default_level: int = 2) -> str:
        props = block.props
        eyebrow = first_of(props, "eyebrow", "kicker", "overline")
        title = first_of(props, "title", "heading")
        subtitle = first_of(props, "subtitle", "lead", "description")
        if not (eyebrow or title or subtitle):
            return ""

        level = props.get("level")
        try:
            level = int(level)
        except (TypeError, ValueError):
            level = default_level
        level = min(max(level, 1), 6)

        parts = []
        if eyebrow:
            parts.append(f'<p class="md-home__eyebrow">{self.inline(eyebrow)}</p>')
        if title:
            parts.append(f'<h{level} class="md-home__title">{self.inline(title)}</h{level}>')
        if subtitle:
            parts.append(f'<p class="md-home__subtitle">{self.inline(subtitle)}</p>')
        centre = " md-home__header--center" if presentation.align == "center" else ""
        return f'<header class="md-home__header{centre}">' + "".join(parts) + "</header>"

    def _figure(
        self,
        image: Mapping[str, Any],
        *,
        ratio: str | None = None,
        zoom: bool = True,
        frames: Any = None,
    ) -> str:
        source = first_of(image, "src", "image", "path", "url")
        if not source:
            raise BlockError("an image needs a `src`")
        alt = first_of(image, "alt", "text", default="")
        caption = first_of(image, "caption", default="")
        link = first_of(image, "link", "href")

        markup = (
            f'<img src="{esc(safe_url(resolve_url(source)))}" alt="{esc(alt)}"'
            ' loading="lazy" decoding="async">'
        )
        clickable = link or (
            zoom and self.options.get("lightbox", True) and as_bool(image.get("zoom"), True)
        )
        if clickable:
            target = link or source
            props = image if link else {"external": False}
            marker = "" if link else " data-home-zoom"
            markup = (
                f'<a class="md-home__zoom" {url_attrs(props, target)}{marker}>{markup}</a>'
            )

        # Frames are modifiers of the figure rather than of whatever happens to
        # contain it, so the hero, the showcase, a card cover and a plain image
        # block all get the identical treatment from one set of rules.
        figure_classes = classes(
            "md-home__figure",
            *[f"md-home__figure--{name}" for name in as_frames(frames)],
        )
        body = f'<figure class="{figure_classes}"{style_attr({"--md-home-ratio": ratio})}>'
        body += markup
        if caption:
            body += f'<figcaption class="md-home__caption">{self.inline(caption)}</figcaption>'
        return body + "</figure>"

    def _actions(self, items: Iterable[Mapping[str, Any]]) -> str:
        parts = []
        for item in items:
            text = first_of(item, "text", "title", "label")
            link = first_of(item, "link", "url", "href")
            if not text and not link:
                continue
            kind = str(first_of(item, "style", "variant", default="secondary")).strip().lower()
            variant = "md-button--primary" if kind in ("primary", "solid", "filled") else ""
            glyph = icon(item["icon"]) if item.get("icon") else ""
            label = self.inline(text) if text else ""
            button = classes("md-button", "md-home__action", variant)
            inner = f'{glyph}<span class="md-home__action-text">{label}</span>'
            if link:
                parts.append(f'<a class="{button}" {url_attrs(item, link)}>{inner}</a>')
            else:
                parts.append(f'<span class="{button}">{inner}</span>')
        return "".join(parts)

    # -- dispatch --------------------------------------------------------
    def render(self, block: Block) -> str:
        handler = getattr(self, f"_{block.kind}", None)
        if handler is None:  # pragma: no cover - the parser rejects unknown kinds
            raise BlockError(f"no renderer for block kind {block.kind!r}")
        return handler(block)

    # -- kinds -----------------------------------------------------------
    def _hero(self, block: Block) -> str:
        props = block.props
        presentation = self._presentation(block)
        image = first_of(props, "image", "img", "background_image")

        panes = [self._header(block, presentation, default_level=1)]
        body = self.block(block.body)
        if body:
            panes.append(f'<div class="md-home__lead md-home__prose md-typeset">{body}</div>')
        actions = self._actions(as_items(props.get("actions"), ("text", "link", "style")))
        if actions:
            panes.append(f'<div class="md-home__actions">{actions}</div>')
        note = first_of(props, "note", "fineprint", "footnote")
        if note:
            panes.append(f'<p class="md-home__note">{self.inline(note)}</p>')
        highlights = self._highlights(props.get("highlights"), presentation)
        if highlights:
            panes.append(highlights)
        text_pane = f'<div class="md-home__hero-body">{"".join(panes)}</div>'

        if not image:
            return self._wrap(
                block,
                f'<div class="md-home__hero md-home__hero--solo">{text_pane}</div>',
                presentation,
            )

        media = self._figure(
            as_item(image, ("src", "caption", "alt")),
            ratio=str(props.get("ratio") or "16/10"),
            zoom=False,
            frames=as_frames(
                first_of(props, "image_frame", "frame", "art_frame"),
                "shadow" if as_bool(props.get("shadow"), True) else None,
                "glow" if as_bool(props.get("glow"), False) else None,
            ),
        )
        media_pane = f'<div class="md-home__hero-media">{media}</div>'
        mirror = as_bool(first_of(props, "mirror", "reverse"), False)
        layout = media_pane + text_pane if mirror else text_pane + media_pane
        return self._wrap(
            block,
            f'<div class="md-home__hero">{layout}</div>',
            presentation,
            "md-home__hero--mirror" if mirror else "",
        )

    def _highlights(self, raw: Any, presentation: Presentation) -> str:
        """The small inline stats a hero can carry (``0 dependencies · 2 schemes``)."""
        items = as_items(raw, ("value", "label", "icon"))
        if not items:
            return ""
        cells = []
        for item in items:
            value = first_of(item, "value", "text", "title")
            label = first_of(item, "label", "desc")
            glyph = f'<span class="md-home__highlight-icon">{icon(item["icon"])}</span>' if item.get("icon") else ""
            cells.append(
                '<li class="md-home__highlight">'
                f"{glyph}"
                f'<span class="md-home__highlight-value">{self.inline(value)}</span>'
                f'<span class="md-home__highlight-label">{self.inline(label)}</span></li>'
            )
        return f'<ul class="md-home__highlights" role="list">{"".join(cells)}</ul>'

    def _cards(self, block: Block) -> str:
        props = block.props
        presentation = self._presentation(block)
        cards = as_items(first_of(props, "cards", "items"), ("title", "link", "desc", "icon"))
        if not cards:
            raise BlockError("a cards block needs a `cards:` list with at least one item")

        style = str(first_of(props, "card_style", "style", default="elevated")).strip().lower()
        if style not in ("elevated", "outlined", "filled", "glass", "plain"):
            style = "elevated"
        cells = "".join(
            self._card(block, presentation, card, index) for index, card in enumerate(cards)
        )
        grid = (
            f'<ul class="md-home__grid md-home__cards md-home__cards--{esc(style)}"'
            f'{self.grid_attrs(block)} role="list">{cells}</ul>'
        )
        return self._wrap(block, self._header(block, presentation) + grid, presentation)

    def _card(
        self, block: Block, presentation: Presentation, card: Mapping[str, Any], index: int
    ) -> str:
        theme = normalize_theme(card.get("theme"))
        link = first_of(card, "link", "url", "href")
        title = first_of(card, "title", "heading")
        desc = first_of(card, "desc", "description", "text")
        meta = first_of(card, "meta", "note")
        badge = first_of(card, "badge", "tag", "label")
        icon_name = card.get("icon")
        image = first_of(card, "image", "img", "cover")

        cell_classes = ["md-home__cell"]
        span = card.get("span") or card.get("cols")
        if _INT_RE.match(str(span or "")):
            cell_classes.append(f"md-home__cell--span{int(span)}")
        if as_bool(card.get("featured"), False):
            cell_classes.append("md-home__cell--featured")

        card_classes = classes(
            "md-home__card",
            "md-home__card--ring",
            f"{ROOT}--theme-{theme}" if theme else "",
            css_class(card.get("class")),
        )
        attrs = []
        if presentation.tilt:
            attrs.append(f'data-home-tilt="{esc(presentation.tilt)}"')

        parts = []
        if image:
            parts.append(
                '<span class="md-home__card-cover">'
                + self._figure(
                    as_item(image, ("src", "caption", "alt")),
                    ratio=str(
                        first_of(card, "ratio", default=None)
                        or block.props.get("ratio")
                        or "16/9"
                    ),
                    zoom=False,
                )
                + "</span>"
            )

        if icon_name or badge:
            # The icon labels the card only when there is no title to do it.
            icon_label = None if title else (str(first_of(card, "alt", default="")) or "图标")
            glyph = (
                f'<span class="md-home__card-icon">{icon(icon_name, label=icon_label)}</span>'
                if icon_name
                else ""
            )
            mark = f'<span class="md-home__badge">{self.inline(badge)}</span>' if badge else ""
            parts.append(f'<span class="md-home__card-head">{glyph}{mark}</span>')

        if title:
            parts.append(f'<span class="md-home__card-title">{self.inline(title)}</span>')
        if desc:
            parts.append(f'<span class="md-home__card-desc">{self.inline(desc)}</span>')

        tags = as_list(card.get("tags"))
        if tags:
            chips = "".join(f"<span>{self.inline(tag)}</span>" for tag in tags if tag)
            parts.append(f'<span class="md-home__card-tags">{chips}</span>')
        if meta:
            parts.append(f'<span class="md-home__card-meta">{self.inline(meta)}</span>')
        if link:
            text = self.inline(first_of(card, "link_text", default=None) or "查看")
            parts.append(
                f'<span class="md-home__card-foot"><span>{text}</span>{icon("arrow-right")}</span>'
            )

        inner = (
            '<span class="md-home__card-glow" aria-hidden="true"></span>'
            f'<span class="md-home__card-inner">{"".join(parts)}</span>'
        )
        if link:
            element = f'<a class="{card_classes}" {url_attrs(card, link)} {" ".join(attrs)}>{inner}</a>'
        else:
            element = f'<span class="{card_classes}" {" ".join(attrs)}>{inner}</span>'
        return (
            f'<li class="{classes(*cell_classes)}"{self._item_attrs(presentation, index)}>'
            f"{element}</li>"
        )

    def _showcase(self, block: Block) -> str:
        """Alternating image/text rows -- the pattern a product page is built from.

        Each row is one claim with one picture, and the sides alternate so the eye
        zig-zags down the page.  A per-row ``reverse`` overrides the alternation,
        and the whole set can be flipped with ``reverse`` on the block.
        """
        props = block.props
        presentation = self._presentation(block)
        rows = as_items(
            first_of(props, "showcase", "items", "sections"),
            ("title", "image", "desc", "link"),
        )
        if not rows:
            raise BlockError("a showcase block needs a `showcase:` list with at least one item")

        alternate = as_bool(props.get("alternate"), True)
        base_reverse = as_bool(props.get("reverse"), False)
        link_text = first_of(props, "link_text", default="了解更多")
        ratio = str(props.get("ratio") or "16/10")

        rendered = []
        for index, row in enumerate(rows):
            theme = normalize_theme(row.get("theme"))
            image = first_of(row, "image", "img", "src", "cover")
            if not image:
                raise BlockError(f"showcase item {index + 1} needs an `image`")
            reverse = as_bool(row.get("reverse"), alternate and index % 2 == 1)
            if base_reverse:
                reverse = not reverse

            panes = []
            eyebrow = first_of(row, "eyebrow", "kicker")
            if eyebrow:
                panes.append(f'<p class="md-home__eyebrow">{self.inline(eyebrow)}</p>')
            title = first_of(row, "title", "heading")
            if title:
                panes.append(f'<h3 class="md-home__showcase-title">{self.inline(title)}</h3>')
            desc = first_of(row, "desc", "description", "text")
            if desc:
                panes.append(f'<p class="md-home__showcase-desc">{self.inline(desc)}</p>')

            bullets = as_items(row.get("features") or row.get("bullets"), ("text", "desc", "icon"))
            if bullets:
                marks = "".join(
                    '<li class="md-home__bullet">'
                    f'<span class="md-home__bullet-icon">{icon(first_of(bullet, "icon", default="check-circle-outline") or "check-circle-outline")}</span>'
                    f'<span>{self.inline(first_of(bullet, "text", "desc", "title"))}</span></li>'
                    for bullet in bullets
                )
                panes.append(f'<ul class="md-home__bullets" role="list">{marks}</ul>')

            link = first_of(row, "link", "url", "href")
            if link:
                text = self.inline(first_of(row, "link_text", default=None) or link_text)
                panes.append(
                    f'<a class="md-home__more" {url_attrs(row, link)}>'
                    f'<span>{text}</span>{icon("arrow-right")}</a>'
                )

            media = self._figure(
                as_item(row, ("image", "caption", "alt")),
                ratio=str(row.get("ratio") or ratio),
                zoom=as_bool(row.get("zoom"), False),
                frames=as_frames(
                    row.get("frame"),
                    "shadow" if as_bool(row.get("shadow"), True) else None,
                    "glow" if as_bool(row.get("glow"), False) else None,
                ),
            )
            media_pane = f'<div class="md-home__showcase-media">{media}</div>'
            body_pane = f'<div class="md-home__showcase-body">{"".join(panes)}</div>'
            row_classes = classes(
                "md-home__showcase-row",
                "md-home__showcase-row--reverse" if reverse else "",
                f"{ROOT}--theme-{theme}" if theme else "",
            )
            rendered.append(
                f'<div class="{row_classes}">{media_pane + body_pane if reverse else body_pane + media_pane}</div>'
            )

        listing = f'<div class="md-home__showcase">{"".join(rendered)}</div>'
        return self._wrap(block, self._header(block, presentation) + listing, presentation)

    def _testimonials(self, block: Block) -> str:
        props = block.props
        presentation = self._presentation(block)
        items = as_items(
            first_of(props, "testimonials", "items", "quotes"), ("quote", "name", "role", "avatar")
        )
        if not items:
            raise BlockError("a testimonials block needs a `testimonials:` list with at least one item")

        style = str(props.get("style") or "cards").strip().lower()
        if style not in ("cards", "quote", "plain"):
            style = "cards"
        show_rating = as_bool(props.get("rating"), False)

        cells = []
        for index, item in enumerate(items):
            theme = normalize_theme(item.get("theme"))
            quote = first_of(item, "quote", "text", "desc")
            if not quote:
                raise BlockError(f"testimonial {index + 1} needs a `quote`")
            name = first_of(item, "name", "title", "author")
            role = first_of(item, "role", "desc", "position")
            avatar = first_of(item, "avatar", "image", "img", "photo")
            link = first_of(item, "link", "url", "href")

            authority = self.inline(name)
            if link and name:
                authority = f'<a class="md-home__quote-link" {url_attrs(item, link)}>{self.inline(name)}</a>'

            mark = icon("format-quote-open") if style != "plain" else ""
            rating = ""
            if show_rating:
                stars = "".join(icon("star") for _ in range(5))
                rating = f'<span class="md-home__quote-rating" aria-hidden="true">{stars}</span>'

            figure = ""
            if avatar:
                figure = (
                    '<span class="md-home__quote-avatar">'
                    f'<img src="{esc(safe_url(resolve_url(avatar)))}" alt="{esc(name or "")}"'
                    ' loading="lazy" decoding="async"></span>'
                )

            byline = (
                '<figcaption class="md-home__quote-by">'
                f"{figure}<span class=\"md-home__quote-meta\">"
                f'<span class="md-home__quote-name">{authority}</span>'
                f'<span class="md-home__quote-role">{self.inline(role)}</span>'
                "</span></figcaption>"
            )
            cells.append(
                f'<li class="{classes("md-home__testimonial", f"{ROOT}--theme-{theme}" if theme else "")}">'
                f'<figure class="md-home__quote md-home__quote--{esc(style)}">'
                f'<span class="md-home__quote-mark" aria-hidden="true">{mark}</span>'
                f"{rating}"
                f'<blockquote class="md-home__quote-body md-home__prose md-typeset">{self.block(quote)}</blockquote>'
                f"{byline}</figure></li>"
            )

        grid = (
            f'<ul class="md-home__grid md-home__testimonials md-home__testimonials--{esc(style)}"'
            f'{self.grid_attrs(block)} role="list">{"".join(cells)}</ul>'
        )
        return self._wrap(block, self._header(block, presentation) + grid, presentation)

    def _logos(self, block: Block) -> str:
        """A "trusted by" row.

        Brand marks come from the bundled Simple Icons set (``simple/github``),
        because MDI has almost none of them.  Entries may equally be images, which
        is what a company with its own logo file wants.
        """
        props = block.props
        presentation = self._presentation(block)
        items = as_items(
            first_of(props, "logos", "items", "brands"), ("icon", "name", "link", "desc")
        )
        if not items:
            raise BlockError(
                "a logos block needs a `logos:` list, e.g. `- simple/github | GitHub | https://github.com`"
            )

        style = str(props.get("style") or "row").strip().lower()
        if style not in ("row", "grid", "marquee"):
            style = "row"
        colored = as_bool(props.get("colored"), False)
        caption = first_of(props, "caption", "note", "text")

        cells = []
        for index, item in enumerate(items):
            name = first_of(item, "name", "title", "text")
            link = first_of(item, "link", "url", "href")
            image = first_of(item, "image", "img", "src")
            mark = (
                f'<img src="{esc(safe_url(resolve_url(image)))}" alt="{esc(name or "")}"'
                ' loading="lazy" decoding="async">'
                if image
                else icon(item.get("icon"), label=name or None)
            )
            label = f'<span class="md-home__logo-name">{self.inline(name)}</span>' if name else ""
            inner = f'<span class="md-home__logo-mark">{mark}</span>{label}'
            classes_ = "md-home__logo"
            if link:
                cells.append(
                    f'<li class="md-home__logo-item"><a class="{classes_}" '
                    f'{url_attrs(item, link)}>{inner}</a></li>'
                )
            else:
                cells.append(
                    f'<li class="md-home__logo-item"><span class="{classes_}" '
                    f'data-home-index="{index}">{inner}</span></li>'
                )

        row = f'<ul class="md-home__logos-list" role="list">{"".join(cells)}</ul>'
        if style == "marquee":
            row = (
                '<div class="md-home__marquee md-home__marquee--logos">'
                '<div class="md-home__marquee-track">'
                f'<div class="md-home__marquee-item">{row}</div>'
                f'<div class="md-home__marquee-item" aria-hidden="true">{row}</div>'
                "</div></div>"
            )

        wrapper = (
            f'<div class="md-home__logos md-home__logos--{esc(style)}'
            f'{" md-home__logos--colored" if colored else ""}"'
            f'{style_attr({"--md-home-logo-size": props.get("size")})}>{row}</div>'
        )
        text = f'<p class="md-home__logos-caption">{self.inline(caption)}</p>' if caption else ""
        return self._wrap(
            block, self._header(block, presentation) + text + wrapper, presentation
        )

    def _cta(self, block: Block) -> str:
        """A closing call to action: a centred, decorated band."""
        props = block.props
        presentation = self._presentation(block)
        image = first_of(props, "image", "img")

        panes = [self._header(block, presentation, default_level=2)]
        body = self.block(block.body)
        if body:
            panes.append(f'<div class="md-home__lead md-home__prose md-typeset">{body}</div>')
        actions = self._actions(as_items(props.get("actions"), ("text", "link", "style")))
        if actions:
            panes.append(f'<div class="md-home__actions">{actions}</div>')
        note = first_of(props, "note", "fineprint", "footnote")
        if note:
            panes.append(f'<p class="md-home__note">{self.inline(note)}</p>')

        inner = f'<div class="md-home__cta-body">{"".join(panes)}</div>'
        if image:
            inner = (
                '<div class="md-home__cta-art">'
                + self._figure(as_item(image, ("src", "caption", "alt")), ratio=str(props.get("ratio") or "1/1"), zoom=False)
                + "</div>"
                + inner
            )
        centred = presentation.align in (None, "center")
        return self._wrap(
            block,
            f'<div class="md-home__cta">{inner}</div>',
            presentation,
            "md-home__cta--centred" if centred else "",
        )

    def _features(self, block: Block) -> str:
        props = block.props
        presentation = self._presentation(block)
        features = as_items(first_of(props, "features", "items"), ("title", "desc", "icon", "link"))
        if not features:
            raise BlockError("a features block needs a `features:` list with at least one item")

        icon_style = str(first_of(props, "icon_style", "style", default="soft")).strip().lower()
        if icon_style not in ICON_STYLES:
            icon_style = "soft"

        cells = []
        for index, feature in enumerate(features):
            theme = normalize_theme(feature.get("theme"))
            link = first_of(feature, "link", "url", "href")
            title = first_of(feature, "title", "heading")
            desc = first_of(feature, "desc", "description", "text")

            parts = []
            if feature.get("icon"):
                parts.append(f'<span class="md-home__feature-icon">{icon(feature["icon"])}</span>')
            if title:
                parts.append(f'<p class="md-home__feature-title">{self.inline(title)}</p>')
            if desc:
                parts.append(f'<p class="md-home__feature-desc">{self.inline(desc)}</p>')
            inner = "".join(parts)

            item_classes = classes(
                "md-home__feature",
                f"md-home__feature--icon-{icon_style}",
                f"{ROOT}--theme-{theme}" if theme else "",
                css_class(feature.get("class")),
            )
            if link:
                inner = f'<a class="md-home__feature-link" {url_attrs(feature, link)}>{inner}</a>'
            else:
                inner = f'<span class="md-home__feature-link">{inner}</span>'
            cells.append(
                f'<li class="{item_classes}"{self._item_attrs(presentation, index)}>{inner}</li>'
            )

        grid = (
            f'<ul class="md-home__grid md-home__features"'
            f'{self.grid_attrs(block)} role="list">{"".join(cells)}</ul>'
        )
        return self._wrap(block, self._header(block, presentation) + grid, presentation)

    def _image(self, block: Block) -> str:
        props = block.props
        presentation = self._presentation(block)
        figure = self._figure(
            {
                "src": first_of(props, "src", "image", "img", "url", "path"),
                "alt": first_of(props, "alt", "text"),
                "caption": first_of(props, "caption", "desc", "description"),
                "link": first_of(props, "link", "href"),
                "zoom": props.get("zoom"),
            },
            ratio=str(props["ratio"]) if props.get("ratio") else None,
            frames=as_frames(
                props.get("frame"),
                "shadow" if as_bool(props.get("shadow"), False) else None,
                "glow" if as_bool(props.get("glow"), False) else None,
            ),
        )
        body = self.block(block.body)
        if body:
            figure += f'<div class="md-home__caption-body md-home__prose md-typeset">{body}</div>'

        extras = []
        side = str(first_of(props, "float", "side", default="") or "").strip().lower()
        if side in ("left", "right"):
            extras.append(f"md-home__float--{side}")

        return self._wrap(
            block,
            figure,
            presentation,
            *extras,
            style=style_attr(
                {
                    "--md-home-float-width": first_of(props, "float_width", "width_px"),
                    "--md-home-max-width": props.get("max_width"),
                }
            ),
        )

    def _gallery(self, block: Block) -> str:
        props = block.props
        presentation = self._presentation(block)
        items = as_items(first_of(props, "images", "items"), ("src", "caption", "alt"))
        if not items:
            items = self._images_from_body(block.body)
        if not items:
            raise BlockError("a gallery block needs an `images:` list or a body of Markdown images")

        mode = str(first_of(props, "mode", "layout", default="scroll")).strip().lower()
        if mode not in ("scroll", "paged", "grid"):
            mode = "scroll"
        ratio = str(props.get("ratio") or "16/9")

        slides = "".join(
            f'<li class="md-home__slide">{self._figure(item, ratio=ratio)}</li>' for item in items
        )
        if mode == "grid":
            grid = (
                f'<ul class="md-home__grid md-home__gallery-grid"'
                f'{self.grid_attrs(block)} role="list">{slides}</ul>'
            )
            return self._wrap(block, self._header(block, presentation) + grid, presentation)

        per_view = as_number(first_of(props, "per_view", "per_page"))
        markup = (
            '<div class="md-home__gallery-viewport" data-home-gallery-viewport>'
            f'<ul class="md-home__gallery-track" role="list">{slides}</ul>'
            "</div>"
            '<div class="md-home__gallery-nav">'
            '<button type="button" class="md-home__gallery-btn" data-home-gallery-prev '
            f'aria-label="上一张">{icon("chevron-left")}</button>'
            '<button type="button" class="md-home__gallery-btn" data-home-gallery-next '
            f'aria-label="下一张">{icon("chevron-right")}</button>'
            "</div>"
            '<div class="md-home__gallery-dots" aria-label="图片导航"></div>'
        )
        gallery = (
            f'<div class="md-home__gallery md-home__gallery--{esc(mode)}"'
            f' data-home-gallery="{esc(mode)}" tabindex="0"'
            f'{style_attr({"--md-home-per-view": per_view})}>{markup}</div>'
        )
        return self._wrap(block, self._header(block, presentation) + gallery, presentation)

    def _images_from_body(self, body: str) -> list:
        """Recover images from a Markdown body so a gallery can just be prose."""
        rendered = self.block(body)
        if not rendered:
            return []
        linked: dict[int, str] = {}
        for match in _LINKED_IMG_RE.finditer(rendered):
            inner = _IMG_RE.search(match.group(2))
            if inner:
                linked[match.start(2) + inner.start()] = match.group(1)

        items = []
        for match in _IMG_RE.finditer(rendered):
            attributes = dict(_ATTR_RE.findall(match.group(0)))
            source = attributes.get("src")
            if not source:
                continue
            items.append(
                {
                    "src": _html.unescape(source),
                    "alt": _html.unescape(attributes.get("alt", "")),
                    "caption": _html.unescape(attributes.get("title", "")),
                    "link": _html.unescape(linked[match.start()])
                    if match.start() in linked
                    else None,
                }
            )
        return items

    def _pane_meta(self, raw: Any) -> dict:
        if isinstance(raw, Mapping):
            return {str(key): value for key, value in raw.items()}
        if isinstance(raw, str):
            parts = split_pipe(raw, maxparts=3)
            return {name: part for name, part in zip(("theme", "class", "title"), parts) if part}
        return {}

    def _split(self, block: Block) -> str:
        props = block.props
        presentation = self._presentation(block)
        panels = split_panels(block.body)
        if len(panels) < 2:
            raise BlockError(
                "a split block needs at least two panels, separated by a line containing only `===`"
            )

        tracks = as_tracks(first_of(props, "ratio", "columns")) or " ".join(["1fr"] * len(panels))
        reverse = as_bool(props.get("reverse"), False)
        divider = as_bool(props.get("divider"), len(panels) == 2)
        sticky = as_bool(props.get("sticky"), False)
        metadatas = [self._pane_meta(raw) for raw in as_list(props.get("panes"))]

        rendered = []
        for index, panel in enumerate(panels):
            meta = metadatas[index] if index < len(metadatas) else {}
            theme = normalize_theme(meta.get("theme"))
            pane_classes = classes(
                "md-home__pane",
                "md-home__prose",
                "md-typeset",
                f"{ROOT}--theme-{theme}" if theme else "",
                css_class(meta.get("class")),
                "md-home__pane--sticky" if sticky and index == 0 else "",
                "md-home__pane--ruled" if divider and index else "",
            )
            header = (
                f'<p class="md-home__pane-title">{self.inline(meta["title"])}</p>'
                if meta.get("title")
                else ""
            )
            rendered.append(f'<div class="{pane_classes}">{header}{self.block(panel)}</div>')

        layout = (
            f'<div class="md-home__split md-home__split--{len(panels)}'
            f'{" md-home__split--reverse" if reverse else ""}"'
            + style_attr(
                {
                    "--md-home-tracks": Validated(tracks),
                    "--md-home-gap": props.get("gap"),
                }
            )
            + f'>{"".join(rendered)}</div>'
        )
        return self._wrap(block, self._header(block, presentation) + layout, presentation)

    def _text(self, block: Block) -> str:
        props = block.props
        presentation = self._presentation(block)
        body = self.block(block.body)
        if not body:
            raise BlockError("a text block needs a Markdown body")

        text_classes = ["md-home__text", "md-home__prose", "md-typeset"]
        if as_bool(first_of(props, "panel", "callout"), False):
            text_classes.append("md-home__text--panel")
        if as_bool(props.get("lead"), False):
            text_classes.append("md-home__text--lead")

        columns = props.get("columns")
        content = body
        if props.get("icon"):
            content = f'{icon(props["icon"])}<div class="md-home__text-body">{body}</div>'
        if as_bool(props.get("collapsible"), False):
            summary = self.inline(first_of(props, "summary", "title", default="展开"))
            content = f'<details class="md-home__details"><summary>{summary}</summary>{content}</details>'
        variables = {"--md-home-text-cols": int(columns)} if _INT_RE.match(str(columns or "")) else {}
        return self._wrap(
            block,
            self._header(block, presentation)
            + f'<div class="{classes(*text_classes)}"{style_attr(variables)}>{content}</div>',
            presentation,
        )

    def _stats(self, block: Block) -> str:
        props = block.props
        presentation = self._presentation(block)
        stats = as_items(first_of(props, "stats", "items"), ("value", "label", "icon"))
        if not stats:
            raise BlockError("a stats block needs a `stats:` list with at least one item")

        animate = as_bool(props.get("animate"), True) and self.options.get("count", True)
        cells = []
        for index, stat in enumerate(stats):
            theme = normalize_theme(stat.get("theme"))
            raw = stat.get("value")
            parts = number_parts(raw) if animate else None
            if parts:
                prefix, number, suffix = parts
                decimals = len(number.split(".")[1]) if "." in number else 0
                value = (
                    '<span class="md-home__stat-value">'
                    f'<span class="md-home__stat-prefix">{esc(prefix)}</span>'
                    f'<span class="md-home__stat-number" data-home-count="{esc(number)}"'
                    f' data-home-decimals="{decimals}">{esc(number)}</span>'
                    f'<span class="md-home__stat-suffix">{esc(suffix)}</span></span>'
                )
            else:
                value = f'<span class="md-home__stat-value">{self.inline(raw)}</span>'
            glyph = (
                f'<span class="md-home__stat-icon">{icon(stat["icon"])}</span>'
                if stat.get("icon")
                else ""
            )
            label = first_of(stat, "label", "desc", "title", default="")
            cells.append(
                f'<li class="{classes("md-home__stat", f"{ROOT}--theme-{theme}" if theme else "")}"'
                f'{self._item_attrs(presentation, index)}>'
                f'{glyph}{value}<span class="md-home__stat-label">{self.inline(label)}</span></li>'
            )
        grid = (
            f'<ul class="md-home__grid md-home__stats"'
            f'{self.grid_attrs(block)} role="list">{"".join(cells)}</ul>'
        )
        return self._wrap(block, self._header(block, presentation) + grid, presentation)

    def _steps(self, block: Block) -> str:
        props = block.props
        presentation = self._presentation(block)
        steps = as_items(first_of(props, "steps", "items"), ("title", "desc", "icon", "link"))
        if not steps:
            raise BlockError("a steps block needs a `steps:` list with at least one item")

        direction = str(props.get("direction") or "vertical").strip().lower()
        if direction not in ("vertical", "horizontal"):
            direction = "vertical"
        numbered = as_bool(props.get("numbered"), True)

        cells = []
        for index, step in enumerate(steps):
            theme = normalize_theme(step.get("theme"))
            marker = (
                icon(step["icon"])
                if step.get("icon")
                else (f'<span class="md-home__step-number">{index + 1}</span>' if numbered else "")
            )
            link = first_of(step, "link", "url", "href")
            title = first_of(step, "title", "heading")
            desc = first_of(step, "desc", "description", "text")
            heading = self.inline(title)
            if link and title:
                heading = f'<a class="md-home__step-link" {url_attrs(step, link)}>{heading}</a>'
            body = f'<p class="md-home__step-title">{heading}</p>' if title else ""
            if desc:
                body += f'<p class="md-home__step-desc">{self.inline(desc)}</p>'
            cells.append(
                f'<li class="{classes("md-home__step", f"{ROOT}--theme-{theme}" if theme else "")}"'
                f'{self._item_attrs(presentation, index)}>'
                f'<span class="md-home__step-marker">{marker}</span>'
                f'<span class="md-home__step-body">{body}</span></li>'
            )
        listing = (
            f'<ol class="md-home__steps md-home__steps--{esc(direction)}"'
            f'{style_attr({"--md-home-cols": len(steps)})} role="list">{"".join(cells)}</ol>'
        )
        return self._wrap(block, self._header(block, presentation) + listing, presentation)

    def _links(self, block: Block) -> str:
        props = block.props
        presentation = self._presentation(block)
        links = as_items(first_of(props, "links", "items"), ("text", "link", "desc"))
        if not links:
            raise BlockError("a links block needs a `links:` list with at least one item")

        style = str(props.get("style") or "list").strip().lower()
        if style not in ("list", "chips", "buttons", "cards"):
            style = "list"

        cells = []
        for index, link in enumerate(links):
            text = first_of(link, "text", "title", "label")
            href = first_of(link, "link", "url", "href")
            desc = first_of(link, "desc", "description", "subtitle")
            theme = normalize_theme(link.get("theme"))
            glyph = icon(link["icon"]) if link.get("icon") else ""
            inner = (
                f'{glyph}<span class="md-home__link-body">'
                f'<span class="md-home__link-text">{self.inline(text)}</span>'
            )
            if desc:
                inner += f'<span class="md-home__link-desc">{self.inline(desc)}</span>'
            inner += "</span>"
            if style in ("list", "cards"):
                inner += icon("arrow-right")
            item_classes = classes(
                "md-home__link",
                f"{ROOT}--theme-{theme}" if theme else "",
                css_class(link.get("class")),
            )
            if href:
                anchor = f'<a class="{item_classes}" {url_attrs(link, href)}>{inner}</a>'
            else:
                anchor = f'<span class="{item_classes}">{inner}</span>'
            cells.append(
                f'<li class="md-home__link-item"{self._item_attrs(presentation, index)}>{anchor}</li>'
            )

        listing = (
            f'<ul class="md-home__links md-home__links--{esc(style)}"'
            f'{self.grid_attrs(block)} role="list">{"".join(cells)}</ul>'
        )
        return self._wrap(block, self._header(block, presentation) + listing, presentation)

    def _anim(self, block: Block) -> str:
        props = block.props
        presentation = self._presentation(block)
        effect = str(first_of(props, "effect", "type", default="float")).strip().lower()
        if effect not in ANIM_EFFECTS:
            raise BlockError(
                f"unknown anim effect {effect!r}; expected one of: " + ", ".join(ANIM_EFFECTS)
            )

        body = self.block(block.body)
        if body:
            inner = f'<div class="md-home__anim-body md-home__prose md-typeset">{body}</div>'
        else:
            text = props.get("text")
            if not text:
                raise BlockError("an anim block needs a Markdown body or a `text` prop")
            inner = f'<div class="md-home__anim-body">{self.inline(text)}</div>'

        variables = {
            "--md-home-anim-duration": props.get("duration"),
            "--md-home-anim-delay": props.get("delay"),
        }
        if effect == "marquee":
            # Duplicating the content is what makes a seamless CSS-only marquee
            # possible; the copy is hidden from assistive technology.
            inner = (
                '<div class="md-home__marquee"><div class="md-home__marquee-track">'
                f'<div class="md-home__marquee-item">{inner}</div>'
                f'<div class="md-home__marquee-item" aria-hidden="true">{inner}</div>'
                "</div></div>"
            )
        elif effect == "typetext":
            plain = _html.unescape(_TAGS_RE.sub("", inner)).strip()
            inner = (
                '<div class="md-home__typing" data-home-typewriter'
                f' data-home-type-text="{esc(plain)}">{inner}'
                '<span class="md-home__caret" aria-hidden="true"></span></div>'
            )

        return self._wrap(
            block,
            inner,
            presentation,
            f"md-home__anim--{effect}",
            tag="div",
            style=style_attr(variables),
            attrs=f'data-home-anim="{esc(effect)}"',
        )

    def _divider(self, block: Block) -> str:
        props = block.props
        presentation = self._presentation(block)
        style = str(first_of(props, "style", "variant", default="line")).strip().lower()
        if style not in ("line", "space", "dots", "wave", "gradient"):
            style = "line"
        label = first_of(props, "text", "label", "title")
        inner = f'<span class="md-home__divider-label">{self.inline(label)}</span>' if label else ""
        variables = {"--md-home-divider-space": props.get("size")} if style == "space" else {}
        return self._wrap(
            block,
            inner,
            presentation,
            f"md-home__divider--{style}",
            tag="div",
            style=style_attr(variables),
            attrs='role="separator"',
        )
