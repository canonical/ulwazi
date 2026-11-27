"""Layer 3: turn ``adoption.json`` into a static dashboard."""

from __future__ import annotations

import csv
import datetime as dt
import json
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any

import jinja2

from tools.adoption import SCHEMA_VERSION
from tools.adoption.models import DataError, read_json
from tools.adoption.process.summary import read_history
from tools.adoption.render.view import build_view

LOG = logging.getLogger("adoption")

HERE = Path(__file__).parent
REPO_ROOT = HERE.parents[2]
SCSS_SOURCE = HERE / "assets" / "dashboard.scss"
STATIC_FILES = ("dashboard.js",)
THEME_ASSETS = REPO_ROOT / "ulwazi" / "theme" / "ulwazi" / "assets"
CSV_COLUMNS = (
    "slug",
    "name",
    "docs_url",
    "repository",
    "repository_url",
    "docs_path",
    "scope",
    "sphinx_stack",
    "sphinx_stack_declared",
    "sphinx_stack_corrected",
    "ulwazi",
    "ulwazi_state",
    "last_build",
)


class RenderError(Exception):
    """Raised when the dashboard cannot be built."""


def build_css(destination: Path) -> None:
    """Compile ``dashboard.scss`` with the same Sass setup as the theme."""
    sass = REPO_ROOT / "node_modules" / ".bin" / "sass"
    executable = str(sass) if sass.exists() else shutil.which("sass")
    if executable is None:
        raise RenderError(
            "Sass is not installed; run 'npm install' in the repository root "
            "(or use --no-css)"
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    command = [
        executable,
        f"--load-path={REPO_ROOT / 'node_modules'}",
        f"--load-path={THEME_ASSETS}",
        "--style=compressed",
        "--no-source-map",
        "--quiet-deps",
        str(SCSS_SOURCE),
        str(destination),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RenderError(f"Sass failed:\n{result.stderr.strip()}")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write the table as CSV for spreadsheets."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in CSV_COLUMNS})


def render_site(
    adoption_json: Path,
    history_file: Path,
    build_dir: Path,
    *,
    compile_css: bool = True,
    now: dt.datetime | None = None,
) -> Path:
    """Write ``index.html`` and its assets to ``build_dir``; return the page path."""
    data = read_json(adoption_json)
    if data.get("schema_version") != SCHEMA_VERSION:
        raise DataError(
            f"{adoption_json} has schema_version {data.get('schema_version')!r}; "
            f"expected {SCHEMA_VERSION}"
        )
    now = now or dt.datetime.now(dt.UTC)
    history = read_history(history_file)
    view = build_view(data, history, now=now)

    environment = jinja2.Environment(
        loader=jinja2.FileSystemLoader(HERE / "templates"),
        autoescape=jinja2.select_autoescape(["html", "j2"]),
        undefined=jinja2.StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    html = environment.get_template("index.html.j2").render(**view)

    build_dir.mkdir(parents=True, exist_ok=True)
    page = build_dir / "index.html"
    page.write_text(html, encoding="utf-8")
    for name in STATIC_FILES:
        shutil.copyfile(HERE / "static" / name, build_dir / name)
    (build_dir / "adoption.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    write_csv(build_dir / "projects.csv", view["csv_rows"])
    if compile_css:
        build_css(build_dir / "dashboard.css")
    LOG.info("Wrote %s", page)
    return page
