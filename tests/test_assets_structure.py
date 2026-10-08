"""Representative asset and Ulwazi-generated structure checks.

Sphinx already warns about unresolved source references. These checks instead
follow URLs and controls after rendering, including on nested dirhtml pages.
"""

import ipaddress
import socket
import warnings
from collections import Counter, defaultdict
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.parse import unquote, urljoin, urlsplit

import pytest
import requests
import tinycss2
from bs4 import BeautifulSoup
from bs4.element import AttributeValueList

REPO = Path(__file__).resolve().parents[1]
PAGES = (
    "",
    "content/myst-cheat-sheet",
    "content/rst-cheat-sheet",
    "content/test-code-headings",
    "search",
)
REQUIRED_CSS = {"vanilla-main.css", "sidenav.css", "local-toc.css"}
REQUIRED_JS = {"nav-toggle.js", "vanilla-tabs.js", "theme-toggle.js"}
RESOURCE_LINK_RELS = {"stylesheet", "icon", "shortcut", "apple-touch-icon", "preload"}
RESOURCE_META = {"og:image", "twitter:image"}
# Do not send requests from CI to arbitrary URLs introduced by documentation edits.
# New public asset hosts must be reviewed and added here deliberately.
REMOTE_ASSET_HOSTS = {"assets.ubuntu.com"}


class RemoteAssetWarning(UserWarning):
    """An advisory: a remote asset was not confirmed available at check time."""


def _local_target(output: Path, page: Path, url: str):
    """Return a local built file or None for external/non-file URLs."""
    parsed = urlsplit(url)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None
    path = unquote(parsed.path)
    target = output / path.lstrip("/") if path.startswith("/") else page.parent / path
    if path.endswith("/"):
        target /= "index.html"
    target = target.resolve()
    if not target.is_relative_to(output.resolve()):
        raise ValueError(f"path escapes built site: {url}")
    return target


def _assets(name, soup, output):
    """Find missing targets and duplicate CSS/JS loads for a page."""
    errors = []
    page = output / name / "index.html" if name else output / "index.html"
    stylesheet_targets, script_targets = [], []
    styles, scripts = set(), set()
    for tag in soup.select("link[href], script[src], img[src]"):
        attr = "href" if tag.name == "link" else "src"
        url = tag.get(attr, "")
        try:
            target = _local_target(output, page, url)
        except ValueError as exc:
            errors.append(f"[{name or 'home'}] {tag.name}[{attr}] {url!r}: {exc}")
            continue
        if target is None:
            continue
        if not target.is_file():
            errors.append(
                f"[{name or 'home'}] {tag.name}[{attr}] {url!r}: missing {target}"
            )
        if tag.name == "script":
            script_targets.append(target)
            scripts.add(target.name)
        elif tag.name == "link" and "stylesheet" in tag.get("rel", []):
            stylesheet_targets.append(target)
            styles.add(target.name)

    for required, actual, kind in (
        (REQUIRED_CSS, styles, "CSS"),
        (REQUIRED_JS, scripts, "JS"),
    ):
        if missing := required - actual:
            errors.append(
                f"[{name or 'home'}] {kind}: missing theme links {sorted(missing)}"
            )
    for targets, kind in (
        (stylesheet_targets, "stylesheet"),
        (script_targets, "script"),
    ):
        for target, count in Counter(targets).items():
            if count > 1:
                errors.append(
                    f"[{name or 'home'}] duplicate {kind} loaded {count} times: {target}"
                )
    breadcrumb_count = sum(
        path.name == "search-breadcrumbs.js" for path in script_targets
    )
    expected = 1 if name == "search" else 0
    if breadcrumb_count != expected:
        errors.append(
            f"[{name or 'home'}] breadcrumb script: expected {expected}, got {breadcrumb_count}"
        )
    return errors


def _controls(name, soup):
    """Verify Ulwazi's own navigation, tab, and local TOC wiring."""
    errors = []
    label = name or "home"
    drawer = soup.select_one("nav#drawer")
    if drawer is None:
        return [f"[{label}] global navigation: missing #drawer"]

    seen = set()
    checkboxes = drawer.select(".nav-item[data-checkbox] input.toctree-checkbox")
    if not checkboxes:
        errors.append(f"[{label}] global navigation: no expandable items")
    for checkbox in checkboxes:
        container = checkbox.find_parent(class_="nav-item")
        checkbox_id = checkbox.get("id")
        if not checkbox_id or checkbox_id in seen:
            errors.append(
                f"[{label}] navigation: missing/duplicate checkbox id {checkbox_id!r}"
            )
        seen.add(checkbox_id)
        corresponding_label = container.find("label", recursive=False)
        if (
            container.get("data-checkbox") != checkbox_id
            or not corresponding_label
            or corresponding_label.get("for") != checkbox_id
        ):
            errors.append(
                f"[{label}] navigation: checkbox {checkbox_id!r} does not match label/data-checkbox"
            )

    article = soup.select_one("main#content article")
    if not article:
        errors.append(f"[{label}] structure: missing main article")
        return errors
    for link in soup.select("nav.p-table-of-contents__nav a[href^='#']"):
        fragment = unquote(link.get("href", "")[1:])
        if fragment and not article.find(id=fragment):
            errors.append(
                f"[{label}] local TOC: {link.get('href')!r} has no target in article"
            )

    errors.extend(
        f"[{label}] notification: empty id on {notification.get_text(' ', strip=True)[:45]!r}"
        for notification in article.select('[class*="p-notification--"]')
        if notification.has_attr("id") and not notification.get("id")
    )

    tab_ids = [
        tag.get("id")
        for tag in article.select('.p-tabs [role="tab"], .p-tabs [role="tabpanel"]')
    ]
    if any(not value for value in tab_ids) or len(set(tab_ids)) != len(tab_ids):
        errors.append(f"[{label}] tabs: missing/duplicate tab button or panel ids")
    return errors


def test_assets_structure_fast(built_site):
    """Report all missing built assets and broken theme controls in one case."""
    errors = []
    for name in PAGES:
        soup = built_site.page(name)
        errors.extend(_assets(name, soup, built_site.output))
        if name != "search":  # The search page has no local TOC/article shell.
            errors.extend(_controls(name, soup))
    errors.extend(_check_remote_helpers())
    assert not errors, (
        "Assets and structure [fast] checks failed:\n  - " + "\n  - ".join(errors)
    )


def _remote_reference(url, source, inventory):
    """Register a static remote asset with its page or stylesheet provenance."""
    if url and urlsplit(url).scheme.lower() in {"http", "https"}:
        inventory[url].add(source)


def _html_sources(url, name, tag, attribute):
    """Find literal source locations; otherwise give the rendered HTML line.

    Sphinx's generated HTML does not retain source lines. Only claim an
    original file location when the exact asset URL occurs in that file.
    """
    locations = set()
    if urlsplit(url).scheme.lower() not in {"http", "https"}:
        return locations
    source = REPO / "docs" / name if name else REPO / "docs" / "index"
    for candidate in (
        source.with_suffix(".md"),
        source.with_suffix(".rst"),
        REPO / "docs/conf.py",
    ):
        if candidate.is_file():
            for number, text in enumerate(
                candidate.read_text(encoding="utf-8").splitlines(), 1
            ):
                if url in text:
                    locations.add(
                        f"{candidate.relative_to(REPO)}:{number} {tag.name}[{attribute}]"
                    )
        if locations:
            break
    if locations:
        return locations
    line = f":{tag.sourceline}" if tag.sourceline is not None else ""
    page = name or "index"
    return {f"rendered {page}/index.html{line} {tag.name}[{attribute}]"}


def _record_html_asset(url, name, tag, attribute, inventory):
    """Record every confirmed origin of a URL on a rendered page."""
    for location in _html_sources(url, name, tag, attribute):
        _remote_reference(url, location, inventory)


def _srcset_urls(value):
    """Return URLs from HTML srcset candidates (not a general HTML link crawler)."""
    # A data URL can contain commas; skip its contents up to the descriptor.
    candidates = []
    in_data_url = False
    for raw_candidate in value.split(","):
        candidate = raw_candidate.strip()
        if candidate.startswith("data:"):
            in_data_url = True
            continue
        if in_data_url:
            if any(candidate.endswith(suffix) for suffix in (" 1x", " 2x", " 3x")):
                in_data_url = False
            continue
        if candidate:
            candidates.append(candidate.split()[0])
    return candidates


def _css_urls(tokens, base, source, inventory):
    """Walk CSS tokens, including nested rules and variable definitions."""
    for token in tokens:
        location = f"{source}:{token.source_line}" if token.source_line else source
        if token.type == "at-rule" and token.lower_at_keyword == "import":
            for part in token.prelude:
                if part.type == "string":
                    _remote_reference(urljoin(base, part.value), location, inventory)
        if token.type == "url":
            _remote_reference(urljoin(base, token.value), location, inventory)
        elif token.type == "function":
            if token.lower_name == "url":
                argument = [
                    part
                    for part in token.arguments
                    if part.type not in {"whitespace", "comment"}
                ]
                if len(argument) == 1 and argument[0].type in {"string", "url"}:
                    _remote_reference(
                        urljoin(base, argument[0].value), location, inventory
                    )
            else:
                _css_urls(token.arguments, base, source, inventory)
        if hasattr(token, "content") and token.content is not None:
            _css_urls(token.content, base, source, inventory)
        if hasattr(token, "prelude") and token.prelude is not None:
            _css_urls(token.prelude, base, source, inventory)


def _remote_assets(site):  # noqa: PLR0912
    """Inventory static external assets on representative pages and local CSS."""
    inventory = defaultdict(set)
    stylesheets = set()
    for name in PAGES:
        label = name or "home"
        site.page(name)  # Fail clearly if the expected built page is absent.
        page = site.output / name / "index.html" if name else site.output / "index.html"
        soup = BeautifulSoup(page.read_text(encoding="utf-8"), "html.parser")

        for tag in soup.select(
            "link[href], script[src], img[src], img[srcset], source[src], source[srcset], meta[property], meta[name]"
        ):
            if tag.name == "link":
                rel = tag.get("rel")
                relations = rel if isinstance(rel, AttributeValueList) else []
                if not RESOURCE_LINK_RELS.intersection(relations):
                    continue
                href = str(tag.get("href", ""))
                _record_html_asset(href, name, tag, "href", inventory)
                if "stylesheet" in relations:
                    target = _local_target(site.output, page, href)
                    if (
                        target is not None
                        and target.is_file()
                        and target.suffix == ".css"
                    ):
                        stylesheets.add(target)
            elif tag.name == "meta":
                if (
                    tag.get("property") in RESOURCE_META
                    or tag.get("name") in RESOURCE_META
                ):
                    _record_html_asset(
                        tag.get("content", ""), name, tag, "content", inventory
                    )
            else:
                if tag.has_attr("src"):
                    _record_html_asset(tag["src"], name, tag, "src", inventory)
                if tag.has_attr("srcset"):
                    for url in _srcset_urls(tag["srcset"]):
                        _record_html_asset(url, name, tag, "srcset", inventory)

    for stylesheet in stylesheets:
        relative = stylesheet.relative_to(site.output)
        original = (
            REPO / "ulwazi/theme/ulwazi/static" / relative.relative_to("_static")
            if relative.parts[0] == "_static"
            else stylesheet
        )
        source = (
            str(original.relative_to(REPO))
            if original.is_file() and original.read_bytes() == stylesheet.read_bytes()
            else f"rendered {relative}"
        )
        base = stylesheet.as_uri()
        rules = tinycss2.parse_stylesheet(
            stylesheet.read_text(encoding="utf-8"),
            skip_comments=True,
            skip_whitespace=True,
        )
        _css_urls(rules, base, source, inventory)
    return inventory


def _public_url(url):
    """Reject local or credentialed destinations before making HTTP requests."""
    parsed = urlsplit(url)
    if (
        parsed.scheme not in {"https", "http"}
        or parsed.hostname not in REMOTE_ASSET_HOSTS
        or parsed.username
        or parsed.password
    ):
        return False
    try:
        addresses = socket.getaddrinfo(
            parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80)
        )
    except OSError:
        return False
    return bool(addresses) and all(
        ipaddress.ip_address(entry[4][0]).is_global for entry in addresses
    )


def _probe_asset(url, kind, session):  # noqa: PLR0911
    """Fetch only headers/first bytes, following at most five public redirects."""
    headers = {"User-Agent": "Ulwazi-theme-asset-check/1.0", "Range": "bytes=0-0"}
    for attempt in range(2):
        current = url
        try:
            for _ in range(6):
                if not _public_url(current):
                    return "non-public, unreachable, or credentialed destination"
                with session.get(
                    current,
                    headers=headers,
                    timeout=(3, 5),
                    stream=True,
                    allow_redirects=False,
                ) as response:
                    if response.status_code in {301, 302, 303, 307, 308}:
                        location = response.headers.get("Location")
                        if not location:
                            return f"HTTP {response.status_code} without Location"
                        current = urljoin(current, location)
                        continue
                    if (
                        response.status_code in {429, 500, 502, 503, 504}
                        and attempt == 0
                    ):
                        break
                    if not 200 <= response.status_code < 300:
                        return f"HTTP {response.status_code}"
                    content_type = (
                        response.headers.get("Content-Type", "")
                        .split(";", 1)[0]
                        .lower()
                    )
                    if content_type == "text/html" or (
                        kind == "css" and content_type and content_type != "text/css"
                    ):
                        return f"unexpected Content-Type {content_type}"
                    return None
            else:
                return "too many redirects"
        except requests.RequestException as exc:
            if attempt == 0:
                continue
            return f"{type(exc).__name__}: {exc}"
    return "request failed after retry"


@pytest.mark.slow
def _check_remote_inventory(inventory, session):
    """Probe one URL once and report all advisory problems together."""
    assert inventory, "Assets and structure [slow]: no remote references discovered"
    issues = []
    for url, sources in sorted(inventory.items()):
        kind = "css" if urlsplit(url).path.endswith(".css") else "other"
        reason = _probe_asset(url, kind, session)
        if reason:
            issues.append(
                f"{url} ({reason}; referenced by {', '.join(sorted(sources))})"
            )
    if issues:
        warnings.warn(
            "Assets and structure [slow]: remote availability is advisory; "
            "fallback not verified:\n  - " + "\n  - ".join(issues),
            RemoteAssetWarning,
            stacklevel=1,
        )


def _check_remote_helpers():  # noqa: PLR0915
    """Exercise advisory discovery and response handling offline in the fast case."""
    errors = []
    inventory = defaultdict(set)
    css = tinycss2.parse_stylesheet(
        "/* url(https://assets.ubuntu.com/fake.png) */"
        '@import "https://assets.ubuntu.com/import.css";'
        '@font-face { src: url("https://assets.ubuntu.com/font.woff2"); }'
        '.image { background: url("data:image/svg+xml,%3Csvg%3E"); }',
        skip_comments=True,
    )
    _css_urls(css, "file:///example/main.css", "[CSS] main.css", inventory)
    if set(inventory) != {
        "https://assets.ubuntu.com/import.css",
        "https://assets.ubuntu.com/font.woff2",
    }:
        errors.append(f"[remote] CSS discovery: unexpected URLs {list(inventory)}")
    candidates = _srcset_urls(
        "data:image/png;base64,https://invalid.example/fake.png 1x, "
        "https://assets.ubuntu.com/real.png 2x"
    )
    if candidates != ["https://assets.ubuntu.com/real.png"]:
        errors.append(f"[remote] srcset discovery: unexpected URLs {candidates}")

    tag = BeautifulSoup(
        '<img src="https://assets.ubuntu.com/image.png">', "html.parser"
    ).img
    file_sources = _html_sources(
        "https://assets.ubuntu.com/v1/d86746ef-cookie_banner.css", "", tag, "href"
    )
    if not any(source.startswith("docs/conf.py:") for source in file_sources):
        errors.append(
            f"[remote] provenance: missing docs/conf.py source: {file_sources}"
        )
    css_sources = defaultdict(set)
    _css_urls(
        tinycss2.parse_stylesheet(
            '.a { background: url("https://assets.ubuntu.com/test.png") }'
        ),
        "file:///example/main.css",
        "ulwazi/theme/ulwazi/static/css/main.css",
        css_sources,
    )
    if css_sources["https://assets.ubuntu.com/test.png"] != {
        "ulwazi/theme/ulwazi/static/css/main.css:1"
    }:
        errors.append(f"[remote] provenance: CSS line lost: {css_sources}")

    for status, expected in (
        (200, None),
        (206, None),
        (403, "HTTP 403"),
        (404, "HTTP 404"),
    ):
        response = MagicMock(status_code=status)
        response.headers = {"Content-Type": "image/png"}
        response.__enter__.return_value = response
        session = MagicMock()
        session.get.return_value = response
        with patch(f"{__name__}._public_url", return_value=True):
            actual = _probe_asset("https://assets.ubuntu.com/a.png", "other", session)
        if actual != expected or session.get.call_count != 1:
            errors.append(
                f"[remote] HTTP {status}: expected {expected!r}, got {actual!r}"
            )

    temporary = MagicMock(status_code=429)
    temporary.headers = {}
    temporary.__enter__.return_value = temporary
    recovered = MagicMock(status_code=200)
    recovered.headers = {"Content-Type": "image/png"}
    recovered.__enter__.return_value = recovered
    session = MagicMock()
    session.get.side_effect = [temporary, recovered]
    with patch(f"{__name__}._public_url", return_value=True):
        result = _probe_asset("https://assets.ubuntu.com/a.png", "other", session)
    if result is not None or session.get.call_count != 2:
        errors.append(f"[remote] HTTP 429 retry: expected recovery, got {result!r}")

    redirect = MagicMock(status_code=302)
    redirect.headers = {"Location": "http://127.0.0.1/private"}
    redirect.__enter__.return_value = redirect
    session = MagicMock()
    session.get.return_value = redirect
    with patch(f"{__name__}._public_url", side_effect=[True, False]):
        result = _probe_asset("https://assets.ubuntu.com/a.png", "other", session)
    if not result or "non-public" not in result or session.get.call_count != 1:
        errors.append(
            f"[remote] redirect: private destination not rejected: {result!r}"
        )

    session = MagicMock()
    session.get.side_effect = requests.Timeout("timed out")
    with patch(f"{__name__}._public_url", return_value=True):
        result = _probe_asset("https://assets.ubuntu.com/a.png", "other", session)
    if not result or "Timeout" not in result or session.get.call_count != 2:
        errors.append(f"[remote] timeout: expected one retry, got {result!r}")
    if any(
        _public_url(url)
        for url in (
            "http://127.0.0.1/private",
            "https://user:secret@assets.ubuntu.com/file",
            "https://invalid.example/file",
        )
    ):
        errors.append("[remote] security: unreviewed or private host allowed")

    assets = {
        "https://assets.ubuntu.com/a.png": {
            "docs/content/myst-cheat-sheet.md:439 img[src]",
            "docs/content/rst-cheat-sheet.rst:554 img[src]",
        },
        "https://assets.ubuntu.com/b.css": {"docs/conf.py:362 link[href]"},
    }
    with patch(
        f"{__name__}._probe_asset", side_effect=["HTTP 404", "HTTP 429"]
    ) as probe:
        with pytest.warns(RemoteAssetWarning) as recorded:
            _check_remote_inventory(assets, MagicMock())
    message = str(recorded[0].message)
    if (
        probe.call_count != 2
        or not all(
            item in message
            for item in (
                "HTTP 404",
                "HTTP 429",
                "docs/content/myst-cheat-sheet.md:439",
                "docs/content/rst-cheat-sheet.rst:554",
                "docs/conf.py:362",
                "fallback not verified",
            )
        )
        or "fallback succeeded" in message
    ):
        errors.append(
            "[remote] warning: status, provenance or fallback label incorrect"
        )
    with patch(f"{__name__}._probe_asset", return_value=None):
        with warnings.catch_warnings(record=True) as emitted:
            _check_remote_inventory(assets, MagicMock())
    if emitted:
        errors.append("[remote] warning: healthy assets emitted a warning")
    return errors


@pytest.mark.slow
def test_assets_structure_slow(built_site):
    """Warn on temporarily unreachable remote resources; do not gate releases."""
    with requests.Session() as session:
        _check_remote_inventory(_remote_assets(built_site), session)
