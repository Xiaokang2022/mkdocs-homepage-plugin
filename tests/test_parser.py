"""Parsing: fences, the props/body split, and the diagnostics."""

from __future__ import annotations

import logging

import pytest

from mkdocs_homepage.parser import (
    Block,
    canonical_kind,
    is_fence_info,
    normalize_pattern,
    normalize_reveal,
    normalize_theme,
    split_blocks,
    split_panels,
    top_level_fence_offset,
)

PLAIN = "# Title\n\nSome prose.\n\n- a\n- b\n"


def test_document_without_fences_is_returned_verbatim():
    assert split_blocks(PLAIN) == [PLAIN]


def test_plain_text_around_a_block_is_preserved(blocks):
    segments = blocks("before\n\n```homepage-text\n---\nbody\n```\n\nafter\n")
    assert len(segments) == 3
    assert segments[0] == "before\n\n"
    assert segments[2] == "\nafter\n"
    assert isinstance(segments[1], Block)
    assert segments[1].kind == "text"
    assert segments[1].body == "body"


def test_split_round_trips_the_document(blocks):
    """Splitting must not lose or invent a single character of the page."""
    fence = "```homepage-divider\nstyle: line\n```"
    text = f"head\n\n{fence}\n\nmiddle\n\n{fence}\n\ntail\n"
    segments = blocks(text)
    assert [s.kind for s in segments if isinstance(s, Block)] == ["divider", "divider"]
    # Every fence became a block; everything else survived untouched.
    rebuilt = "".join(s for s in segments if isinstance(s, str))
    removed = "\n".join(["head", ""] + ["", "middle", ""] + ["", "tail", ""])
    assert rebuilt == removed


def test_plain_text_chunks_reassemble_exactly(blocks):
    text = "head\n\n```homepage-divider\n```\n\ntail\n"
    segments = blocks(text)
    rebuilt = "".join(segment for segment in segments if isinstance(segment, str))
    assert rebuilt == "head\n\n\ntail\n"


def test_a_block_at_the_very_start_needs_no_leading_newline(blocks):
    segments = blocks("```homepage-divider\n```\n\nafter\n")
    assert [s for s in segments if isinstance(s, str)] == ["\nafter\n"]


def test_a_document_with_only_a_block_rebuilds_to_nothing(blocks):
    assert [s for s in blocks("```homepage-divider\n```") if isinstance(s, str)] == []


def test_props_and_body_split_on_the_first_hr(blocks):
    block = blocks("```homepage-text\ntitle: A\npanel: true\n---\n## Body\n**bold**\n```\n")[0]
    assert block.props == {"title": "A", "panel": True}
    assert block.body.strip() == "## Body\n**bold**"


def test_props_without_a_separator_are_detected(blocks):
    block = blocks("```homepage-cards\ncolumns: 3\ncards:\n  - title: A\n    desc: B\n```\n")[0]
    assert block.props["columns"] == 3
    assert block.body == ""


def test_prose_without_props_is_detected(blocks):
    block = blocks("```homepage-text\n## 标题\n\n正文 **粗体**\n```\n")[0]
    assert block.props == {}
    assert "正文" in block.body


def test_leading_hr_means_props_are_absent(blocks):
    block = blocks("```homepage-text\n---\n---\nis a horizontal rule\n```\n")[0]
    assert block.props == {}
    assert block.body.startswith("---\nis a horizontal rule")


def test_a_non_homepage_fence_is_skipped_whole(blocks):
    text = "```homepage-cards\ncards:\n  - title: A\n```\n\n```python\nprint(1)\n```\n"
    segments = blocks(text)
    assert [segment.kind if isinstance(segment, Block) else "text" for segment in segments] == [
        "cards",
        "text",
    ]


def test_a_homepage_fence_inside_a_longer_fence_is_literal(blocks):
    text = "````text\n```homepage-cards\ncards:\n  - title: A\n```\n````\n"
    segments = blocks(text)
    assert len(segments) == 1
    assert isinstance(segments[0], str)


def test_nested_fence_inside_a_block_is_literal(blocks):
    body = "````text\n```homepage-cards\ncards: []\n```\n````"
    block = blocks(f"```homepage-text\n---\n{body}\n```\n")[0]
    assert "homepage-cards" in block.body


def test_tilde_fences_work(blocks):
    block = blocks("~~~homepage-divider\nstyle: dots\n~~~\n")[0]
    assert block.kind == "divider"


def test_crlf_line_endings(blocks):
    block = blocks("```homepage-text\r\ntitle: A\r\n---\r\nbody\r\n```\r\n")[0]
    assert block.props == {"title": "A"}


@pytest.mark.parametrize(
    ("info", "expected"),
    [
        ("homepage-cards", True),
        ("homepage", True),
        ("homepage_split", True),
        (" homepagesss ", False),
        ("homepages", False),
        ("", False),
        ("python", False),
    ],
)
def test_fence_info_detection(info, expected):
    assert is_fence_info(info) is expected


@pytest.mark.parametrize(
    ("token", "expected"),
    [
        ("cards", "cards"),
        ("card", "cards"),
        ("quick-links", "links"),
        ("quicklinks", "links"),
        ("carousel", "gallery"),
        ("columns", "split"),
        ("sections", "showcase"),
        ("spotlight", "showcase"),
        ("reviews", "testimonials"),
        ("users", "testimonials"),
        ("brands", "logos"),
        ("trust", "logos"),
        ("sponsor", "cta"),
        ("promo", "cta"),
        ("nope", None),
    ],
)
def test_kind_aliases(token, expected):
    assert canonical_kind(token) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [("aurora", "aurora"), ("grid", "grid"), ("dots", "dots"), ("rays", "rays"),
     ("none", None), ("plain", None), ("off", None), (True, "aurora"), (None, None)],
)
def test_normalize_pattern(value, expected):
    assert normalize_pattern(value) == expected


def test_a_pattern_can_be_switched_off_without_a_warning(caplog):
    """`pattern: none` used to warn that `none` is not a pattern.

    `normalize_pattern` answers "no pattern" with `None`, so the validator could
    not tell an explicit opt-out from a typo -- and `hero`/`cta` default to
    `aurora`, which makes switching it off the single most likely thing to write.
    The warning even listed `none` among the valid choices, which is how the
    contradiction stayed invisible.
    """
    from tests.conftest import render

    for spelling in ("none", "off", "false", "plain", "", "None"):
        with caplog.at_level(logging.WARNING, logger="mkdocs.plugins.homepage"):
            html = render(f"```homepage-hero\ntitle: A\npattern: '{spelling}'\n```")
        assert "unknown pattern" not in caplog.text, spelling
        assert "md-home--pattern-" not in html, spelling
        assert "md-home--error" not in html, spelling
        caplog.clear()

    # ...while a genuine typo still warns, and names the choices.
    with caplog.at_level(logging.WARNING, logger="mkdocs.plugins.homepage"):
        render("```homepage-hero\ntitle: A\npattern: aurorra\n```")
    assert "unknown pattern" in caplog.text
    assert "aurora" in caplog.text


def test_every_named_pattern_is_reachable():
    """`none` is in `PATTERNS`, so it may not be the one value that always warns."""
    from mkdocs_homepage.parser import PATTERNS, PATTERN_OPTOUT
    from tests.conftest import render

    assert "none" in PATTERNS
    for pattern in sorted(PATTERNS - PATTERN_OPTOUT):
        html = render(f"```homepage-hero\ntitle: A\npattern: {pattern}\n```")
        assert f"md-home--pattern-{pattern}" in html, pattern


def test_unknown_kind_is_reported_and_kept(blocks, caplog):
    with caplog.at_level(logging.WARNING, logger="mkdocs.plugins.homepage"):
        block = blocks("```homepage-nonsense\ntitle: A\n```\n")[0]
    assert block.issue is not None
    assert "unknown block type" in block.issue
    assert any("unknown block type" in record.getMessage() for record in caplog.records)


def test_missing_kind_is_reported(blocks):
    block = blocks("```homepage\ntitle: A\n```\n")[0]
    assert block.issue is not None
    assert "missing block type" in block.issue


def test_declared_type_prop_selects_the_kind(blocks):
    block = blocks("```homepage\ntype: hero\ntitle: A\n```\n")[0]
    assert block.issue is None
    assert block.kind == "hero"


def test_broken_yaml_keeps_the_block_with_an_issue(blocks):
    block = blocks('```homepage-cards\ncards:\n  - title: A\n    desc: span: 2\n```\n')[0]
    assert block.issue is not None
    assert "YAML" in block.issue
    # The block is kept so the page can show a marker where it went wrong.
    assert "desc: span: 2" in block.body


def test_unknown_theme_warns_and_falls_back(blocks, caplog):
    with caplog.at_level(logging.WARNING, logger="mkdocs.plugins.homepage"):
        block = blocks("```homepage-text\ntheme: chartreuse\n---\nx\n```\n")[0]
    assert block.props["theme"] is None
    assert any("unknown theme" in record.getMessage() for record in caplog.records)


def test_unterminated_fence_is_reported(blocks, caplog):
    with caplog.at_level(logging.WARNING, logger="mkdocs.plugins.homepage"):
        segments = blocks("```homepage-text\n---\nbody\n")
    assert all(isinstance(segment, str) for segment in segments)
    assert any("unterminated" in record.getMessage() for record in caplog.records)


def test_missing_closing_fence_before_another_block_is_reported(blocks, caplog):
    text = "```homepage-anim\neffect: marquee\n---\nhello\n\n```homepage-links\nlinks: []\n```\n"
    with caplog.at_level(logging.WARNING, logger="mkdocs.plugins.homepage"):
        blocks(text)
    messages = [record.getMessage() for record in caplog.records]
    assert any("closing" in message for message in messages)


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ("effect: marquee\n---\nhello\n\n```homepage-links\nx\n```\n", 4),
        ("text\n\n````text\n```homepage-cards\nx\n````\n", None),
        ("just prose", None),
        ("```homepage-cards\nunclosed", 0),
    ],
)
def test_top_level_fence_offset(body, expected):
    assert top_level_fence_offset(body) == expected


def test_split_panels():
    assert split_panels("a\n===\nb\n+++\nc") == ["a", "b", "c"]


def test_split_panels_needs_a_whole_line():
    assert split_panels("a === b") == ["a === b"]


@pytest.mark.parametrize(
    ("value", "expected"),
    [(True, "up"), (False, None), ("zoom", "zoom"), ("none", None), ("", None), (None, None)],
)
def test_normalize_reveal(value, expected):
    assert normalize_reveal(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [("cyan", "cyan"), ("  TEAL ", "teal"), ("grey", "blue-grey"), ("default", None), ("x", None)],
)
def test_normalize_theme(value, expected):
    assert normalize_theme(value) == expected
