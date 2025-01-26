from os import path
from pathlib import Path
import importlib.util


THEME_PATH = (Path(__file__).parent / "theme" / "ulwazi").resolve()

# See http://www.sphinx-doc.org/en/stable/theming.html#distribute-your-theme-as-a-python-package
def setup(app):
    app.add_html_theme('ulwazi', str(THEME_PATH))

    app.connect(  # pyright: ignore [reportUnknownMemberType]
        "config-inited",
        config_inited,
    )

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }

def config_inited(app, config):  # noqa: ANN401
    """Read user-provided values and setup defaults."""

    html_context = config.html_context

    required_packages = [
        "sphinxcontrib.jquery",
    ]

    for package in required_packages:
        try:
            if importlib.util.find_spec(package) is not None:
                app.setup_extension(package)
            else:
                print(f"{package} not found.\n{package} will not be configured.")
        except ModuleNotFoundError:  # noqa: PERF203
            print(f"{package} not found.\n{package} will not be configured.")

    extra_css = [
        "css/debug.css",
        # "css/skeleton.css",
        "css/vanilla-framework-version-4.18.5.min.css",
    ]

    extra_js = [
        "js/scripts.js",
        "js/top-menu.js"
        # "js/header-nav.js",
        # "js/dropdown.js"
    ]

    values_and_defaults = [
        ("product_tag", "_static/tag.png"),
        ("github_version", "main"),
        ("github_folder", "docs"),
        ("github_issues", "enabled"),
        ("discourse", "https://discourse.ubuntu.com"),
        ("sequential_nav", "none"),
        ("display_contributors", True),
        ("path", "/docs"),
    ]

    for value, default in values_and_defaults:
        html_context.setdefault(value, default)

    config.html_css_files.extend(extra_css)
    config.html_js_files.extend(extra_js)