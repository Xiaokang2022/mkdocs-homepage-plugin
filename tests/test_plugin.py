"""The MkDocs plugin: config wiring, asset registration, and option handling."""

from __future__ import annotations

import os

import pytest
from mkdocs.config.base import ValidationError
from mkdocs.structure.files import Files

from mkdocs_homepage.plugin import (
    ASSETS,
    EXTENSION_ENTRY,
    HomepagePlugin,
    Number,
)


class _Plugins:
    _current_plugin = "homepage"


class _Config(dict):
    """The subset of MkDocsConfig the plugin touches."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.site_dir = kwargs.get("site_dir", "site")
        self.use_directory_urls = kwargs.get("use_directory_urls", True)
        self.plugins = _Plugins()


def make_plugin(**options):
    plugin = HomepagePlugin()
    # MkDocs assigns `plugin.config` in `load_config`, so a bare instance has none.
    plugin.load_config(options)
    return plugin


def make_config(**overrides):
    config = _Config(
        markdown_extensions=["admonition", "toc"],
        mdx_configs={"toc": {"permalink": True}},
        extra_css=["assets/custom.css"],
        extra_javascript=[],
    )
    config.update(overrides)
    return config


# -- config wiring ---------------------------------------------------------
def test_extension_is_registered_with_the_sites_own_setup():
    plugin = make_plugin()
    config = plugin.on_config(make_config())
    assert config["markdown_extensions"][-1] == EXTENSION_ENTRY
    options = config["mdx_configs"][EXTENSION_ENTRY]
    # The site's own extensions are threaded through, minus ourselves.
    assert options["extensions"] == ["admonition", "toc"]
    assert options["extension_configs"] == {"toc": {"permalink": True}}


def test_registering_twice_does_not_duplicate():
    plugin = make_plugin()
    config = make_config()
    plugin.on_config(config)
    plugin.on_config(config)
    assert config["markdown_extensions"].count(EXTENSION_ENTRY) == 1


def test_an_explicitly_listed_extension_is_not_added_again():
    plugin = make_plugin()
    config = make_config(markdown_extensions=[EXTENSION_ENTRY])
    plugin.on_config(config)
    assert config["markdown_extensions"] == [EXTENSION_ENTRY]


def test_the_extension_can_be_switched_off():
    plugin = make_plugin(markdown_extension=False)
    config = plugin.on_config(make_config())
    assert EXTENSION_ENTRY not in config["markdown_extensions"]


def test_assets_are_appended_without_clobbering_the_site():
    plugin = make_plugin()
    config = plugin.on_config(make_config())
    assert config["extra_css"] == ["assets/custom.css", "assets/homepage.css"]
    assert config["extra_javascript"] == ["assets/homepage.js"]


def test_assets_can_be_switched_off():
    plugin = make_plugin(assets=False)
    config = plugin.on_config(make_config())
    assert config["extra_css"] == ["assets/custom.css"]
    assert config["extra_javascript"] == []


def test_assets_dir_customisation_and_traversal_are_handled():
    plugin = make_plugin(assets_dir="/static/homepage/")
    config = plugin.on_config(make_config())
    assert config["extra_css"][-1] == "static/homepage/homepage.css"

    plugin = make_plugin(assets_dir="../../etc")
    config = plugin.on_config(make_config())
    assert config["extra_css"][-1] == "etc/homepage.css"


def test_plugin_options_reach_the_extension():
    plugin = make_plugin(tilt=False, tilt_strength=12, reveal="up", lightbox=False, count=False)
    config = plugin.on_config(make_config())
    options = config["mdx_configs"][EXTENSION_ENTRY]["options"]
    assert options == {
        "tilt": False,
        "tilt_strength": 12.0,
        "reveal": "up",
        "lightbox": False,
        "count": False,
    }


# -- files -----------------------------------------------------------------
def test_assets_are_added_to_the_site():
    plugin = make_plugin()
    config = plugin.on_config(make_config())
    files = plugin.on_files(Files([]), config)
    uris = sorted(file.src_uri for file in files)
    assert uris == [f"assets/{name}" for name in sorted(ASSETS)]
    for file in files:
        assert os.path.isfile(file.abs_src_path)
        assert file.dest_uri.startswith("assets/")


def test_asset_registration_is_idempotent():
    plugin = make_plugin()
    config = plugin.on_config(make_config())
    files = plugin.on_files(Files([]), config)
    again = plugin.on_files(files, config)
    assert len(again) == len(ASSETS)


def test_assets_are_not_added_when_switched_off():
    plugin = make_plugin(assets=False)
    config = plugin.on_config(make_config())
    assert len(plugin.on_files(Files([]), config)) == 0


# -- css_vars --------------------------------------------------------------
def test_css_vars_are_injected_into_the_head():
    plugin = make_plugin(css_vars={"--md-home-radius": "1rem", "--md-home-gap": "12px"})
    plugin.on_config(make_config())
    output = plugin.on_post_page("<html><head><title>x</title></head><body></body></html>")
    assert ":root{--md-home-radius:1rem;--md-home-gap:12px;}" in output
    assert output.index("<style>") < output.index("</head>")


def test_css_vars_reject_a_breakout_attempt(caplog):
    plugin = make_plugin(
        css_vars={
            "not-a-custom-property": "red",
            "--md-home-radius": "1rem;} body{display:none",
            "--md-home-gap": "1rem",
        }
    )
    plugin.on_config(make_config())
    output = plugin.on_post_page("<html><head></head></html>")
    assert "display:none" not in output
    assert output.count("--md-home-gap") == 1
    messages = [record.getMessage() for record in caplog.records]
    assert any("ignoring css_vars" in message for message in messages)


def test_no_css_vars_means_no_style_tag():
    plugin = make_plugin()
    plugin.on_config(make_config())
    output = "<html><head></head></html>"
    assert plugin.on_post_page(output) == output


# -- the Number option -----------------------------------------------------
@pytest.mark.parametrize("value", [6, 6.5, "7", " 8.25 "])
def test_number_accepts_anything_numeric(value):
    assert Number(default=6.0).validate(value) == float(str(value).strip())


@pytest.mark.parametrize("value", [True, False, "abc", None, [1]])
def test_number_rejects_the_rest(value):
    with pytest.raises(ValidationError):
        Number(default=6.0).validate(value)


def test_number_default_is_kept():
    assert Number(default=6.0).default == 6.0


# -- page context ----------------------------------------------------------
class _File:
    src_uri = "docs/index.md"


class _Page:
    file = _File()
    url = ""


def test_page_context_is_set_and_then_cleared():
    from mkdocs_homepage.context import current_page, current_page_source

    plugin = make_plugin()
    plugin.on_page_markdown("# hi", page=_Page(), files="FILES")
    assert current_page_source() == "docs/index.md"
    assert current_page().files == "FILES"
    plugin.on_page_content("<p>hi</p>")
    assert current_page_source() is None


def test_page_markdown_is_returned_unchanged():
    plugin = make_plugin()
    text = "# hi\n\n```homepage-cards\ncars: []\n```\n".replace("cars", "cards")
    assert plugin.on_page_markdown(text, page=_Page(), files=None) == text


# -- URL resolution --------------------------------------------------------
class _Files:
    """Just enough of `mkdocs.structure.files.Files` for `resolve_url`."""

    def __init__(self, mapping):
        self._mapping = mapping

    def get_file_from_path(self, path):
        return self._mapping.get(path)


class _Target:
    def __init__(self, url):
        self.url = url


@pytest.fixture
def page_context():
    from mkdocs_homepage.context import PageContext, clear_page_context, set_page_context

    files = _Files(
        {
            "guide/index.md": _Target("guide/"),
            "guide/blocks.md": _Target("guide/blocks/"),
            "index.md": _Target("./"),
            "assets/logo.png": _Target("assets/logo.png"),
        }
    )
    set_page_context(PageContext(src_uri="guide/blocks.md", url="guide/blocks/", files=files))
    yield
    clear_page_context()


def test_markdown_links_are_resolved_like_the_page_body(page_context):
    from mkdocs_homepage.context import resolve_url

    # From `guide/blocks.md`: `../index.md` is the root index, which is at `./`.
    assert resolve_url("../index.md") == "../../"
    # A sibling inside `guide/` is one level up from `guide/blocks/`.
    assert resolve_url("index.md") == "../"


def test_anchors_and_queries_are_preserved(page_context):
    from mkdocs_homepage.context import resolve_url

    assert resolve_url("../index.md#top") == "../../#top"
    assert resolve_url("../index.md?x=1") == "../../?x=1"


def test_assets_are_resolved_to_their_url(page_context):
    from mkdocs_homepage.context import resolve_url

    assert resolve_url("../assets/logo.png") == "../../assets/logo.png"


def test_a_link_outside_the_docs_directory_is_left_alone(page_context, caplog):
    from mkdocs_homepage.context import resolve_url

    assert resolve_url("../../index.md") == "../../index.md"
    assert any("does not match" in record.getMessage() for record in caplog.records)


@pytest.mark.parametrize(
    "value",
    ["https://example.com/", "mailto:a@b.c", "//cdn.example.com/x", "/absolute/", "#anchor", ""],
)
def test_urls_that_are_left_alone(page_context, value):
    from mkdocs_homepage.context import resolve_url

    assert resolve_url(value) == value


def test_an_unknown_markdown_link_is_reported_and_left_as_is(page_context, caplog):
    from mkdocs_homepage.context import resolve_url

    assert resolve_url("nope.md") == "nope.md"
    messages = [record.getMessage() for record in caplog.records]
    assert any("does not match any file" in message for message in messages)


def test_without_a_page_context_nothing_is_rewritten():
    from mkdocs_homepage.context import clear_page_context, resolve_url

    clear_page_context()
    assert resolve_url("guide/index.md") == "guide/index.md"
