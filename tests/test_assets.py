"""The shipped assets: syntax, and the hooks they share with the renderer.

The widget is glued together by ``data-home-*`` attributes: the renderer emits
them, the script queries them, the stylesheet selects them. Nothing in Python
notices when one side is renamed, and the symptom is always the same -- a feature
that simply stops working, silently. Browser behaviour itself can only be checked
by hand, but the *contract* can be checked here.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "mkdocs_homepage"
JS = PACKAGE / "assets" / "homepage.js"
CSS = PACKAGE / "assets" / "homepage.css"
RENDERER = PACKAGE / "render.py"

HOOK_RE = re.compile(r"\bdata-home-[a-z][a-z-]*")

#: Hooks the script owns outright -- it sets them on the document or on an
#: element it bound, so the renderer never emits them.
JS_OWNED = {
    "data-home-ready",
    "data-home-bound",
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def hooks(text: str) -> set:
    return set(HOOK_RE.findall(text))


# -- syntax ----------------------------------------------------------------
@pytest.mark.parametrize("asset", [JS, CSS])
def test_asset_is_not_empty(asset):
    assert read(asset).strip()


def test_the_script_parses():
    """A syntax error in the script ships silently: nothing else would notice."""
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed; the widget does not need it")
    result = subprocess.run(
        [node, "--check", str(JS)], capture_output=True, text=True, timeout=60
    )
    assert result.returncode == 0, result.stderr


def test_the_stylesheet_braces_balance():
    text = read(CSS)
    assert text.count("{") == text.count("}"), "unbalanced braces in homepage.css"


def test_every_custom_property_the_stylesheet_reads_is_defined_somewhere():
    """A `var()` nobody defines is a silent no-op.

    A property is legitimately defined either in the stylesheet or inline by the
    renderer, which is how the per-block values travel (`--md-home-ratio`,
    `--md-home-cols`, ...). Anything else is a typo, or a rename that only landed
    on one side.
    """
    css = read(CSS)
    renderer = read(RENDERER)

    in_css = set(re.findall(r"(--md-home-[a-z0-9-]+)\s*:", css))
    in_renderer = set(re.findall(r"(--md-home-[a-z0-9-]+)", renderer))
    read_back = set(re.findall(r"var\((--md-home-[a-z0-9-]+)", css))

    undefined = {
        name
        for name in read_back
        if name not in in_css
        and name not in in_renderer
        and not re.search(rf"var\({name},", css)
    }
    assert not undefined, f"custom properties read but never set: {sorted(undefined)}"


#: Classes the renderer always wraps in another element, so a child combinator on
#: them can never match.  `_header()` puts every title inside a `<header>`; a
#: `> .md-home__title` rule therefore silently matches nothing, and the hero fell
#: back to the ordinary section-title size exactly that way.
ALWAYS_WRAPPED = ("md-home__title", "md-home__subtitle", "md-home__eyebrow")


def test_no_child_combinator_targets_an_always_wrapped_class():
    # Comments stripped first: the file *explains* this trap, and a naive scan
    # would flag its own documentation.
    css = re.sub(r"/\*.*?\*/", "", read(CSS), flags=re.S)
    offending = [
        line.strip()
        for line in css.splitlines()
        for name in ALWAYS_WRAPPED
        if f"> .{name}" in line
    ]
    assert not offending, (
        "these selectors can never match, because the renderer wraps the element "
        f"in a <header>: {offending}"
    )


def test_the_wrapping_contract_holds_in_the_markup():
    """The complement of the check above: the wrapper really is there."""
    from tests.conftest import render

    html = render("```homepage-hero\ntitle: T\nsubtitle: S\n```")
    header = re.search(r'<header class="md-home__header[^"]*">(?P<body>.*?)</header>', html, re.S)
    assert header, "the hero title is no longer wrapped in a header"
    assert "md-home__title" in header.group("body")
    assert "md-home__subtitle" in header.group("body")


def test_prose_list_markers_are_stated_not_reverted():
    """`revert` inside a `<ul>`-based block silently yields the wrong marker.

    `revert` rolls back to the *user agent* stylesheet, whose list markers are
    chosen by nesting depth.  A testimonial grid is a `<ul>` of `<li>`, so a
    list in the quote body is at depth 2 to the UA and gets the hollow `circle`
    -- while the same Markdown on the page gets a solid `disc`.  Declaring the
    marker is the only way to make the two agree, because the depth the widget
    adds is not knowable from inside the stylesheet.
    """
    css = re.sub(r"/\*.*?\*/", "", read(CSS), flags=re.S)
    prose = [
        rule
        for rule in re.findall(r"([^{}]+)\{([^{}]*)\}", css)
        if "__prose" in rule[0] and "list-style" in rule[1]
    ]
    assert prose, "no prose list rule found -- did the selector get renamed?"
    for selector, body in prose:
        assert "list-style: revert" not in body, f"a depth-dependent marker is back in {selector.strip()!r}"


# -- the shared hook contract ---------------------------------------------
def test_every_hook_the_script_queries_is_emitted_by_the_renderer():
    renderer = read(RENDERER)
    missing = {
        hook
        for hook in hooks(read(JS))
        if hook not in JS_OWNED and hook not in renderer
    }
    assert not missing, (
        "the script queries hooks the renderer never emits: "
        f"{sorted(missing)}. Either the renderer was renamed or the script has a typo — "
        "either way the feature is silently dead."
    )


def test_every_attribute_selector_the_stylesheet_uses_is_emitted():
    renderer = read(RENDERER)
    used = {
        hook
        for hook in hooks(read(CSS))
        if hook not in JS_OWNED
    }
    missing = {hook for hook in used if hook not in renderer}
    assert not missing, f"homepage.css selects attributes the renderer never emits: {sorted(missing)}"


def test_the_hook_scan_is_not_vacuous():
    """Positive control: a renamed hook must actually be detected."""
    assert hooks('card.getAttribute("data-home-tilt")') == {"data-home-tilt"}
    assert "data-home-cols" in hooks(read(CSS))
    assert "data-home-cols" in hooks(read(RENDERER))
    assert len(hooks(read(JS))) >= 6


# -- reading the stylesheet as rules, not as text --------------------------
def css_rules(text: str | None = None):
    """Flatten the stylesheet into ``(at_rule_context, selector, body)`` triples.

    Several contracts are about *where* a rule lives -- a press effect written
    inside `@media (hover: hover)` is a press effect a phone never sees -- and a
    regex over the whole file cannot tell the difference.  Comments are stripped
    first, so the file's own explanations can never be mistaken for code (which is
    how a scan for `> .foo__title` once flagged the comment describing that trap).
    """
    css = re.sub(r"/\*.*?\*/", "", text if text is not None else read(CSS), flags=re.S)
    stack: list[str] = []
    rules = []
    buffer = ""
    index = 0
    while index < len(css):
        char = css[index]
        if char == "{":
            prelude = buffer.strip()
            buffer = ""
            if prelude.startswith("@"):
                stack.append(prelude)
            else:
                depth = 1
                end = index + 1
                while end < len(css) and depth:
                    if css[end] == "{":
                        depth += 1
                    elif css[end] == "}":
                        depth -= 1
                    end += 1
                rules.append((" ".join(stack), prelude, css[index + 1 : end - 1]))
                index = end
                continue
        elif char == "}":
            buffer = ""
            if stack:
                stack.pop()
        else:
            buffer += char
        index += 1
    return rules


def test_the_rule_reader_is_not_vacuous():
    """Positive control for the parser the contracts below depend on."""
    rules = css_rules(".a { color: red; }\n@media (hover: hover) { .b { top: 0; } }")
    assert rules == [("", ".a", " color: red; "), ("@media (hover: hover)", ".b", " top: 0; ")]
    assert css_rules("/* .a { color: red } */") == []
    assert len(css_rules()) > 200


def selectors_and_bodies(*needles: str):
    """Rules whose selector mentions every needle, with their media context."""
    return [
        (context, selector, body)
        for context, selector, body in css_rules()
        if all(needle in selector for needle in needles)
    ]


def declared(body: str, name: str) -> str:
    """The value of one declaration, or `""` when it is not declared there."""
    match = re.search(rf"(?:^|;)\s*{re.escape(name)}:\s*(?P<value>[^;]+)", body)
    return match.group("value").strip() if match else ""


def split_selector_list(selector: str) -> list[str]:
    """Split on commas that are not inside a functional pseudo-class."""
    parts, depth, current = [], 0, ""
    for char in selector:
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        if char == "," and depth == 0:
            parts.append(current.strip())
            current = ""
        else:
            current += char
    if current.strip():
        parts.append(current.strip())
    return parts


def last_compound(part: str) -> str:
    """The final compound selector, ignoring whitespace inside `()`.

    A naive `split()` tears `:is(:hover, :focus-visible)` apart at its own space,
    which silently reported the hover rule as having no subject at all.
    """
    depth = 0
    start = 0
    for index, char in enumerate(part):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif depth == 0 and (char.isspace() or char in ">+~"):
            start = index + 1
    return part[start:].strip()


def subject_classes(part: str) -> set[str]:
    """The classes of the element a selector *matches*, if it is a plain one.

    What decides whether an `opacity` reaches an image is whether the rule's
    subject is one of the image's ancestors -- not whether the class happens to be
    mentioned somewhere in the selector.  `.md-home__logo .md-icon` mentions
    `.md-home__logo` but matches the mark, and dimming the mark does not dim the
    picture next to it.
    """
    tail = re.sub(r"::?[a-z-]+(\([^()]*\))?", "", last_compound(part))
    return set(re.findall(r"\.[\w-]+", tail))


def test_the_subject_reader_is_not_vacuous():
    assert subject_classes(".md-home__logo") == {".md-home__logo"}
    assert subject_classes(".md-home__logs .md-home__logo:hover") == {".md-home__logo"}
    assert subject_classes(".md-home__logo .md-icon") == {".md-icon"}
    assert subject_classes("li.md-home__logo-item") == {".md-home__logo-item"}
    assert subject_classes(".a::after") == {".a"}
    assert subject_classes("img") == set()
    # A space inside `:is()` is not a descendant combinator.
    assert subject_classes(".md-typeset .md-home .md-home__logo:is(:hover, :focus-visible)") == {
        ".md-home__logo"
    }
    assert subject_classes(".a > .b") == {".b"}


def requires(selector: str, state: str) -> bool:
    """Whether the selector *needs* `state`, as opposed to ruling it out.

    The difference decides whether two states can be true at once.  A hover rule
    carrying `:not(:active)` never applies while the card is being pressed, which
    is exactly what lets it score higher than the press rule without winning.
    """
    return state in re.sub(r":not\([^()]*\)", "", selector)


def excludes(selector: str, state: str) -> bool:
    """Whether the selector rules `state` out inside a `:not()`."""
    return re.search(rf":not\([^()]*{re.escape(state)}[^()]*\)", selector) is not None


def specificity(selector: str) -> tuple[int, int, int]:
    """A small CSS specificity calculator, good enough for the selectors here.

    Written because a rule that *looks* right can lose silently: a (0,5,0) hover
    exception outranked the (0,4,0) press rule, so a card that was being pressed
    kept exactly the transparent border the press existed to replace.  Reading
    the two rules side by side shows nothing wrong, and there is no browser in
    this test suite to catch it -- so the arithmetic is checked instead.
    """
    best = (0, 0, 0)
    for part in split_selector_list(selector):
        # `:where()` is zero-specificity; `:is()`/`:not()`/`:has()` contribute the
        # specificity of their most specific argument.
        inner = (0, 0, 0)
        for match in re.finditer(r":(?:is|not|has)\(([^()]*)\)", part):
            argument = max(
                (specificity(item) for item in split_selector_list(match.group(1))),
                default=(0, 0, 0),
            )
            inner = tuple(a + b for a, b in zip(inner, argument))
        part = re.sub(r":where\([^()]*\)", "", part)
        part = re.sub(r":(?:is|not|has)\([^()]*\)", "", part)

        counts = (
            len(re.findall(r"#[\w-]+", part)),
            len(re.findall(r"\.[\w-]+", part))
            + len(re.findall(r"\[", part))
            + len(re.findall(r"(?<!:)::?[\w-]+", part)),
            len(re.findall(r"(?:^|[\s>+~])([a-z][\w-]*)", part)),
        )
        candidate = tuple(a + b for a, b in zip(inner, counts))
        best = max(best, candidate)
    return best


def test_the_specificity_calculator_agrees_with_the_computed_values_it_checks():
    """`getComputedStyle` cannot tell us which rule won, so this file counts.

    Every expectation here was read off the real cascade in a browser during the
    change that introduced the press state.
    """
    cases = {
        ".a": (0, 1, 0),
        ".a .b": (0, 2, 0),
        "#a": (1, 0, 0),
        ".md-home *": (0, 1, 0),
        "[data-home-cols]": (0, 1, 0),
        ":where(.a)": (0, 0, 0),
        ".md-typeset .md-home .md-home__card:is(:active, :focus-visible)": (0, 4, 0),
        ".md-home__card.md-home--theme-cyan": (0, 2, 0),
        ".md-typeset .md-home .md-home__cards--plain .md-home__card:hover:not(:active):not(:focus-visible)": (
            0,
            7,
            0,
        ),
    }
    for selector, expected in cases.items():
        assert specificity(selector) == expected, f"{selector}: {specificity(selector)} != {expected}"


def test_no_hover_only_rule_outranks_the_press_state():
    """The press has to win the cascade, not just be written down.

    This is the bug the calculator above was written for: adding a hover
    exception for the `plain` and `filled` card styles scored (0,5,0) and beat
    the (0,4,0) press rule, so a pressed plain card kept its transparent border.
    A hover rule may outrank the press as long as it *cannot be true at the same
    time* -- which is what `:not(:active):not(:focus-visible)` buys.
    """
    rules = list(css_rules())
    pressed = [
        (index, selector)
        for index, (_, selector, body) in enumerate(rules)
        if "md-home__card" in selector
        and requires(selector, ":active")
        and ("border-color" in body or "box-shadow" in body)
    ]
    assert pressed, "no rule lights up the card when it is pressed"
    press_index = max(index for index, _ in pressed)
    press_score = max(specificity(selector) for _, selector in pressed)

    for index, (_, selector, body) in enumerate(rules):
        if (
            "md-home__card" not in selector
            or not requires(selector, ":hover")
            or not ("border-color" in body or "box-shadow" in body)
        ):
            continue
        # Harmless: it stands down for both ways of being pressed.
        if excludes(selector, ":active") and excludes(selector, ":focus-visible"):
            continue
        score = specificity(selector)
        assert score <= press_score, (
            f"{selector!r} scores {score} against the press rule's {press_score}, so its "
            "declarations win while the card is being pressed"
        )
        if score == press_score:
            assert index < press_index, (
                f"{selector!r} ties with the press rule and comes after it in the file, "
                "so the press loses the tie"
            )


# -- press feedback ---------------------------------------------------------
def test_the_press_state_exists_and_is_not_hidden_behind_a_hover_query():
    """`@media (hover: hover)` is a query about the *capability*, not the device.

    A press effect written inside it is a press effect a touch screen never sees,
    and a finger has no hover -- so the press is the only feedback there is.  This
    is the one rule of the press that cannot be checked by looking at a desktop.
    """
    pressed = [rule for rule in css_rules() if requires(rule[1], ":active")]
    assert pressed, "no `:active` rule left in the stylesheet — did the press state go?"
    hidden = [rule for rule in pressed if "hover" in rule[0]]
    assert not hidden, (
        "these press states can never fire on a touch screen: "
        f"{[(context, selector) for context, selector, _ in hidden]}"
    )


def test_the_card_press_glow_is_drawn_from_the_block_accent():
    """A hard-coded glow would not move with `theme:`, and would not survive a
    scheme change -- which is the whole promise of the colour system."""
    pressed = [
        rule
        for rule in css_rules()
        if requires(rule[1], ":active") and "md-home__card" in rule[1] and "box-shadow" in rule[2]
    ]
    assert pressed, "the card no longer changes its shadow when pressed"
    for _, selector, body in pressed:
        assert declared(body, "box-shadow") == "var(--md-home-shadow-press)", selector

    definitions = [
        (selector, declared(body, "--md-home-shadow-press"))
        for _, selector, body in css_rules()
        if re.search(r"(?:^|;)\s*--md-home-shadow-press:", body)
    ]
    assert len(definitions) >= 2, (
        "the press glow is declared once, so one colour scheme is stuck with the "
        "other's alphas: " + repr(definitions)
    )
    assert any("slate" in selector for selector, _ in definitions), definitions
    for selector, value in definitions:
        assert "var(--md-home-accent)" in value, f"{selector} uses a literal colour"
        assert "inset" in value, f"{selector} has no inner wash — it reads as a halo behind the card"


def test_the_crisp_edge_is_revealed_by_the_same_states_as_the_glow():
    """The ring is the edge the glow spills from; revealing it on hover only would
    put the two on different triggers, leaving a press on a touch screen with a
    shadow but no edge to cast it from."""
    ring = [
        rule
        for rule in selectors_and_bodies("md-home__card--ring", "::after")
        if "opacity" in rule[2]
    ]
    assert ring
    lit = [rule for rule in ring if declared(rule[2], "opacity") == "1"]
    assert lit, "the gradient ring is never revealed"
    assert [rule for rule in lit if "hover" not in rule[0]], (
        "every rule that reveals the ring sits inside a hover query, so a press on "
        "a touch screen has an edge that never lights up"
    )


def test_the_keyboard_and_the_pointer_share_one_press_rule():
    """Two rules would drift; the `:is()` list is what keeps them equal."""
    pressed = [
        selector
        for _, selector, body in css_rules()
        if "md-home__card" in selector
        and requires(selector, ":active")
        and "box-shadow" in body
    ]
    assert pressed
    for selector in pressed:
        assert requires(selector, ":focus-visible"), (
            f"{selector!r} lights up for the mouse but not for the keyboard"
        )


# -- elevation -------------------------------------------------------------
def test_every_shape_that_reads_as_a_card_shares_the_elevation_token():
    """A quote, a logo tile and a link card are the same shape as a card.

    They were built as tinted panels with a hairline and no shadow, so a
    testimonial block sat visibly flatter than a card block next to it.
    """
    elevated = {
        part.strip()
        for _, selector, body in css_rules()
        if declared(body, "box-shadow") == "var(--md-home-shadow)"
        for part in selector.split(",")
    }
    for surface in (
        ".md-home__quote",
        ".md-home__logos--grid .md-home__logo",
        ".md-home__links--cards .md-home__link",
        ".md-home__links--buttons .md-home__link",
    ):
        assert surface in elevated, f"{surface} lost its elevation"


def test_the_interactive_surfaces_lift_further_on_hover():
    hover = [
        (selector, declared(body, "box-shadow"))
        for _, selector, body in css_rules()
        if "md-home__link" in selector and ":hover" in selector
    ]
    lifted = [selector for selector, value in hover if value == "var(--md-home-shadow-hover)"]
    assert lifted, "a link card no longer lifts when hovered"
    assert any("--cards" in selector for selector in lifted), lifted
    assert any("--buttons" in selector for selector in lifted), lifted


def test_every_filled_icon_bubble_shares_one_hairline():
    """Three bubbles drawn three ways is what made the blocks look unrelated."""
    ringed = {
        part.strip()
        for _, selector, body in css_rules()
        if declared(body, "box-shadow") == "var(--md-home-bubble-ring)"
        for part in selector.split(",")
    }
    assert ".md-home__card-icon" in ringed, ringed
    assert any("md-home__feature-icon" in part for part in ringed), ringed
    assert ".md-home__step-marker" in ringed, ringed


def test_the_bubble_hairline_is_not_declared_alongside_a_literal_inset_ring():
    """The card icon used to carry its own (0,1,0) `inset` rule, which is exactly
    how the three bubbles drifted apart in the first place."""
    strays = [
        selector
        for _, selector, body in css_rules()
        if "md-home__card-icon" in selector and "inset 0 0 0" in body
    ]
    assert not strays, f"a one-off inner ring is back in {strays}; use --md-home-bubble-ring"


# -- spacing ----------------------------------------------------------------
def test_the_spacing_scale_is_a_ladder():
    """Each step roughly twice the last, or the tiers stop being distinguishable."""
    steps = [
        (int(number), float(value))
        for number, value in re.findall(r"--md-home-space-(\d):\s*([\d.]+)em", read(CSS))
    ]
    assert steps, "the spacing scale is gone"
    numbers = [number for number, _ in sorted(steps)]
    values = [value for _, value in sorted(steps)]
    assert numbers == list(range(1, len(numbers) + 1)), numbers
    assert values == sorted(values) and len(set(values)) == len(values), values
    assert values[0] >= 0.3 and values[-1] <= 3.0, values


def test_no_spacing_step_is_defined_but_unused():
    """A scale nobody references is a scale that has already rotted."""
    css = re.sub(r"/\*.*?\*/", "", read(CSS), flags=re.S)
    unused = [
        number
        for number in re.findall(r"--md-home-space-(\d):", css)
        if not re.search(rf"var\(--md-home-space-{number}\)", css)
    ]
    assert not unused, f"defined but never used: {unused}"


def test_the_shared_gutter_is_the_scale_not_a_one_off():
    for token, step in (("--md-home-gap", 3), ("--md-home-pad", 4), ("--md-home-section-gap", 6)):
        declaration = re.search(rf"{token}:\s*(?P<value>[^;]+);", read(CSS))
        assert declaration, f"{token} is gone"
        assert declaration.group("value").strip() == f"var(--md-home-space-{step})", (
            f"{token} escaped the scale"
        )


def test_a_panel_is_padded_more_than_the_gutter_between_two_of_them():
    """Otherwise a grid reads as cramped however wide the cards are."""
    tokens = dict(re.findall(r"(--md-home-space-\d):\s*([\d.]+)em", read(CSS)))
    declaration = re.search(r"--md-home-pad:\s*var\((?P<token>--md-home-space-\d)\)", read(CSS))
    assert declaration, "the panel padding left the scale"
    pad = float(tokens[declaration.group("token")])
    gap = float(tokens["--md-home-space-3"])
    assert pad > gap, f"padding {pad}em <= gutter {gap}em"


def test_everything_the_script_appends_outside_the_widget_can_see_its_tokens():
    """The lightbox is a child of `<body>`, so `.md-home`'s tokens never reach it.

    That is not theoretical: every default was declared on `.md-home`, so
    `var(--md-home-radius-sm)` was invalid inside the lightbox and `box-shadow`
    fell back to `none` -- the zoomed image rendered square and flat, with no
    console error and nothing to fail.  Anything such a component reads has to be
    on `:root`, or declared in a rule that matches the component itself.
    """
    on_root: set[str] = set()
    for _, selector, body in css_rules():
        if selector.strip() == ":root":
            on_root |= set(re.findall(r"(--md-home-[a-z0-9-]+)\s*:", body))
    assert on_root, "the scheme-independent tokens have moved off :root again"

    # The class names the script creates, per `buildLightbox()`.
    components = ["md-home-lightbox"]
    for name in components:
        declared_here: set[str] = set()
        borrowed: set[str] = set()
        found = False
        for _, selector, body in css_rules():
            if name not in selector:
                continue
            found = True
            declared_here |= set(re.findall(r"(--md-home-[a-z0-9-]+)\s*:", body))
            borrowed |= set(re.findall(r"var\((--md-home-[a-z0-9-]+)", body))
        assert found, f".{name} has no styles at all"
        missing = borrowed - on_root - declared_here
        assert not missing, (
            f".{name} sits outside .md-home, so these are silently empty there: "
            f"{sorted(missing)}"
        )


def test_only_the_first_block_loses_its_lead_in():
    """Every pair of blocks must sit the same distance apart.

    `.md-home:first-child + .md-home { margin-block-start: 0 }` exempted the
    *second* block too, and the demo measured 26px between the hero and the logos
    row against a uniform 40px everywhere else.  Margins collapse, so an exempt
    block needs no help from its successor's rule.
    """
    offenders = [
        selector
        for _, selector, body in css_rules()
        if declared(body, "margin-block-start") == "0"
        and "+" in selector
        and "md-home" in selector
    ]
    assert not offenders, (
        "these rules zero a block's lead-in whenever it follows another block, so the "
        f"gap after the exempt one collapses to the previous block's own margin: {offenders}"
    )


def test_a_band_and_a_pattern_pad_identically():
    """`background:` and `pattern:` are two spellings of "this block is a band".

    Only the rules that actually declare a padding are considered -- the same
    selector also carries the *tint*, in a rule of its own.
    """
    padding_rules = [
        (selector, declared(body, "padding"))
        for _, selector, body in css_rules()
        if re.search(r"(?:^|;)\s*padding:", body)
        and (
            "md-home--bg-tint" in selector
            or "md-home--bg-surface" in selector
            or "md-home--bg-accent" in selector
            or "md-home--pattern-aurora" in selector
        )
    ]
    assert padding_rules, "the bands lost their padding"
    for selector, value in padding_rules:
        assert value == "var(--md-home-band-pad)", f"{selector} pads off the token: {value!r}"


def test_a_transition_is_declared_on_the_resting_rule_not_on_hover():
    """Declared on `:hover` it only runs on the way in, so the element snaps back
    the moment the pointer leaves.  The feature icon shipped exactly that bug."""
    hovered = [
        (selector, body)
        for _, selector, body in css_rules()
        if "md-home__feature-icon" in selector and ":hover" in selector
    ]
    assert hovered, "the feature icon no longer responds to hover"
    for selector, body in hovered:
        assert "transition" not in body, f"the transition is back on {selector!r}"

    resting = [
        body
        for _, selector, body in css_rules()
        if selector.strip() == ".md-home__feature-icon"
    ]
    assert resting and any("transition" in body for body in resting), (
        "the feature icon's transition is not on its resting rule"
    )


# -- the marquee loop -------------------------------------------------------
def test_the_marquee_shift_is_exactly_one_period():
    """`translateX(-50%)` is only seamless if half the track *is* one period.

    Which needs the track to be symmetric: any spacing that sits between the two
    periods rather than inside them makes `-50%` land short.  The demo measured
    1454px needed against 1438px delivered -- a 16px jump every cycle, i.e. half
    of the 32px `gap` that used to sit on the track.
    """
    tracks = [
        rule
        for rule in css_rules()
        if subject_classes(rule[1]) == {".md-home__marquee-track"}
    ]
    assert tracks, "the marquee track is gone"
    # No rule may put a gap on the track -- not the base one, not a hover one.
    for _, selector, body in tracks:
        assert declared(body, "gap") == "", (
            f"{selector!r} has a gap on the track: it belongs to one period, not between two"
        )

    geometry = [rule for rule in tracks if declared(rule[2], "animation")]
    assert geometry, "the track is no longer animated"
    for _, selector, body in geometry:
        assert declared(body, "min-width") == "200%", (
            f"{selector!r} must be at least two viewports wide, or the right-hand side runs "
            "out of content before the loop ends"
        )
        assert declared(body, "justify-content") == "space-around", (
            f"{selector!r} must use `space-around`: it is the only distribution whose "
            "end spaces add up to exactly one junction, which is what the wrap needs"
        )

    keyframe = [
        rule for rule in css_rules() if rule[0].endswith("md-home-marquee") and rule[1] == "to"
    ]
    assert keyframe, "the marquee keyframe is gone"
    assert declared(keyframe[0][2], "transform") == "translateX(-50%)", keyframe[0][2]


def test_every_marquee_period_carries_its_own_half_gap():
    """Both periods have to be padded identically, on both sides."""
    half = "calc(var(--md-home-marquee-gap) / 2)"
    periods = [
        rule
        for rule in css_rules()
        if subject_classes(rule[1]) & {".md-home__marquee-item", ".md-home__logo-item"}
        and declared(rule[2], "padding-inline")
    ]
    assert periods, "no marquee period declares a padding"
    for _, selector, body in periods:
        assert declared(body, "padding-inline") == half, f"{selector}: {body}"
        assert declared(body, "margin-inline") == "", (
            f"{selector!r} spaces a period with a margin, which collapses and breaks the loop"
        )
        assert declared(body, "flex") == "0 0 auto", (
            f"{selector!r} must not grow: a grown period puts its free space at its own edge, "
            "so the seam stops matching the logos inside"
        )


def test_the_gap_token_the_periods_read_is_declared_where_they_can_see_it():
    declared_tokens = {
        name
        for _, selector, body in css_rules()
        if subject_classes(selector) <= {".md-home__marquee", ".md-home"}
        for name in re.findall(r"(--md-home-marquee-gap)\s*:", body)
    }
    assert declared_tokens, "the marquee gap token is not declared on the marquee or its root"


def test_the_logos_list_is_the_one_flex_line():
    """A wrapper per period is what makes the seam and the logos disagree.

    The row is a single flex line holding both periods, so one `space-around`
    governs every junction at once -- the seam included.
    """
    rows = [
        (selector, body)
        for _, selector, body in css_rules()
        if "md-home__logos--marquee" in selector and "md-home__logos-list" in selector
    ]
    assert rows, "the marquee row lost its rule"
    for selector, body in rows:
        assert declared(body, "flex-wrap") == "nowrap", selector
        assert declared(body, "gap") == "0", (
            f"{selector!r} keeps a gap on the line: the spacing has to come from the periods' "
            "own half-paddings, or the seam gets a second, different gap"
        )


def test_the_marquee_row_beats_the_base_list_rule():
    """`flex-wrap: nowrap` used to lose 0,2,0 against 0,3,0 and nothing said so.

    The "marquee" was quietly a wrapping row, and its measured width was inflated
    by 200px.  A rule that overrides a property has to out-score the rule it
    overrides, or the override is dead code.
    """
    base = [
        (selector, body)
        for _, selector, body in css_rules()
        if "md-home__logos-list" in selector and declared(body, "flex-wrap") == "wrap"
    ]
    assert base, "the base list rule no longer sets flex-wrap"
    base_score = max(specificity(selector) for selector, _ in base)
    for _, selector, body in css_rules():
        if "md-home__logos--marquee" not in selector or "md-home__logos-list" not in selector:
            continue
        for prop in ("flex-wrap", "gap"):
            if declared(body, prop):
                assert specificity(selector) >= base_score, (
                    f"{selector!r} sets `{prop}` at {specificity(selector)} against the base "
                    f"rule's {base_score}, so the base wins and the marquee silently wraps"
                )


# -- logo images ------------------------------------------------------------
def test_an_image_logo_is_a_circle():
    rules = [rule for rule in css_rules() if "md-home__logo img" in rule[1]]
    assert rules, "the image logo lost its rule"
    for _, selector, body in rules:
        assert declared(body, "border-radius") == "50%", f"{selector}: {body}"
        assert declared(body, "object-fit") == "cover", selector
        assert declared(body, "aspect-ratio") in ("1", "1 / 1"), (
            f"{selector!r} must square the box, or a wide image becomes an ellipse "
            "instead of a circle"
        )
        assert declared(body, "width") == "var(--md-home-logo-size, 1.9em)", selector


def test_an_image_logo_keeps_its_own_colours():
    """Greyscale is gone, and no `colored` rule may reach an image."""
    css = re.sub(r"/\*.*?\*/", "", read(CSS), flags=re.S)
    assert "grayscale" not in css, "an image logo is being greyed out again"
    touched = [
        selector
        for _, selector, _ in css_rules()
        if "colored" in selector and re.search(r"\bimg\b", selector)
    ]
    assert not touched, f"`colored` must not touch an image logo: {touched}"


def test_nothing_dims_an_image_through_an_ancestor():
    """`opacity` and `filter` multiply down onto descendants.

    A wrapper `opacity` on `.md-home__logo` therefore reached the picture, which
    is how `colored` used to change an image's appearance no matter what the
    option said.  Dimming the parts (`.md-icon`, `.md-home__logo-name`) is
    deliberate; dimming a container of the image is not.
    """
    ancestors = {
        ".md-home__logo",
        ".md-home__logo-item",
        ".md-home__logo-mark",
        ".md-home__logos",
    }
    offenders = []
    for _, selector, body in css_rules():
        if ".md-home__logo img" in selector:
            continue
        for part in split_selector_list(selector):
            if not subject_classes(part) & ancestors:
                continue
            for prop in ("opacity", "filter"):
                if declared(body, prop):
                    offenders.append((part.strip(), prop, declared(body, prop)))
    assert not offenders, (
        "these rules dim an ancestor of the picture, so a brand file is rendered faded "
        f"however `colored` is set: {offenders}"
    )


def test_the_dimming_lands_on_the_parts_instead():
    for cls in (".md-home__logo .md-icon", ".md-home__logo-name"):
        assert any(
            subject_classes(part) and declared(body, "opacity")
            for _, selector, body in css_rules()
            for part in split_selector_list(selector)
            if cls in part
        ), f"{cls} is no longer dimmed, so the strip reads at full strength by default"


def test_colored_recolours_the_marks_and_leaves_the_images_alone():
    """`colored` has to mean something, and what it means has to stop at the file.

    The icon marks are `currentColor`, so the option can colour them; an image
    carries its own palette and the option may not touch it.  Both halves are
    asserted, because "does nothing to images" is only half the contract -- it
    used to do nothing to the marks either, which made the option dead code.
    """
    marks = [
        (selector, body)
        for _, selector, body in css_rules()
        if "colored" in selector and "md-icon" in selector
    ]
    assert marks, "`colored` no longer reaches the icon marks"
    assert any(declared(body, "color") == "var(--md-home-accent)" for _, body in marks), marks

    for _, selector, body in css_rules():
        if "colored" not in selector:
            continue
        assert not re.search(r"\bimg\b", selector), (
            f"`colored` must not reach an image logo, but {selector!r} does"
        )
        assert not declared(body, "filter"), f"{selector!r} filters something"


def test_the_strip_does_not_inherit_the_sites_link_colour():
    """A linked logo is an `<a>`, and Material sizes its own link rule to win.

    `.md-typeset a` is (0,1,1); a bare `.md-home__logo` (0,1,0) loses to it, so
    every linked logo rendered in `--md-typeset-a-color` and the "muted, then
    accent on hover" design silently never applied to the common case.  Both the
    resting colour and the hover accent therefore have to be re-stated on a prefix
    that beats the theme's link rule.
    """
    link_colour = specificity(".md-typeset a")
    logo_rules = [
        (selector, body)
        for _, selector, body in css_rules()
        for part in split_selector_list(selector)
        if subject_classes(part) == {".md-home__logo"} and declared(body, "color")
    ]
    assert len(logo_rules) >= 2, (
        "the strip no longer states both its resting colour and its hover accent: "
        f"{logo_rules}"
    )
    for selector, body in logo_rules:
        score = max(
            specificity(part)
            for part in split_selector_list(selector)
            if subject_classes(part) == {".md-home__logo"}
        )
        assert score >= link_colour, (
            f"{selector!r} scores {score} against the theme's link rule {link_colour}, so "
            "Material's link colour wins and this declaration is dead"
        )


# -- behaviours a future edit could quietly drop ---------------------------
def test_the_tilt_cancels_its_pending_frame_on_leave():
    """The reported bug: a queued frame overwriting the reset with a stale move.

    Checked structurally because there is no browser here; the comment in the
    script explains the failure in full, and a manual browser pass covers it.
    """
    script = read(JS)
    assert "cancelAnimationFrame" in script
    # The leave path must both clear the stored point and drop the frame.
    leave = re.search(r"var reset = function \(\) \{(?P<body>.*?)\n      \};", script, re.S)
    assert leave, "the tilt `reset` closure is gone; update this test"
    body = leave.group("body")
    assert "cancelAnimationFrame" in body
    assert "point = null" in body


def test_the_script_resets_state_between_passes():
    """`init()` promises to be re-runnable, and instant navigation relies on it."""
    script = read(JS)
    teardown = re.search(r"function teardown\(\) \{(?P<body>.*?)\n  \}", script, re.S)
    assert teardown, "teardown() is gone; update this test"
    body = teardown.group("body")
    assert "removeEventListener" in body
    # A binding marker left behind makes the next pass skip an element it just
    # unbound, so tilt, typewriter and lightbox all go dead.
    assert "data-home-bound" in body
    assert "tilters = []" in body
