"""Fast, user-visible smoke checks for the Ulwazi home page."""


def test_smoke_fast(built_site):
    """One result for the basic page shell, with individually labelled failures."""
    soup = built_site.page("")
    errors = []
    article = soup.select_one("main#content article[role=main]")
    if not article or not any(
        "Welcome to the Ulwazi theme preview" in heading.get_text(" ", strip=True)
        for heading in article.select("h1")
    ):
        errors.append("[home] article: missing welcome heading in main content")
    if not article or "Vanilla Framework-based theme" not in article.get_text(
        " ", strip=True
    ):
        errors.append("[home] article: preview description is missing")

    for label, selector in (
        ("header", "header#navigation"),
        ("global navigation", "nav#drawer.p-side-navigation--raw-html"),
        ("footer", "footer.l-docs__footer"),
    ):
        if soup.select_one(selector) is None:
            errors.append(f"[home] {label}: missing {selector}")

    if not soup.select_one('a.p-link--skip[href="#content"]') or not soup.select_one(
        "main#content"
    ):
        errors.append("[home] accessibility: skip link must target main#content")

    home = soup.select_one('#drawer a[aria-current="page"]')
    if (
        not home
        or home.get_text(" ", strip=True) != "Home"
        or "is-active" not in home.get("class", [])
    ):
        errors.append("[home] navigation: Home must be the active current-page link")

    # Example code in documentation can legitimately contain Jinja delimiters.
    for tag in soup.select("pre, code, script, style"):
        tag.decompose()
    visible = soup.get_text(" ", strip=True)
    errors.extend(
        f"[home] template: unrendered {delimiter!r} in visible text"
        for delimiter in ("{{", "{%", "{#")
        if delimiter in visible
    )

    assert not errors, "Smoke [fast] checks failed:\n  - " + "\n  - ".join(errors)
