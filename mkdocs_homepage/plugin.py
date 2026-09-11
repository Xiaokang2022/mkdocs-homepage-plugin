"""The MkDocs plugin.

It does three things and deliberately nothing else:

* registers the Markdown extension (so an author only ever writes
  ``plugins: [homepage]``, never a ``markdown_extensions`` entry),
* threads the site's own extension list into it, so block bodies render exactly
  like the rest of the page,
* copies the stylesheet and the behaviour script into the site and links them.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Mapping

from mkdocs.config import config_options as c
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import File

from .context import PageContext, clear_page_context, set_page_context
from .converter import extension_name, is_own_extension

log = logging.getLogger("mkdocs.plugins.homepage")

#: The dotted path the extension is registered under in ``markdown_extensions``.
EXTENSION_ENTRY = "mkdocs_homepage.extension:HomepageExtension"

#: Directory inside the package holding the shipped assets.
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

#: Asset file names, in load order.
ASSETS = ("homepage.css", "homepage.js")

#: A CSS custom property name, and a value that cannot escape a declaration.
_CSS_NAME_RE = re.compile(r"^--[A-Za-z0-9_-]+$")
_CSS_VALUE_RE = re.compile(r"^[^;{}<>\\\"']+$")

#: Reveal values accepted by the `reveal` plugin option.
REVEAL_CHOICES = ("auto", "off", "up", "down", "left", "right", "zoom", "fade")


class Number(c.BaseConfigOption):
    """A number.

    ``c.Type(float)`` rejects ``tilt_strength: 6`` -- YAML resolves that to an
    ``int`` -- and asking authors to write ``6.0`` for a tilt angle is the kind of
    papercut that makes a plugin feel fussy.  Booleans are rejected explicitly
    because ``True`` is an ``int`` in Python.
    """

    def __init__(self, default: float = 0.0, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.default = default

    def run_validation(self, value: Any) -> float:
        if isinstance(value, bool):
            raise c.ValidationError("expected a number, got a boolean")
        try:
            return float(value)
        except (TypeError, ValueError):
            raise c.ValidationError(f"expected a number, got {value!r}")


class HomepagePlugin(BasePlugin):
    """Compose a homepage out of Markdown-authored content blocks."""

    config_scheme = (
        ("assets", c.Type(bool, default=True)),
        (
            "assets_dir",
            c.Type(str, default="assets"),
        ),
        ("tilt", c.Type(bool, default=True)),
        ("tilt_strength", Number(default=6.0)),
        ("reveal", c.Choice(REVEAL_CHOICES, default="auto")),
        ("lightbox", c.Type(bool, default=True)),
        ("count", c.Type(bool, default=True)),
        ("markdown_extension", c.Type(bool, default=True)),
        ("strict", c.Type(bool, default=False)),
        ("css_vars", c.Type(dict, default={})),
    )

    def __init__(self) -> None:
        super().__init__()
        self._assets_dir = "assets"
        self._css_vars: dict = {}

    # -- helpers ---------------------------------------------------------
    def _asset_uri(self, name: str) -> str:
        return f"{self._assets_dir}/{name}"

    @staticmethod
    def _sanitise_assets_dir(value: str) -> str:
        cleaned = str(value or "assets").strip().strip("/")
        cleaned = cleaned.replace("\\", "/")
        parts = [part for part in cleaned.split("/") if part and part not in (".", "..")]
        return "/".join(parts) or "assets"

    def _sanitise_css_vars(self, raw: Mapping[str, Any]) -> dict:
        """Keep only declarations that cannot escape the generated ``<style>``."""
        clean: dict = {}
        for name, value in (raw or {}).items():
            key = str(name).strip()
            text = str(value).strip()
            if not _CSS_NAME_RE.match(key):
                log.warning("homepage: ignoring css_vars key %r; expected a --custom-property", name)
                continue
            if not _CSS_VALUE_RE.match(text):
                log.warning("homepage: ignoring css_vars value for %r; unsupported characters", key)
                continue
            clean[key] = text
        return clean

    def _extension_config(self, config: Mapping[str, Any]) -> dict:
        """Build the extension's configuration from the site's own Markdown setup."""
        extensions = list(config["markdown_extensions"] or [])
        configs = dict(config["mdx_configs"] or {})
        # Everything except ourselves: a fragment must never be re-entered.
        extensions = [
            entry
            for entry in extensions
            if not (extension_name(entry) and is_own_extension(extension_name(entry)))
        ]
        configs.pop(EXTENSION_ENTRY, None)
        return {
            "extensions": extensions,
            "extension_configs": configs,
            "options": {
                "tilt": self.config["tilt"],
                "tilt_strength": self.config["tilt_strength"],
                "reveal": self.config["reveal"],
                "lightbox": self.config["lightbox"],
                "count": self.config["count"],
            },
            "strict": self.config["strict"],
        }

    # -- events ----------------------------------------------------------
    def on_config(self, config) -> Any:
        self._assets_dir = self._sanitise_assets_dir(self.config["assets_dir"])
        self._css_vars = self._sanitise_css_vars(self.config["css_vars"])

        self._register_extension(config)

        if self.config["assets"]:
            self._register_assets(config)
        return config

    def _register_extension(self, config) -> None:
        if not self.config["markdown_extension"]:
            return
        extensions = config["markdown_extensions"]
        if extensions is None:
            extensions = config["markdown_extensions"] = []

        already = any(
            extension_name(entry) and is_own_extension(extension_name(entry))
            for entry in extensions
        )
        if not already:
            extensions.append(EXTENSION_ENTRY)

        config["mdx_configs"] = config["mdx_configs"] or {}
        config["mdx_configs"][EXTENSION_ENTRY] = self._extension_config(config)

    def _register_assets(self, config) -> None:
        extra_css = config["extra_css"] or []
        for name in ASSETS:
            if name.endswith(".css"):
                uri = self._asset_uri(name)
                if uri not in extra_css:
                    extra_css.append(uri)
        config["extra_css"] = extra_css

        extra_js = config["extra_javascript"] or []
        for name in ASSETS:
            if name.endswith(".js"):
                uri = self._asset_uri(name)
                if uri not in extra_js:
                    extra_js.append(uri)
        config["extra_javascript"] = extra_js

    def on_files(self, files, config) -> Any:
        if not self.config["assets"]:
            return files
        for name in ASSETS:
            source = os.path.join(ASSETS_DIR, name)
            if not os.path.isfile(source):
                log.warning("homepage: bundled asset %s is missing from the package", source)
                continue
            uri = self._asset_uri(name)
            if files.get_file_from_path(uri) is not None:
                continue
            files.append(File.generated(config, uri, abs_src_path=source))
        return files

    def on_page_markdown(self, markdown: str, **kwargs: Any) -> str:
        page = kwargs.get("page")
        files = kwargs.get("files")
        # The extension cannot see the page, and `on_page_markdown` runs in this
        # thread immediately before `md.convert()`.
        set_page_context(
            PageContext(
                src_uri=getattr(getattr(page, "file", None), "src_uri", "") or "",
                url=getattr(page, "url", "") or "",
                files=files,
            )
        )
        return markdown

    def on_page_content(self, html: str, **kwargs: Any) -> str:
        clear_page_context()
        return html

    def on_post_page(self, output: str, **kwargs: Any) -> str:
        """Append the configured custom properties to the end of ``<head>``.

        Placed after the theme's own stylesheets so that a site-wide override wins
        a specificity tie without ``!important``.
        """
        if not self._css_vars:
            return output
        declarations = "".join(f"{name}:{value};" for name, value in self._css_vars.items())
        tag = f"<style>:root{{{declarations}}}</style>"
        marker = "</head>"
        if marker not in output:
            return output
        return output.replace(marker, tag + marker, 1)
