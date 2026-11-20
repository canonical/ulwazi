"""Smoke checks for the Slopstrap experiment branch.

The regular suites are collect-ignored in ``tests/conftest.py`` on this
branch because they assert Vanilla Framework specifics (pruner behaviour,
``vanilla-main.css`` assets, ``p-*`` markup, feature mappings) that the
Slopstrap experiment intentionally replaces. This module keeps a minimal
signal that the re-skinned theme builds and ships its assets.
"""

from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from conftest import BuiltSite

SLOPSTRAP_CSS = "slopstrap.css"
SLOP_BRIDGE_CSS = "slop-bridge.css"
SLOPSTRAP_JS = "slopstrap.js"


def test_slopstrap_assets_ship(built_site: BuiltSite) -> None:
    """The vendored Slopstrap assets and the bridge stylesheet are copied."""
    static = built_site.output / "_static"
    for name in (SLOPSTRAP_CSS, SLOP_BRIDGE_CSS):
        assert (static / "css" / name).is_file(), f"missing {name}"
    assert (static / "js" / SLOPSTRAP_JS).is_file(), f"missing {SLOPSTRAP_JS}"


def test_no_vanilla_main_reference(built_site: BuiltSite) -> None:
    """No built page links the retired vanilla-main.css stylesheet."""
    for page in built_site.output.rglob("*.html"):
        soup = BeautifulSoup(page.read_text(encoding="utf-8"), "lxml")
        for link in soup.find_all("link", rel="stylesheet"):
            href = link.get("href", "")
            assert "vanilla-main.css" not in href, (
                f"{page} links vanilla-main.css"
            )


def test_slopstrap_shell(built_site: BuiltSite) -> None:
    """The home page carries the Slopstrap shell and asset references."""
    home = built_site.page("")
    html_tag = home.find("html")
    assert html_tag is not None
    assert html_tag.get("data-slop-level") == "3"

    body = home.find("body")
    assert body is not None
    body_classes = " ".join(body.get("class", []))
    assert "slop-body" in body_classes
    assert "slop-grid-bg" in body_classes

    assert home.find("div", class_="slop-orb-layer") is not None

    css_links = {link.get("href", "") for link in home.find_all("link", rel="stylesheet")}
    assert any(SLOPSTRAP_CSS in href for href in css_links)
    assert any(SLOP_BRIDGE_CSS in href for href in css_links)

    scripts = {script.get("src", "") for script in home.find_all("script", src=True)}
    assert any(SLOPSTRAP_JS in src for src in scripts)


def test_slopstrap_transforms(built_site: BuiltSite) -> None:
    """Headings and admonitions carry Slopstrap classes in built pages."""
    config = built_site.page("content/configuration")
    headings = {
        cls
        for tag in config.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        for cls in tag.get("class", [])
    }
    assert any(cls.startswith("slop-h") for cls in headings), (
        "no slop-h* heading class found on content/configuration"
    )

    cheat = built_site.page("content/myst-cheat-sheet")
    alerts = cheat.find_all(class_="slop-alert")
    assert alerts, "no slop-alert admonition found on content/myst-cheat-sheet"
    assert any(
        any(cls.startswith("slop-border-l-") for cls in alert.get("class", []))
        for alert in alerts
    ), "slop-alert without a slop-border-l-* accent"


@pytest.mark.parametrize(
    ("page", "marker"),
    [
        ("", "slop-status"),
        ("content/slop-demo", "slop-card-beam"),
        ("content/slop-demo", "data-slop-marquee"),
        ("content/slop-demo", "data-slop-testimonials"),
    ],
)
def test_demo_fixtures(built_site: BuiltSite, page: str, marker: str) -> None:
    """The demo fixtures render the expected Slopstrap widgets."""
    soup = built_site.page(page)
    assert soup.find(string=lambda text: marker in (text or "")) is not None or (
        soup.find(attrs={"class": lambda value: value and marker in value})
        is not None
        or soup.find(attrs={"data-slop-marquee": True}) is not None
        or marker in str(soup)
    ), f"marker {marker!r} not found in {page or 'home'}"
