"""Rendering: the markup contract, the escaping rules, and Markdown parity."""

from __future__ import annotations

import logging
import re

import pytest

from tests.conftest import render

#: One minimal, valid source per kind.  Every kind must render without an error
#: marker -- this is the smoke test that catches a kind wired to no renderer or a
#: required prop that is impossible to satisfy.
SAMPLES = {
    "hero": '```homepage-hero\ntitle: Hello\nimage: /a.svg\n---\nLead text\n```',
    "cards": '```homepage-cards\ncards:\n  - title: A\n    desc: B\n```',
    "showcase": '```homepage-showcase\nshowcase:\n  - title: A\n    image: /a.svg\n```',
    "features": '```homepage-features\nfeatures:\n  - title: A\n    icon: tools\n```',
    "testimonials": '```homepage-testimonials\ntestimonials:\n  - quote: Nice\n    name: A\n```',
    "logos": '```homepage-logos\nlogos:\n  - simple/github | GitHub\n```',
    "image": '```homepage-image\nsrc: /a.svg\ncaption: A caption\n```',
    "gallery": '```homepage-gallery\n---\n![one](/1.svg "first")\n\n![two](/2.svg "second")\n```',
    "split": '```homepage-split\n---\nleft\n\n===\n\nright\n```',
    "text": '```homepage-text\n---\nprose\n```',
    "stats": '```homepage-stats\nstats:\n  - value: "12"\n    label: things\n```',
    "steps": '```homepage-steps\nsteps:\n  - title: first\n```',
    "links": '```homepage-links\nlinks:\n  - a | /a/\n```',
    "cta": '```homepage-cta\ntitle: Join\nactions:\n  - Go | /go/ | primary\n```',
    "anim": '```homepage-anim\neffect: pulse\n---\ncontent\n```',
    "divider": '```homepage-divider\nstyle: dots\n```',
}

#: Every slot in the widget that draws one small mark, and the shortest source
#: that reaches it.  The list is deliberately exhaustive: "everywhere an icon is
#: allowed a picture is allowed too" is only true if there is no slot missing
#: from here, so a new icon slot has to be added to this table.
MARK_SLOTS = {
    "cards": "```homepage-cards\ncards:\n  - title: A\n    icon: /a.svg\n```",
    "features": "```homepage-features\nfeatures:\n  - title: A\n    icon: /a.svg\n```",
    "stats": "```homepage-stats\nstats:\n  - 1 | one | /a.svg\n```",
    "steps": "```homepage-steps\nsteps:\n  - A | /x/ | desc | /a.svg\n```",
    "links": "```homepage-links\nlinks:\n  - A | /x/ | desc | /a.svg\n```",
    "showcase-bullet": (
        "```homepage-showcase\nshowcase:\n  - title: A\n    image: /b.svg\n"
        "    features:\n      - id: x\n        icon: /a.svg\n```"
    ),
    "hero-actions": "```homepage-hero\ntitle: T\nactions:\n  - A | /x/ | primary | /a.svg\n```",
    "hero-highlights": "```homepage-hero\ntitle: T\nhighlights:\n  - 1 | one | /a.svg\n```",
    "cta-actions": "```homepage-cta\ntitle: T\nactions:\n  - A | /x/ | primary | /a.svg\n```",
    "text": "```homepage-text\nicon: /a.svg\n---\nprose\n```",
    "logos-icon": "```homepage-logos\nlogos:\n  - icon: /a.svg\n    name: A\n```",
    "logos-image": "```homepage-logos\nlogos:\n  - image: /a.svg\n    name: A\n```",
}


@pytest.mark.parametrize("kind", sorted(SAMPLES))
def test_every_kind_renders_without_an_error_marker(kind):
    html = render(SAMPLES[kind])
    assert f"md-home--{kind}" in html
    assert "md-home--error" not in html


# -- icons and pictures are interchangeable --------------------------------
@pytest.mark.parametrize("slot", sorted(MARK_SLOTS))
def test_every_icon_slot_takes_a_picture(slot):
    """One key carries either, so every slot takes a picture the same way.

    ``icon:`` is the key that means "the small mark here", and a value with a
    picture extension is a file.  A slot that only understands glyph names would
    make an author with a logo file hunt for a substitute glyph, which is the
    whole point of the feature.
    """
    html = render(MARK_SLOTS[slot])
    assert "md-home--error" not in html
    assert '<img class="md-home__mark-img" src="/a.svg"' in html, html[:400]


@pytest.mark.parametrize("slot", sorted(MARK_SLOTS))
def test_the_same_key_still_takes_a_glyph(slot):
    """The positive control: the picture path must not have replaced the glyph.

    Every source above is the same block with the mark swapped, so if a slot
    stopped drawing icons this would catch it -- and if the *discriminator* were
    broken (everything treated as a picture) the test above would pass on its own.
    """
    source = MARK_SLOTS[slot].replace("/a.svg", "rocket-launch-outline")
    # A slot reached through the explicit `image:` key wants that key swapped too,
    # because `image:` is *meant* to stay a picture whatever it holds.
    source = source.replace("image: rocket-launch-outline", "icon: rocket-launch-outline")
    html = render(source)
    assert "md-home--error" not in html
    assert "md-home__mark-img" not in html, html[:400]
    assert "<svg" in html


def test_a_dot_is_what_makes_an_icon_value_a_picture():
    """The discriminator, at the value level, including the near misses."""
    from mkdocs_homepage.util import is_image_ref

    assert is_image_ref("assets/logo.svg")
    assert is_image_ref("/logo.png")
    assert is_image_ref("https://example.com/a.webp")
    assert is_image_ref("logo.svg?v=2")  # a query string is not an extension
    assert is_image_ref("logo.svg#frag")

    assert not is_image_ref("simple/github")  # a slash is not a dot
    assert not is_image_ref("rocket-launch-outline")
    assert not is_image_ref("check-circle-outline")
    assert not is_image_ref("")
    assert not is_image_ref(None)
    assert not is_image_ref("logo")  # a bare name has no extension
    assert not is_image_ref("assets/logo")  # ...even in a directory


def test_a_decorative_mark_gets_an_empty_alt_and_a_labelled_one_does_not():
    """`alt` admits to guessing otherwise.

    A card icon sits beside the card's own title, so an alt that fell back to
    `title:` made a screen reader read the heading twice.  Blank means decorative.
    """
    card = render("```homepage-cards\ncards:\n  - title: Hello\n    icon: /a.svg\n```")
    assert 'alt=""' in card, card[:400]

    logo = render("```homepage-logos\nlogos:\n  - icon: /a.svg\n    name: Acme\n```")
    assert 'alt="Acme"' in logo

    explicit = render("```homepage-features\nfeatures:\n  - title: A\n    icon: /a.svg\n    alt: 说明\n```")
    assert 'alt="说明"' in explicit


def test_a_picture_is_never_reported_as_an_unknown_icon(caplog):
    """The name validator must not see a path -- that warning would be noise."""
    with caplog.at_level(logging.WARNING, logger="mkdocs.plugins.homepage"):
        render("```homepage-cards\ncards:\n  - title: A\n    icon: /a.svg\n```")
    assert "unknown icon" not in caplog.text


def test_a_move_kind_of_value_is_still_treated_as_a_glyph(caplog):
    """Positive control for the check above: a typo must still be reported."""
    with caplog.at_level(logging.WARNING, logger="mkdocs.plugins.homepage"):
        render("```homepage-cards\ncards:\n  - title: A\n    icon: not-a-real-icon\n```")
    assert "unknown icon" in caplog.text


# -- the compact `|` form --------------------------------------------------
#: The order the docs promise, and the blocks that honour it, as
#: ``kind: (source, the text the first field carries)``.
LINK_LIKE = {
    "cards": (
        "```homepage-cards\ncards:\n  - Card | /c/ | Desc | rocket-launch-outline\n```",
        "Card",
    ),
    "features": (
        "```homepage-features\nfeatures:\n  - Feat | /f/ | Desc | rocket-launch-outline\n```",
        "Feat",
    ),
    "steps": (
        "```homepage-steps\nsteps:\n  - Step | /s/ | Desc | rocket-launch-outline\n```",
        "Step",
    ),
    "links": (
        "```homepage-links\nlinks:\n  - Link | /l/ | Desc | rocket-launch-outline\n```",
        "Link",
    ),
}


@pytest.mark.parametrize("kind", sorted(LINK_LIKE))
def test_the_pipe_form_fills_the_same_fields_in_every_block(kind):
    """`标题 | 链接 | 描述 | 图标` has to mean one thing, or nobody can remember it.

    It used to mean something different per block: `links` had no `icon` field at
    all, so the fourth value was dropped *and* the third landed in `desc` -- the
    demo rendered `book-open-page-variant-outline` as the description text of a
    link.  `steps` and `features` put `icon` in the third slot instead, so the
    same line drew a different card depending on the fence it sat in.
    """
    source, title = LINK_LIKE[kind]
    html = render(source)
    assert "md-home--error" not in html
    assert f"{title}<" in html, f"{kind}: the first field did not become the title"
    assert ">Desc<" in html, f"{kind}: the description did not land in `desc`"
    assert 'href="' in html, kind
    # The icon is a glyph here, and it is drawn -- not printed.
    assert "<svg" in html
    assert "rocket-launch-outline" not in html, (
        f"{kind}: the icon name leaked into the output as text"
    )


def test_the_pipe_form_reaches_the_action_icon():
    """`文字 | 链接 | 样式 | 图标` -- actions have a required third field."""
    html = render(
        "```homepage-cta\ntitle: T\nactions:\n  - Go | /go/ | primary | rocket-launch-outline\n```"
    )
    assert 'md-button--primary' in html
    assert "<svg" in html
    assert "rocket-launch-outline" not in html


def test_an_empty_pipe_field_does_not_shift_the_others():
    """`A | /x/ | | icon` -- the description is optional, the icon is not lost."""
    html = render("```homepage-links\nlinks:\n  - A | /x/ | | rocket-launch-outline\n```")
    assert 'href="/x/"' in html
    assert "<svg" in html
    assert "rocket-launch-outline" not in html


def test_the_field_tuples_are_named_constants_not_local_decisions():
    """A per-block order is what let them drift apart in the first place.

    Both orders are documented constants now, so the promise in the docs and the
    behaviour in the code are the same object -- and the three orders that used to
    be written inline (two of them wrong) cannot come back.
    """
    import inspect

    from mkdocs_homepage import render as renderer

    source = inspect.getsource(renderer)
    assert renderer.LINK_FIELDS == ("title", "link", "desc", "icon")
    assert renderer.ACTION_FIELDS == ("text", "link", "style", "icon")

    for stale in (
        '("text", "link", "desc", "icon")',
        '("title", "desc", "icon", "link")',
        '("text", "link", "desc")',
        '("text", "link", "style")',
    ):
        assert stale not in source, f"{stale} is back; use the named constant"
    assert source.count("LINK_FIELDS)") >= 4, "the link-like blocks stopped sharing the order"
    assert source.count("ACTION_FIELDS)") >= 2, "the two action lists stopped sharing the order"




def test_kinds_are_complete():
    from mkdocs_homepage.parser import BLOCK_KINDS

    assert set(SAMPLES) == set(BLOCK_KINDS)


def test_missing_required_props_produce_an_error_marker():
    html = render("```homepage-cards\ntitle: nothing here\n```")
    assert "md-home--error" in html
    assert "at least one item" in html


def test_strict_mode_raises_instead_of_marking():
    from mkdocs_homepage.parser import BlockError

    with pytest.raises(BlockError):
        render("```homepage-cards\ntitle: nothing here\n```", strict=True)


# -- the markup contract ---------------------------------------------------
def test_card_markup_contract():
    html = render(
        '```homepage-cards\ncolumns: 3\ncards:\n  - title: A\n    link: /a/\n'
        "    icon: tools\n    badge: new\n    tags: [x, y]\n```"
    )
    assert 'data-home-tilt="6"' in html
    assert "data-home-cols" in html
    assert "--md-home-cols:3" in html
    assert '<span class="md-home__card-icon">' in html
    assert "md-home__badge" in html and "md-home__card-tags" in html
    assert 'href="/a/"' in html


def test_cards_reveal_items_not_the_section():
    html = render("```homepage-cards\ncards:\n  - title: A\n  - title: B\n```")
    section = html.split("<ul", 1)[0]
    assert "data-home-reveal" not in section
    assert html.count("data-home-reveal") == 2
    assert "--md-home-reveal-delay:0ms" in html
    assert "--md-home-reveal-delay:55ms" in html


def test_single_blocks_reveal_themselves():
    html = render("```homepage-text\nreveal: up\n---\nx\n```")
    assert 'data-home-reveal="up"' in html


def test_a_card_theme_overrides_its_section():
    html = render("```homepage-cards\ntheme: teal\ncards:\n  - title: A\n    theme: cyan\n```")
    assert "md-home--theme-teal" in html
    assert 'md-home__card md-home__card--ring md-home--theme-cyan' in html


def test_hero_actions_and_lead():
    html = render(
        "```homepage-hero\ntitle: T\nactions:\n  - Go | /go/ | primary\n  - Plain\n---\nlead\n```"
    )
    assert "<h1" in html
    assert "md-button--primary" in html
    assert 'class="md-button md-home__action"' in html
    assert 'href="/go/"' in html
    assert "md-home__lead" in html


def test_split_panels_and_tracks():
    html = render("```homepage-split\nratio: 1.2 1\ndivider: true\n---\nA\n\n===\n\nB\n```")
    assert html.count('class="md-home__pane') == 2
    assert "--md-home-tracks:1.2fr 1fr" in html
    assert "md-home__pane--ruled" in html


def test_split_needs_two_panels():
    assert "at least two panels" in render("```homepage-split\n---\nonly one\n```")


def test_gallery_from_markdown_images():
    html = render('```homepage-gallery\nmode: paged\nper_view: 2\n---\n![a](/a.svg "cap a")\n\n![b](/b.svg)\n```')
    assert html.count("md-home__slide") == 2
    assert "md-home__gallery--paged" in html
    assert "--md-home-per-view:2" in html
    assert "cap a" in html
    assert "md-home__gallery-dots" in html
    assert "md-home__gallery-btn" in html


def test_gallery_from_an_images_list():
    html = render("```homepage-gallery\nimages:\n  - /a.svg | cap\n```")
    assert "/a.svg" in html and "cap" in html


def test_image_lightbox_and_float():
    html = render(
        "```homepage-image\nsrc: /a.svg\nfloat: right\nfloat_width: 40%\nshadow: true\n```"
    )
    assert "data-home-zoom" in html
    assert "md-home__float--right" in html
    assert "--md-home-float-width:40%" in html
    # The frame lands on the figure, so every block that shows an image can use it.
    assert "md-home__figure--shadow" in html


@pytest.mark.parametrize("written", ["16/10", "16 / 10", "16:10", "1.6"])
def test_ratio_is_accepted_in_the_forms_authors_write_it(written):
    """A ratio that a length validator rejects is a silently ignored prop."""
    html = render(f"```homepage-image\nsrc: /a.svg\nratio: '{written}'\n```")
    assert "--md-home-ratio:" in html, written


def test_a_nonsense_ratio_is_dropped_rather_than_passed_through():
    html = render("```homepage-image\nsrc: /a.svg\nratio: '16/0'; color: red\n```")
    assert "color:red" not in html
    assert "--md-home-ratio" not in html


def test_stats_split_prefix_and_suffix():
    html = render('```homepage-stats\nstats:\n  - value: "98.6%"\n    label: uptime\n```')
    assert 'data-home-count="98.6"' in html
    assert 'data-home-decimals="1"' in html
    assert "md-home__stat-suffix" in html and "%" in html


def test_non_numeric_stat_is_not_counted():
    html = render('```homepage-stats\nstats:\n  - value: "∞"\n    label: always\n```')
    assert "data-home-count" not in html
    assert "∞" in html


def test_links_external_links_open_in_a_new_tab():
    html = render("```homepage-links\nlinks:\n  - Project | https://example.com/\n```")
    assert 'target="_blank"' in html and 'rel="noopener"' in html


def test_links_internal_links_do_not():
    html = render("```homepage-links\nlinks:\n  - Guide | /guide/\n```")
    assert "target=" not in html


def test_anim_marquee_duplicates_content_for_a_seamless_loop():
    html = render("```homepage-anim\neffect: marquee\n---\nticker\n```")
    assert 'data-home-anim="marquee"' in html
    assert html.count("md-home__marquee-item") == 2
    assert 'aria-hidden="true"' in html


def test_anim_typetext_carries_its_text():
    html = render("```homepage-anim\neffect: typetext\n---\n**hello** world\n```")
    assert "data-home-typewriter" in html
    assert 'data-home-type-text="hello world"' in html


def test_anim_rejects_an_unknown_effect():
    assert "unknown anim effect" in render("```homepage-anim\neffect: explode\n---\nx\n```")


# -- the "rich" blocks -----------------------------------------------------
def test_showcase_alternates_and_can_be_overridden():
    html = render(
        "```homepage-showcase\nshowcase:\n  - title: A\n    image: /a.svg\n    link: /a/\n"
        "    features:\n      - one\n      - two\n  - title: B\n    image: /b.svg\n"
        "  - title: C\n    image: /c.svg\n    reverse: false\n```"
    )
    # Row 1 and row 3 are as authored (the third opts back out), row 2 alternates.
    assert html.count('class="md-home__showcase-row"') == 2
    assert html.count("md-home__showcase-row--reverse") == 1
    assert "md-home__bullets" in html
    assert "md-home__more" in html
    assert 'href="/a/"' in html


def test_showcase_reverse_flips_which_side_starts():
    html = render(
        "```homepage-showcase\nreverse: true\nshowcase:\n  - title: A\n    image: /a.svg\n"
        "  - title: B\n    image: /b.svg\n```"
    )
    # Flipping the *set* swaps the sides of the first row; the zig-zag stays.
    rows = html.split('class="md-home__showcase-row')
    assert "--reverse" in rows[1]
    assert "--reverse" not in rows[2]


def test_showcase_needs_an_image_per_row():
    assert "needs an `image`" in render("```homepage-showcase\nshowcase:\n  - title: A\n```")


def test_testimonials_render_quote_author_and_avatar():
    html = render(
        "```homepage-testimonials\nrating: true\ntestimonials:\n  - quote: Great\n"
        "    name: Lin\n    role: Docs lead\n    avatar: /a.svg\n    link: https://example.com/\n```"
    )
    assert "md-home__quote-body" in html
    assert "md-home__quote-avatar" in html
    assert "md-home__quote-role" in html
    assert "md-home__quote-rating" in html
    assert 'target="_blank"' in html


def test_testimonials_need_a_quote():
    assert "needs a `quote`" in render("```homepage-testimonials\ntestimonials:\n  - name: A\n```")


def test_logos_use_the_brand_set_and_can_marquee():
    html = render(
        "```homepage-logos\nstyle: marquee\nlogos:\n  - simple/github | GitHub | https://github.com\n"
        "  - simple/python | Python\n```"
    )
    assert "md-home__icon--simple" in html
    assert "md-home__logo-name" in html
    assert 'href="https://github.com"' in html
    # One list, four rows: two periods on a SINGLE flex line. Wrapping each period
    # in its own box put the seam on a different flex line from the logos, so the
    # seam spacing and the logo spacing were computed independently and could
    # never match -- which is what made the loop jump.
    assert html.count("md-home__logos-list") == 1
    assert html.count('class="md-home__logo-item"') == 4
    assert "md-home__marquee-item" not in html
    # The scrolling pass is decoration: out of the accessibility tree *and* out of
    # the tab order, or a keyboard user walks every brand twice. Only the linked
    # one is focusable, so only it needs the skip.
    assert html.count('<li class="md-home__logo-item" aria-hidden="true">') == 2
    assert html.count('tabindex="-1"') == 1


def test_the_marquee_copy_is_hidden_but_still_rendered():
    """A single logo still needs a second period, or there is nothing to loop."""
    html = render("```homepage-logos\nstyle: marquee\nlogos:\n  - simple/python | Python\n```")
    assert html.count('class="md-home__logo-item"') == 2
    assert html.count('class="md-home__logo-item" aria-hidden="true"') == 1
    assert html.count("md-home__logo-name") == 2


def test_a_non_marquee_row_is_rendered_once():
    for style in ("row", "grid"):
        html = render(
            f"```homepage-logos\nstyle: {style}\nlogos:\n  - simple/python | Python\n"
            "  - simple/rust | Rust\n```"
        )
        assert html.count('class="md-home__logo-item"') == 2, style
        assert "md-home__logo-item\" aria-hidden" not in html, style
        assert "tabindex" not in html, style


def test_logos_accept_images_too():
    """An image logo is written as a mapping; the pipe form is for icon marks."""
    html = render(
        "```homepage-logos\nlogos:\n  - image: /logo.svg\n    name: Acme\n    link: /\n```"
    )
    assert '<img class="md-home__mark-img" src="/logo.svg"' in html
    assert "md-home__logo-name" in html
    assert "Acme" in html


def test_a_marquee_loads_its_images_eagerly():
    """`lazy` is wrong for a strip whose content is about to scroll into view.

    Measured in the browser: the second copy's image sat at `complete: false`
    with a 0x0 natural size, so it popped in mid-loop instead of being there.
    A row or a grid may be far down a page and keeps the deferral.
    """
    marquee = render(
        "```homepage-logos\nstyle: marquee\nlogos:\n  - image: /a.svg\n    name: A\n```"
    )
    assert marquee.count('loading="eager"') == 2
    assert "lazy" not in marquee

    row = render("```homepage-logos\nlogos:\n  - image: /a.svg\n    name: A\n```")
    assert 'loading="lazy"' in row


def test_logos_need_a_list():
    assert "needs a `logos:` list" in render("```homepage-logos\ntitle: nothing\n```")


def test_cta_is_centred_and_decorated_by_default():
    html = render("```homepage-cta\ntitle: Join us\nactions:\n  - Go | /go/\n---\nbody\n```")
    assert "md-home__cta--centred" in html
    assert "md-home--pattern-aurora" in html
    assert "md-home__cta-body" in html


def test_a_band_pattern_can_be_switched_off():
    html = render("```homepage-cta\npattern: none\ntitle: Plain\n```")
    assert "md-home--pattern-" not in html


def test_pattern_is_reported_when_unknown(caplog):
    with caplog.at_level(logging.WARNING, logger="mkdocs.plugins.homepage"):
        html = render("```homepage-cta\npattern: lava\ntitle: x\n```")
    assert "md-home--pattern-lava" not in html
    assert any("unknown pattern" in record.getMessage() for record in caplog.records)


@pytest.mark.parametrize(
    "pattern", ["aurora", "grid", "dots", "rays"]
)
def test_every_pattern_is_a_band(pattern):
    html = render(f"```homepage-text\npattern: {pattern}\ntitle: x\n---\ny\n```")
    assert f"md-home--pattern-{pattern}" in html


# -- hero extras -----------------------------------------------------------
def test_hero_highlights_and_note():
    html = render(
        "```homepage-hero\ntitle: T\nnote: MIT licensed\nhighlights:\n"
        "  - 16 | blocks | view-dashboard-outline\n  - 0 | deps\n```"
    )
    assert "md-home__highlights" in html
    assert "md-home__highlight-value" in html
    assert "md-home__highlight-icon" in html
    assert "md-home__note" in html


def test_hero_frame_is_a_figure_modifier():
    """One frame vocabulary, so `frame: browser` means the same in every block."""
    hero = render("```homepage-hero\ntitle: T\nimage: /a.svg\nimage_frame: browser\n```")
    showcase = render(
        "```homepage-showcase\nshowcase:\n  - title: A\n    image: /a.svg\n    frame: browser\n```"
    )
    for html in (hero, showcase):
        assert "md-home__figure--browser" in html
        # ... and the frame is on the figure, not on a wrapper around it.
        assert re.search(r'<figure class="md-home__figure[^"]*--browser', html)


def test_shadow_and_glow_land_on_the_figure():
    html = render("```homepage-image\nsrc: /a.svg\nshadow: true\nglow: true\n```")
    assert "md-home__figure--shadow" in html
    assert "md-home__figure--glow" in html


# -- escaping and sanitisation --------------------------------------------
def test_titles_are_escaped():
    html = render('```homepage-cards\ncards:\n  - title: "<script>alert(1)</script>"\n```')
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_descriptions_accept_inline_markdown():
    html = render('```homepage-cards\ncards:\n  - title: A\n    desc: "**bold** and `code`"\n```')
    assert "<strong>bold</strong>" in html
    assert "<code>code</code>" in html


def test_a_block_level_title_falls_back_to_escaped_text():
    html = render('```homepage-cards\ncards:\n  - title: "# not a heading"\n```')
    assert "<h1" not in html
    assert "# not a heading" in html


def test_javascript_urls_are_dropped():
    html = render("```homepage-cards\ncards:\n  - title: A\n    link: \"javascript:alert(1)\"\n```")
    assert "javascript:" not in html
    assert "href=" not in html


def test_data_urls_are_dropped():
    html = render("```homepage-image\nsrc: \"data:text/html;base64,PHNjcmlwdD4=\"\n```")
    assert "data:" not in html


def test_style_props_are_whitelisted():
    html = render("```homepage-image\nsrc: /a.svg\nfloat_width: 40%;color:red\n```")
    assert "color:red" not in html


def test_unan_safe_column_count_is_ignored():
    html = render('```homepage-cards\ncolumns: "3; color: red"\ncards:\n  - title: A\n```')
    assert "color:red" not in html
    assert "data-home-cols" not in html


def test_class_prop_cannot_break_out_of_the_attribute():
    """A `class:` value is a class list, never a way to add an attribute."""
    html = render("```homepage-text\nclass: 'ok\" onmouseover=\"x <b>'\n---\nx\n```")
    assert 'onmouseover="' not in html
    assert "<b>" not in html
    assert 'class="md-home ok onmouseoverx b md-home--text"' in html


# -- Markdown parity -------------------------------------------------------
def test_admonitions_render_inside_a_block():
    html = render('```homepage-text\n---\n!!! note "Hi"\n    body\n```')
    assert 'class="admonition note"' in html
    assert "admonition-title" in html


def test_body_tables_render():
    html = render("```homepage-text\n---\n| a | b |\n| - | - |\n| 1 | 2 |\n```")
    assert "<table>" in html


def test_toc_is_excluded_so_headings_get_no_permalinks():
    html = render("```homepage-text\n---\n## Title\n```")
    assert "headerlink" not in html
    assert "permalink" not in html


def test_meta_is_excluded_so_props_like_prose_is_not_eaten():
    html = render("```homepage-text\n---\nkey: value\n\nmore\n```")
    assert "key: value" in html


def test_our_own_extension_does_not_recurse():
    html = render("```homepage-text\n---\n````text\n```homepage-cards\n````\n```")
    assert "homepage-cards" in html


def test_blocks_are_free_of_theme_scale_leaks():
    """Headings keep the widget's own scale instead of Material's `rem` sizes."""
    html = render("```homepage-cards\ntitle: Section\ncards:\n  - title: A\n```")
    assert '<h2 class="md-home__title">Section</h2>' in html


def test_options_can_disable_the_tilt_and_the_lightbox():
    html = render("```homepage-cards\ncards:\n  - title: A\n```", options={"tilt": False})
    assert "data-home-tilt" not in html


def test_options_can_change_the_tilt_strength():
    html = render("```homepage-cards\ncards:\n  - title: A\n```", options={"tilt_strength": 10})
    assert 'data-home-tilt="10"' in html


def test_reveal_auto_only_animates_lists():
    listy = render("```homepage-cards\ncards:\n  - title: A\n```")
    prose = render("```homepage-text\n---\nx\n```")
    assert "data-home-reveal" in listy
    assert "data-home-reveal" not in prose


def test_reveal_auto_can_be_switched_off_site_wide():
    html = render("```homepage-cards\ncards:\n  - title: A\n```", options={"reveal": "off"})
    assert "data-home-reveal" not in html


# -- diagnostics -----------------------------------------------------------
def test_a_broken_block_is_visible_with_its_reason(caplog):
    with caplog.at_level(logging.WARNING, logger="mkdocs.plugins.homepage"):
        html = render("```homepage-cards\ncards:\n  - title: A\n    desc: a: b\n```")
    assert "md-home--error" in html
    assert "YAML" in html
    assert "line 1" in html
    # Reported once, not twice: the parser already named the line.
    messages = [record.getMessage() for record in caplog.records]
    assert sum("test.md:1" in message for message in messages) == 1


def test_unknown_icon_is_reported(caplog):
    with caplog.at_level(logging.WARNING, logger="mkdocs.plugins.homepage"):
        html = render("```homepage-cards\ncards:\n  - title: A\n    icon: nope\n```")
    assert "md-home__icon--missing" in html
    assert any("unknown icon" in record.getMessage() for record in caplog.records)
