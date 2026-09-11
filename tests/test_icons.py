"""Icons: the copied paths, and the guards that keep them copied correctly.

Two failure modes motivated this file, and both are invisible at a glance:

* a call site renamed while the table was not, which renders ``<path d="undefined">``
  -- a valid, empty SVG, with no error anywhere;
* a long path split across two string literals for line length, which drops the
  whitespace *separator* between two numbers and quietly changes the glyph.
"""

from __future__ import annotations

import importlib.util
import logging
import re
from pathlib import Path

import pytest

from mkdocs_homepage.icons import BRAND_PATHS, ICON_PATHS, ICON_SETS
from mkdocs_homepage.parser import Block, split_blocks
from mkdocs_homepage.svg import icon, icon_names, resolve

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "mkdocs_homepage"
DEMO = ROOT / "demo"

#: A literal `icon("...")` / `icon_span("...")` call site.
CALL_SITE_RE = re.compile(r"\bicon(?:_span)?\(\s*\"([^\"]+)\"")
#: An SVG `d` attribute, as one string literal, is the only place a path may live.
PATH_LITERAL_RE = re.compile(r'^\s+"([MmLlHhVvCcSsQqTtAaZz][^"]*)",?$', re.M)

#: SVG path tokeniser.  Whitespace is a *separator* in path data, not decoration,
#: so the tokens -- not a whitespace-stripped string -- are what must be compared.
TOKEN_RE = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]|-?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")


def tokenize(path: str) -> list:
    return TOKEN_RE.findall(path)


def material_icon_dir() -> str | None:
    try:
        import material
    except ImportError:
        return None
    path = Path(material.__file__).parent / "templates" / ".icons" / "material"
    return str(path) if path.is_dir() else None


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "_generate_icons", ROOT / "scripts" / "generate_icons.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# -- shape -----------------------------------------------------------------
def test_every_entry_is_a_viewbox_and_a_tuple_of_paths():
    for name, entry in ICON_PATHS.items():
        assert isinstance(entry, tuple) and len(entry) == 2, name
        viewbox, paths = entry
        assert isinstance(viewbox, str) and re.fullmatch(r"[-\d. ]+", viewbox), name
        # The regression this guards: a bare string is iterated character by
        # character at render time, emitting one <path d="m"/> per letter.
        assert isinstance(paths, tuple), f"{name}: paths must be a tuple, not {type(paths)}"
        assert paths and all(isinstance(path, str) for path in paths), name
        assert all(path.startswith(tuple("MmLlHhVvCcSsQqTtAaZz")) for path in paths), name


def test_every_path_is_one_string_literal():
    """A path wrapped across `"..." + "..."` loses the separator between numbers."""
    source = (PACKAGE / "icons.py").read_text(encoding="utf-8")
    literals = PATH_LITERAL_RE.findall(source)
    total = sum(len(paths) for _, paths in ICON_PATHS.values()) + sum(
        len(paths) for _, paths in BRAND_PATHS.values()
    )
    assert literals and len(literals) == total
    # No concatenation on a path: one path, one literal.
    assert not re.search(r'^\s*"[MmLlHhVvCcSsQqTtAaZz][^"]*"\s*\+', source, re.M)


def test_the_tokeniser_tells_two_different_paths_apart():
    """Positive control: without this, the comparison below could pass vacuously."""
    assert tokenize("c5 0 9.27") != tokenize("c5 09.27")
    assert tokenize("9.5 1.5") != tokenize("9.51.5")
    assert tokenize("m13.13 22.19-1.63-3.83") == tokenize("m13.13 22.19-1.63-3.83")
    assert tokenize("m13.13 22.19-1.63-3.83") != tokenize("m13.1322.19-1.63-3.83")


# -- the copy is faithful --------------------------------------------------
def test_paths_match_the_installed_material_theme_token_by_token():
    directory = material_icon_dir()
    if directory is None:
        pytest.skip("mkdocs-material is not installed; the widget does not need it")
    generator = load_generator()
    for set_name, names, table in (
        ("material", generator.ICON_NAMES, ICON_PATHS),
        ("simple", generator.BRAND_NAMES, BRAND_PATHS),
    ):
        set_dir = generator.set_directories().get(set_name)
        if set_dir is None:
            pytest.skip(f"the {set_name} icon set is not installed")
        for name in names:
            viewbox, expected = generator.read_icon(set_dir, name)
            actual_viewbox, actual = table[name]
            assert actual_viewbox == viewbox, name
            assert [tokenize(path) for path in actual] == [tokenize(path) for path in expected], name


def test_the_curated_set_is_fully_present():
    generator = load_generator()
    assert set(generator.ICON_NAMES) == set(ICON_PATHS)
    assert set(generator.BRAND_NAMES) == set(BRAND_PATHS)
    assert len(ICON_PATHS) == len(generator.ICON_NAMES)
    assert len(BRAND_PATHS) == len(generator.BRAND_NAMES)


# -- call sites ------------------------------------------------------------
def test_every_literal_icon_call_site_is_declared():
    found = {}
    sites = 0
    for path in sorted(PACKAGE.glob("*.py")):
        for name in CALL_SITE_RE.findall(path.read_text(encoding="utf-8")):
            sites += 1
            found.setdefault(name, []).append(path.name)
    # Positive control: if the scan stopped finding call sites the check below
    # would pass without testing anything.
    assert sites >= 4, f"the call-site scan found too few calls: {found}"
    undeclared = {name: files for name, files in found.items() if name not in ICON_PATHS}
    assert not undeclared, f"icon() called with names that are not in ICON_PATHS: {undeclared}"


def collect_icon_props(value, out):
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "icon" and isinstance(item, str):
                out.append(item)
            else:
                collect_icon_props(item, out)
    elif isinstance(value, list):
        for item in value:
            collect_icon_props(item, out)


def test_every_icon_used_in_the_demo_is_declared():
    if not DEMO.is_dir():
        pytest.skip("no demo site in this checkout")
    used = {}
    for path in sorted(DEMO.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        for segment in split_blocks(text, source=str(path)):
            if not isinstance(segment, Block):
                continue
            names = []
            collect_icon_props(segment.props, names)
            for name in names:
                used.setdefault(name, []).append(f"{path.name}:{segment.line}")
    assert used, "the demo uses no icons at all; this check would be vacuous"
    undeclared = {name: where for name, where in used.items() if name not in ICON_PATHS}
    assert not undeclared, f"the demo uses undeclared icons: {undeclared}"


# -- rendering -------------------------------------------------------------
def test_icon_renders_a_current_color_path():
    html = icon("close")
    assert 'class="md-icon"' in html
    assert "currentColor" not in html  # colour comes from `fill: currentcolor` in CSS
    assert "<path d=" in html
    assert 'viewBox="0 0 24 24"' in html


def test_icon_label_makes_it_a_named_image():
    assert 'role="img" aria-label="关闭"' in icon("close", label="关闭")
    assert 'aria-hidden="true"' in icon("close")


def test_unknown_icon_is_visible_and_logged(caplog):
    with caplog.at_level(logging.WARNING, logger="mkdocs.plugins.homepage"):
        html = icon("definitely-not-an-icon")
    assert "md-home__icon--missing" in html
    assert "undefined" not in html
    assert any("unknown icon" in record.getMessage() for record in caplog.records)


def test_empty_icon_renders_nothing():
    assert icon(None) == ""
    assert icon("") == ""


def test_both_sets_are_exposed_under_the_material_naming_scheme():
    """Names are addressed as Material addresses them: `set/name`, bare = material."""
    names = icon_names()
    assert set(ICON_PATHS) <= set(names)
    assert {f"simple/{name}" for name in BRAND_PATHS} <= set(names)
    assert set(icon_names("material")) == set(ICON_PATHS)
    assert set(icon_names("simple")) == set(BRAND_PATHS)
    assert set(ICON_SETS) == {"material", "simple"}


@pytest.mark.parametrize(
    ("name", "set_name", "key"),
    [
        ("rocket-launch-outline", "material", "rocket-launch-outline"),
        ("material/rocket-launch-outline", "material", "rocket-launch-outline"),
        ("MATERIAL/Rocket-Launch-Outline", "material", "rocket-launch-outline"),
        ("simple/github", "simple", "github"),
        ("simple:github", "simple", "github"),
    ],
)
def test_resolve(name, set_name, key):
    found = resolve(name)
    assert found and found[0] == set_name and found[1] == key


@pytest.mark.parametrize(
    "name",
    ["nope", "simple/nope", "nope/github", "github", "", "  "],
)
def test_resolve_rejects(name):
    # `simple/github` exists but `github` alone does not: MDI has no brand mark.
    assert resolve(name) == ()


def test_a_brand_mark_is_tagged_with_its_set():
    assert "md-home__icon--simple" in icon("simple/github")
    assert "md-home__icon--simple" not in icon("github")


def test_a_missing_set_prefix_is_suggested(caplog):
    """`github` is a brand mark; say so rather than only listing 95 names."""
    with caplog.at_level(logging.WARNING, logger="mkdocs.plugins.homepage"):
        icon("github")
    assert any("simple/github" in record.getMessage() for record in caplog.records)
