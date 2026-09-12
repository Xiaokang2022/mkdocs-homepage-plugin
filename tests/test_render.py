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


@pytest.mark.parametrize("kind", sorted(SAMPLES))
def test_every_kind_renders_without_an_error_marker(kind):
    html = render(SAMPLES[kind])
    assert f"md-home--{kind}" in html
    assert "md-home--error" not in html


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
    assert '<img src="/logo.svg"' in html
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
