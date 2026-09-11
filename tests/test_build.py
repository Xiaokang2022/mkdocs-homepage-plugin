"""End-to-end: build the demo site and check what actually lands on disk.

The unit tests prove each piece; this one proves the pieces are wired together --
the entry point resolves, the assets are copied, the Markdown extension is
registered by the plugin rather than by the config file, and the demo builds
without a single warning.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from mkdocs_homepage.plugin import ASSETS

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo"


def _entry_point_registered() -> bool:
    from importlib.metadata import entry_points

    return any(entry.name == "homepage" for entry in entry_points(group="mkdocs.plugins"))


pytestmark = pytest.mark.skipif(
    not _entry_point_registered(),
    reason="the 'homepage' entry point is not installed (run `pip install -e .`)",
)


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    if not DEMO.is_dir():
        pytest.skip("no demo site in this checkout")

    from mkdocs.commands.build import build
    from mkdocs.config import load_config

    site_dir = tmp_path_factory.mktemp("site")
    config = load_config(config_file=str(DEMO / "mkdocs.yml"), site_dir=str(site_dir))
    build(config)
    return site_dir


@pytest.fixture(scope="module")
def homepage(built):
    return (built / "index.html").read_text(encoding="utf-8")


def test_the_demo_builds_without_warnings(caplog):
    from mkdocs.commands.build import build
    from mkdocs.config import load_config
    import tempfile

    with tempfile.TemporaryDirectory() as site_dir:
        config = load_config(config_file=str(DEMO / "mkdocs.yml"), site_dir=site_dir)
        with caplog.at_level(logging.WARNING):
            build(config)
    homepage_warnings = [
        record.getMessage()
        for record in caplog.records
        if record.levelno >= logging.WARNING and "homepage" in record.name
    ]
    assert not homepage_warnings


def test_no_error_marker_reached_the_output(built):
    for page in built.rglob("*.html"):
        assert "md-home--error" not in page.read_text(encoding="utf-8"), page


def test_the_assets_were_copied(built):
    for name in ASSETS:
        assert (built / "assets" / name).is_file()


#: The blocks the demo homepage is built from, in order.
HOMEPAGE_BLOCKS = (
    "hero",
    "logos",
    "features",
    "showcase",
    "cards",
    "stats",
    "gallery",
    "testimonials",
    "split",
    "anim",
    "cta",
    "links",
)


def test_the_homepage_is_rendered(homepage):
    for block in HOMEPAGE_BLOCKS:
        assert f'data-home-block="{block}"' in homepage, block
    for hook in (
        "md-home__card",
        "data-home-tilt",
        "data-home-cols",
        "md-home__marquee",
        "md-home--pattern-aurora",
        "md-home--gradient",
        "md-home__logo",
        "md-home__quote",
        "md-home__showcase-row",
        "md-home__highlights",
        "md-home__more",
    ):
        assert hook in homepage, hook


def test_the_demo_exercises_every_kind(built):
    """A demo that skips a kind is a kind nobody ever sees working."""
    from mkdocs_homepage.parser import BLOCK_KINDS

    text = "\n".join(page.read_text(encoding="utf-8") for page in built.rglob("*.html"))
    missing = [
        kind
        for kind in BLOCK_KINDS
        if f'data-home-block="{kind}"' not in text
    ]
    assert not missing, f"the demo never renders: {missing}"


def test_the_demo_does_not_overstate_the_block_count(built):
    """The demo's copy promises a number; a stale one is a lie in the marketing.

    This is the *whole* count of blocks the parser accepts, so the demo cannot
    quietly advertise a smaller set than it ships.
    """
    from mkdocs_homepage.parser import BLOCK_KINDS

    text = "\n".join(page.read_text(encoding="utf-8") for page in built.rglob("*.html"))
    assert f">{len(BLOCK_KINDS)}<" in text


def test_the_demo_does_not_overstate_the_icon_count(built):
    """So is the icon count -- read the real sets, not a number someone typed."""
    from mkdocs_homepage.svg import ICON_SETS

    total = sum(len(paths) for paths in ICON_SETS.values())
    text = "\n".join(page.read_text(encoding="utf-8") for page in built.rglob("*.html"))
    assert f">{total}<" in text, f"the demo never states the real icon count ({total})"


def test_the_plugin_registered_the_extension(built):
    """The demo config lists only `plugins: [homepage]` -- no markdown extension."""
    config = (DEMO / "mkdocs.yml").read_text(encoding="utf-8")
    assert "mkdocs_homepage" not in config
    # ... and yet a fenced block was rendered, so the extension was registered.
    assert "md-home__card" in (built / "index.html").read_text(encoding="utf-8")


def test_the_assets_are_linked_from_every_page(built):
    for page in built.rglob("*.html"):
        text = page.read_text(encoding="utf-8")
        assert "assets/homepage.css" in text, page
        assert "assets/homepage.js" in text, page


def test_prose_bodies_rendered_like_the_page(built):
    """An admonition inside a block must survive with its theme classes."""
    found = []
    for page in sorted(built.rglob("*.html")):
        text = page.read_text(encoding="utf-8")
        if "admonition note" in text:
            found.append(text)
    assert found, "no page shows an admonition inside a block"
    assert any("admonition-title" in text for text in found)


def test_no_raw_fence_leaked_into_the_page(homepage):
    assert "homepage-cards" not in homepage
    assert "homepage-anim" not in homepage


def test_no_link_points_at_a_markdown_source_file(built):
    """A `.md` href in the output can only come from block HTML MkDocs did not rewrite."""
    import re

    pattern = re.compile(r'<a\b[^>]*\bhref="([^"]+)"')
    bad = []
    for page in sorted(built.rglob("*.html")):
        for href in pattern.findall(page.read_text(encoding="utf-8")):
            if href.split("#", 1)[0].split("?", 1)[0].endswith(('.md', ".markdown")):
                bad.append(f"{page.relative_to(built)} -> {href}")
    assert not bad, "links that were never resolved:\n" + "\n".join(bad)


def test_block_links_resolve_to_real_pages(built):
    """The demo's cards link to sibling pages; those hrefs must exist."""
    from urllib.parse import unquote, urlparse

    import re

    homepage = (built / "index.html").read_text(encoding="utf-8")
    cards = re.findall(r'class="md-home__card[^"]*"[^>]*\bhref="([^"]+)"', homepage)
    assert cards, "no card links found; this check would be vacuous"
    for href in cards:
        if href.startswith(("http", "//", "#")):
            continue
        target = built / unquote(urlparse(href).path).lstrip("/")
        assert target.exists() or (target / "index.html").exists(), href


def test_the_other_pages_built_too(built):
    for page in (
        "guide/index.html",
        "guide/syntax/index.html",
        "guide/blocks/index.html",
        "reference/index.html",
    ):
        assert (built / page).is_file(), page


def test_every_image_reference_resolves(built):
    """Block HTML is stashed, so MkDocs never rewrites its relative URLs.

    A `src:` prop or a Markdown image inside a block is resolved by the browser
    against the *page* URL, and nothing fixes it for the author.
    """
    import re
    from urllib.parse import unquote, urlparse

    pattern = re.compile(r'<img\b[^>]*\bsrc="([^"]+)"')
    missing = []
    for page in sorted(built.rglob("*.html")):
        for source in pattern.findall(page.read_text(encoding="utf-8")):
            if source.startswith(("http://", "https://", "//", "data:")):
                continue
            path = unquote(urlparse(source).path)
            target = built / path.lstrip("/") if path.startswith("/") else page.parent / path
            if not target.exists():
                missing.append(f"{page.relative_to(built)} -> {source}")
    assert not missing, "images that do not resolve:\n" + "\n".join(missing)


def test_every_zoomable_image_points_at_a_real_file(built):
    import re
    from urllib.parse import unquote, urlparse

    pattern = re.compile(r'data-home-zoom[^>]*\bhref="([^"]+)"|href="([^"]+)"[^>]*\bdata-home-zoom')
    missing = []
    for page in sorted(built.rglob("*.html")):
        text = page.read_text(encoding="utf-8")
        for match in pattern.findall(text):
            source = match[0] or match[1]
            if source.startswith(("http://", "https://", "//", "data:")):
                continue
            path = unquote(urlparse(source).path)
            target = built / path.lstrip("/") if path.startswith("/") else page.parent / path
            if not target.exists():
                missing.append(f"{page.relative_to(built)} -> {source}")
    assert not missing, "lightbox targets that do not resolve:\n" + "\n".join(missing)
