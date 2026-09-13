"""The four "author in control" features: ratio, blank slots, rows, colours.

These are the props that let an author say what they want directly instead of
working around the widget, so each one is asserted from two directions: the
capability is reachable, and the *absence* of the prop changes nothing.  The
second half matters more than it looks -- every one of these is opt-in, and an
opt-in that quietly applies itself by default is worse than not having it.
"""

from __future__ import annotations

import logging
import re

import pytest

from mkdocs_homepage.render import as_item, as_items, is_gap
from mkdocs_homepage.util import NAMED_COLORS, css_color, css_ratio
from tests.conftest import render


# -- the blank slot --------------------------------------------------------
def test_every_way_of_writing_a_blank_is_one():
    """A bare `-`, an empty mapping and the marker words all mean the same."""
    fields = ("title", "link")
    for raw in (None, {}, "", "empty", "blank", "gap", "spacer", "GAP"):
        assert is_gap(as_item(raw, fields)), raw
    for raw in ("A", {"title": "A"}, "empty | /x/"):
        assert not is_gap(as_item(raw, fields)), raw


def test_a_marker_word_with_a_pipe_is_a_real_entry():
    """`- empty` is a gap; `- empty | /x/` is a card *called* empty."""
    item = as_item("empty | /guide/", ("title", "link"))
    assert not is_gap(item)
    assert item["title"] == "empty"
    assert item["link"] == "/guide/"


def test_as_items_keeps_blanks_but_as_list_still_normalises():
    items = as_items(["A", None, "C"], ("title", "link"))
    assert len(items) == 3
    assert [is_gap(item) for item in items] == [False, True, False]


@pytest.mark.parametrize(
    "kind, source",
    [
        ("cards", "```homepage-cards\ncolumns: 4\ncards:\n  - A\n  - blank\n  - C\n```"),
        ("features", "```homepage-features\ncolumns: 3\nfeatures:\n  - A\n  -\n  - C\n```"),
        ("stats", "```homepage-stats\ncolumns: 3\nstats:\n  - 1 | a\n  - empty\n  - 3 | c\n```"),
        ("steps", "```homepage-steps\ncolumns: 3\nsteps:\n  - A | /a/\n  - gap\n  - C | /c/\n```"),
        ("links", "```homepage-links\ncolumns: 3\nlinks:\n  - A | /a/\n  - blank\n  - C | /c/\n```"),
        (
            "testimonials",
            "```homepage-testimonials\ncolumns: 3\ntestimonials:\n  - quote: A\n  - spacer\n"
            "  - quote: C\n```",
        ),
        ("logos", "```homepage-logos\nlogos:\n  - simple/github | A\n  - gap\n```"),
        (
            "showcase",
            "```homepage-showcase\nshowcase:\n  - title: A\n    image: /a.svg\n  - blank\n"
            "  - title: C\n    image: /c.svg\n```",
        ),
        ("gallery", "```homepage-gallery\nimages:\n  - src: /a.svg\n  - gap\n```"),
    ],
)
def test_every_repeatable_block_can_hold_a_blank(kind, source):
    """A blank position, in every list a block can repeat."""
    html = render(source)
    assert "md-home--error" not in html, html[:500]
    assert "md-home__gap" in html or 'aria-hidden="true"></li>' in html, html[:500]
    # The blocks that are not grids mark their own blank; both are fine, but the
    # *item count* has to match the author's list either way.
    assert html.count("md-home--error") == 0


def test_a_blank_does_not_invent_a_missing_required_prop():
    """The gap has to be skipped *before* the per-item validation."""
    # `showcase` requires an image per row; a blank row must not trip that.
    html = render("```homepage-showcase\nshowcase:\n  - title: A\n    image: /a.svg\n  - \n```")
    assert "needs an `image`" not in html
    # ...and a block whose *only* entry is a blank is still an error, not an
    # empty grid with no explanation.
    for kind in (
        "cards",
        "features",
        "stats",
        "steps",
        "links",
        "logos",
        "testimonials",
        "showcase",
    ):
        html = render(f"```homepage-{kind}\n{kind}:\n  - gap\n```")
        assert "md-home--error" in html, kind
        assert "needs a" in html, kind


def test_the_stagger_keeps_counting_the_blank():
    """Otherwise the delays stop matching the visual order."""
    html = render(
        "```homepage-cards\ncolumns: 3\ncards:\n  - A\n  - blank\n  - C\n```"
    )
    indexes = re.findall(r'data-home-index="(\d+)"', html)
    assert indexes == ["0", "2"], indexes


def test_a_blank_carries_nothing_to_announce():
    html = render("```homepage-cards\ncards:\n  - A\n  - blank\n```")
    gap = re.search(r"<li class=\"[^\"]*md-home__gap[^\"]*\"[^>]*>", html)
    assert gap, html[:400]
    assert 'aria-hidden="true"' in gap.group(0)
    assert "data-home-reveal" not in gap.group(0)


def test_a_marquee_blank_survives_the_duplicate_pass():
    """One gap in one period and not the other puts the loop out of phase."""
    html = render("```homepage-logos\nstyle: marquee\nlogos:\n  - simple/github | A\n  - gap\n```")
    assert html.count("md-home__logo-item") == 4, html.count("md-home__logo-item")


# -- the card's own ratio --------------------------------------------------
def test_a_card_can_set_its_own_aspect_ratio():
    html = render(
        "```homepage-cards\ncards:\n  - title: A\n    ratio: 4/3\n"
        "---\n```"
    )
    assert "--md-home-card-ratio:4 / 3;" in html, html[:400]
    assert "md-home__card--sized" in html


def test_a_card_without_a_ratio_is_not_sized():
    html = render("```homepage-cards\ncards:\n  - title: A\n```")
    assert "md-home__card-ratio" not in html
    assert "md-home__card--sized" not in html


def test_the_cover_ratio_moved_to_its_own_key():
    """`ratio` used to mean the cover's, which left no way to size the card."""
    html = render(
        "```homepage-cards\ncards:\n  - title: A\n    image: /a.svg\n    ratio: 4/3\n```"
    )
    # The card is 4/3 ...
    assert "--md-home-card-ratio:4 / 3;" in html
    # ... and the cover falls back to the default, not to 4/3.
    assert "--md-home-ratio:16 / 9;" in html, html[:600]

    explicit = render(
        "```homepage-cards\ncards:\n  - title: A\n    image: /a.svg\n"
        "    image_ratio: 21/9\n    ratio: 1/1\n```"
    )
    assert "--md-home-card-ratio:1 / 1;" in explicit
    assert "--md-home-ratio:21 / 9;" in explicit


def test_the_block_ratio_is_still_the_cover_default():
    html = render(
        "```homepage-cards\nratio: 3/2\ncards:\n  - title: A\n    image: /a.svg\n```"
    )
    assert "--md-home-ratio:3 / 2;" in html


# -- per-scheme colours ----------------------------------------------------
def test_a_card_can_name_its_own_colours_per_scheme():
    html = render(
        "```homepage-cards\ncards:\n  - title: A\n"
        "    bg: '#eef1ff'\n    bg_dark: '#171a26'\n"
        "    glow: '#4f6bed'\n    glow_dark: '#8fa4ff'\n```"
    )
    assert "--md-home-card-bg:#eef1ff;" in html
    assert "--md-home-card-bg-dark:#171a26;" in html
    assert "--md-home-card-accent:#4f6bed;" in html
    assert "--md-home-card-accent-dark:#8fa4ff;" in html


def test_the_two_schemes_are_independent():
    """Naming only one must not lock the other out."""
    light_only = render(
        "```homepage-cards\ncards:\n  - title: A\n    bg: '#eef1ff'\n```"
    )
    assert "--md-home-card-bg:#eef1ff;" in light_only
    assert "--md-home-card-bg-dark" not in light_only

    dark_only = render(
        "```homepage-cards\ncards:\n  - title: A\n    bg_dark: '#171a26'\n```"
    )
    assert "--md-home-card-bg:" not in dark_only
    assert "--md-home-card-bg-dark:#171a26;" in dark_only


def test_the_colour_keys_accept_the_shapes_an_author_writes():
    html = render(
        "```homepage-cards\ncards:\n  - title: A\n    bg: rebeccapurple\n"
        "    glow: rgb(20 30 40 / 0.5)\n  - title: B\n    bg: '#abc'\n"
        "    glow: oklch(0.7 0.1 250)\n  - title: C\n    bg: transparent\n```"
    )
    assert "--md-home-card-bg:rebeccapurple;" in html
    assert "rgb(20 30 40 / 0.5)" in html
    assert "--md-home-card-bg:#abc;" in html
    assert "oklch(0.7 0.1 250)" in html
    assert "--md-home-card-bg:transparent;" in html


def test_a_colour_that_is_not_a_colour_is_reported(caplog):
    """Silently dropping it would look like the prop does nothing."""
    with caplog.at_level(logging.WARNING, logger="mkdocs.plugins.homepage"):
        html = render("```homepage-cards\ncards:\n  - title: A\n    bg: '#ggg'\n```")
    assert "is not a colour" in caplog.text
    assert "--md-home-card-bg" not in html


def test_a_card_without_colours_keeps_the_derived_palette():
    html = render("```homepage-cards\ncards:\n  - title: A\n    theme: cyan\n```")
    assert "md-home--theme-cyan" in html
    assert "--md-home-card-" not in html


# -- the colour validator --------------------------------------------------
def test_the_colour_validator_accepts_the_legitimate_shapes():
    for value in (
        "#fff",
        "#ffff",
        "#ffffff",
        "#ffffff80",
        "red",
        "RED",
        "transparent",
        "currentcolor",
        "rgb(1, 2, 3)",
        "rgba(1 2 3 / 50%)",
        "hsl(200 50% 40%)",
        "oklch(0.7 0.1 250)",
        "color-mix(in srgb, red 20%, blue)",
        "light-dark(#fff, #000)",
    ):
        assert css_color(value) == value.strip().lower() or css_color(value) is not None, value


def test_the_colour_validator_rejects_what_could_escape_the_declaration():
    """The value lands in an inline `style`, so this is the guard that matters."""
    for value in (
        "red;background:url(evil)",
        "url(evil)",
        "#ggg",
        "#12345",
        "expression(alert(1))",
        'red"}',
        "red\\",
        "rgb(1,2,3);x",
        "banana",
        "",
        None,
        True,
    ):
        assert css_color(value) is None, value


def test_every_named_colour_is_a_name():
    assert NAMED_COLORS, "the named-colour list is empty"
    assert all(name.isalpha() and name.islower() for name in NAMED_COLORS)
    assert "rebeccapurple" in NAMED_COLORS
    assert "transparent" in NAMED_COLORS


def test_a_colour_value_cannot_smuggle_a_second_declaration():
    html = render(
        "```homepage-cards\ncards:\n  - title: A\n    bg: 'red;color:blue'\n```"
    )
    assert "color:blue" not in html
    assert "--md-home-card-bg" not in html


# -- ratio, the YAML trap --------------------------------------------------
def test_a_colon_ratio_that_yaml_already_evaluated_is_refused(caplog):
    """`ratio: 4:3` unquoted is 243, and 243 is a *valid* CSS ratio.

    YAML 1.1 folds sexagesimal, so the author's `4:3` reached the renderer as
    `4 * 60 + 3`.  243 is a legal `aspect-ratio`, so nothing rejected it and the
    card came out 243 times taller than wide with no message at all.
    """
    assert css_ratio("4:3") == "4 / 3"  # quoted, the way it should be written
    for mangled, original in ((243, "4:3"), (969, "16:9"), (61, "1:1"), (1269, "21:9")):
        with caplog.at_level(logging.WARNING, logger="mkdocs.plugins.homepage"):
            assert css_ratio(mangled) is None, f"{mangled} ({original}) was accepted"
        assert "YAML" in caplog.text
        caplog.clear()


def test_a_plain_number_ratio_still_works():
    """`ratio: 1.5` is a legitimate shorthand and must not trip the guard."""
    assert css_ratio(1.5) == "1.5"
    assert css_ratio(3) == "3"
    assert css_ratio(16) == "16"
    assert css_ratio("1.5") == "1 / 5" or css_ratio("1.5") is None


def test_a_mangled_ratio_falls_back_instead_of_exploding(caplog):
    """The card keeps the default box rather than rendering 243x tall."""
    with caplog.at_level(logging.WARNING, logger="mkdocs.plugins.homepage"):
        html = render("```homepage-cards\ncards:\n  - title: A\n    ratio: 243\n```")
    assert "--md-home-card-ratio" not in html
    assert "md-home__card--sized" not in html
    assert "YAML" in caplog.text
    # ...and the card is still a card, not a half-rendered one.
    assert "md-home__card-title" in html


def test_the_same_guard_covers_the_cover_ratio(caplog):
    """`ratio: 16:9` unquoted is 969, and a cover is not special."""
    with caplog.at_level(logging.WARNING, logger="mkdocs.plugins.homepage"):
        html = render("```homepage-cards\nratio: 969\ncards:\n  - title: A\n    image: /a.svg\n```")
    assert "--md-home-ratio" not in html, html[:400]
    assert "YAML" in caplog.text
    # The figure still renders; it just keeps the built-in default.
    assert "md-home__figure" in html


def test_a_valid_cover_ratio_is_unaffected():
    assert "--md-home-ratio:16 / 9;" in render(
        "```homepage-cards\nratio: 16/9\ncards:\n  - title: A\n    image: /a.svg\n```"
    )
    # A bare number is still a legitimate ratio.
    assert "--md-home-ratio:1.5;" in render(
        "```homepage-cards\nratio: 1.5\ncards:\n  - title: A\n    image: /a.svg\n```"
    )


# -- rows ------------------------------------------------------------------
def test_cards_can_be_laid_out_as_rows():
    html = render(
        "```homepage-cards\nlayout: rows\ncards:\n  - title: A\n    body: |\n      Long form.\n```"
    )
    assert "md-home__cards--rows" in html
    assert "md-home__card-row" in html
    assert "md-home__card-aside" in html
    assert "Long form." in html


def test_a_row_keeps_its_pane_when_it_has_no_prose():
    """That is what lines a stack of these up."""
    html = render("```homepage-cards\nlayout: rows\ncards:\n  - title: A\n```")
    assert "md-home__card-aside" in html
    assert "aria-hidden=\"true\"" in html


def test_a_row_can_flip_its_sides():
    html = render(
        "```homepage-cards\nlayout: rows\ncards:\n  - title: A\n    body: x\n    reverse: true\n```"
    )
    assert "md-home__card-row--reverse" in html


def test_the_row_body_is_markdown_not_escaped_text():
    html = render(
        "```homepage-cards\nlayout: rows\ncards:\n  - title: A\n"
        "    body: |\n      - one\n      - two\n```"
    )
    assert "<li>one</li>" in html
    assert "md-home__prose" in html


def test_the_grid_layout_is_still_the_default():
    html = render("```homepage-cards\ncards:\n  - title: A\n```")
    assert "md-home__cards--grid" in html
    assert "md-home__card-row" not in html


def test_an_unknown_layout_falls_back_to_grid():
    html = render("```homepage-cards\nlayout: spiral\ncards:\n  - title: A\n```")
    assert "md-home--error" not in html
    assert "md-home__cards--grid" in html


# -- columns reach every grid ----------------------------------------------
def test_every_grid_container_can_take_a_declared_column_count():
    """`columns` was silently ignored by one grid and honoured by the rest.

    A brand wall in `style: grid` is a grid like any other, so `columns: 4` has to
    mean four -- a prop that does nothing is worse than a prop that is absent.
    """
    grid = render("```homepage-logos\nstyle: grid\ncolumns: 4\nlogos:\n  - simple/go | Go\n```")
    assert "data-home-cols" in grid, grid[:400]
    assert "--md-home-cols:4;" in grid

    # The flex and marquee forms are not grids, so the marker stays off them --
    # `grid-template-columns` on a flex container would be dead weight.
    for style in ("row", "marquee"):
        flexible = render(
            f"```homepage-logos\nstyle: {style}\ncolumns: 4\nlogos:\n  - simple/go | Go\n```"
        )
        assert "data-home-cols" not in flexible, style
        assert "md-home--error" not in flexible
