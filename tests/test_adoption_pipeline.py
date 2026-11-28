"""Offline tests of the adoption tool's detection and processing layers.

Nothing here touches the network: GitHub is replaced by an in-memory fake and
the Read the Docs data comes from small fixtures.
"""

# Tests dereference results that would fail the test anyway if they were None.
# pyright: reportOptionalMemberAccess=false, reportOptionalIterable=false

import datetime as dt
import json
import zlib
from pathlib import Path
from typing import Any

import pytest

from adoption_samples import TODAY
from tools.adoption.cache import Cache
from tools.adoption.config import ConfigError, load_config
from tools.adoption.detect.normalize import is_public, parse_repo_url
from tools.adoption.detect.rtd_api import RtdClient, RtdError, detect_from_api
from tools.adoption.detect.rtd_file import detect_from_file
from tools.adoption.models import DataError, RtdProject, write_json
from tools.adoption.process import pipeline
from tools.adoption.process.corrections import KNOWN_ISSUES, correct_version
from tools.adoption.process.github import GitHub, RepoFiles, RepoInfo
from tools.adoption.process.live_site import LiveResult, parse_page
from tools.adoption.process.locate import (
    locate_docs,
    python_requirements,
    sphinx_configuration,
)
from tools.adoption.process.requirements import (
    parse_pyproject,
    parse_requirements_txt,
)
from tools.adoption.process.stack import detect_stack
from tools.adoption.process.summary import deltas, summarize, update_history
from tools.adoption.process.ulwazi import resolve_ulwazi
from tools.adoption.process.ulwazi_releases import (
    Catalogue,
    Release,
    asset_checksum,
)
from tools.adoption.process.ulwazi_repo import RepoUlwazi, analyse_repo, parse_conf
from tools.adoption.process.upstream import Upstream, git_blob_sha

OID = "a" * 40
PRIVATE_NAME = "secret-private-project"


class FakeGitHub(GitHub):
    """GitHub backed by dictionaries: ``{(owner, name, ref): {path: content}}``."""

    def __init__(self, repos: dict[tuple[str, str, str], dict[str, str]]) -> None:
        super().__init__(None, Cache(None))
        self.repos = repos
        self.visible: dict[tuple[str, str], RepoInfo | None] = {}

    def raw(self, owner: str, name: str, ref: str, path: str) -> bytes | None:
        content = self.repos.get((owner, name, ref), {}).get(path)
        return None if content is None else content.encode()

    def tree(self, owner: str, name: str, oid: str) -> list[str]:
        return sorted(self.repos.get((owner, name, oid), {}))

    def repo_infos(self, repos):
        return {key: self.visible.get(key) for key in repos}

    def docs_commit_dates(self, items):
        dates: dict[tuple[str, str, str, str], str | None] = {}
        for item in items:
            dates[item] = "2026-11-20T10:00:00+00:00"
        return dates

    def releases(self, repo: str) -> list[dict[str, Any]]:
        return [{"tag_name": tag} for tag in ("1.0", "2.0", "3.0")]


# Trimmed copies of the real upstream files. ``main`` already had the new
# update script, check_removed_urls.py and Makefile before the 3.0 changes.
MAKEFILE_3_0 = "CHECK_PATH ?= $(filter-out $(DOCS_VENVDIR) $(DOCS_BUILDDIR) $(DEV_DIR),$(wildcard *))\n"
REQUIREMENTS_2_0 = (
    "canonical-sphinx~=0.6\nsphinx-roles~=0.1\nsphinx-terminal~=1.0\nsphinx-llm~=0.4\n"
)
REQUIREMENTS_3_0 = (
    "ulwazi~=1.0\nsphinx-roles~=1.0\nsphinx-terminal~=1.1\nsphinx-llm~=1.1\n"
    "sphinx-modern-pdf-style~=0.1\n"
)
CONF_2_0 = 'extensions = ["canonical_sphinx", "notfound.extension"]\n'
CONF_3_0 = 'html_theme = "ulwazi"\nextensions = ["ulwazi", "sphinx_modern_pdf_style"]\n'
MAIN_BEFORE_3_0 = {
    "docs/_dev/version": "2.0\n",
    "docs/_dev/update_sp.py": "# update script 3.0\n",
    "docs/_dev/check_removed_urls.py": "# removed urls\n",
    "docs/Makefile": MAKEFILE_3_0,
    "docs/requirements.txt": REQUIREMENTS_2_0,
    "docs/conf.py": CONF_2_0,
}
UPSTREAM_FILES = {
    ("canonical", "sphinx-stack", "2.0"): {
        "docs/_dev/version": "2.0\n",
        "docs/_dev/update_sp.py": "# update script 2.0\n",
        "docs/requirements.txt": REQUIREMENTS_2_0,
        "docs/conf.py": CONF_2_0,
    },
    ("canonical", "sphinx-stack", KNOWN_ISSUES[0].baseline): MAIN_BEFORE_3_0,
    ("canonical", "sphinx-stack", "3.0"): {
        **MAIN_BEFORE_3_0,
        "docs/requirements.txt": REQUIREMENTS_3_0,
        "docs/conf.py": CONF_3_0,
    },
}


def make_files(
    project_files: dict[str, str],
    *,
    upstream: dict[tuple[str, str, str], dict[str, str]] | None = None,
) -> tuple[RepoFiles, Upstream]:
    repos = {("canonical", "docs-repo", OID): project_files}
    repos.update(UPSTREAM_FILES if upstream is None else upstream)
    github = FakeGitHub(repos)
    return RepoFiles(github, "canonical", "docs-repo", OID), Upstream(
        github, "canonical/sphinx-stack"
    )


def stack_of(project_files: dict[str, str], **kwargs: Any) -> Any:
    files, upstream = make_files(project_files, **kwargs)
    docs = locate_docs(files, rtd_yaml=None)
    return detect_stack(files, docs, upstream, latest="3.0")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


def write_config(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "config.toml"
    path.write_text(body, encoding="utf-8")
    return path


def test_shipped_config_is_valid():
    config = load_config()
    assert config.mode == "auto"
    assert config.rtd_organization


def test_exclusion_needs_a_reason(tmp_path):
    path = write_config(tmp_path, '[[exclude]]\nslug = "internal-*"\n')
    with pytest.raises(ConfigError, match="reason"):
        load_config(path)


def test_manual_mode_needs_include_entries(tmp_path):
    path = write_config(tmp_path, '[tracking]\nmode = "manual"\n')
    with pytest.raises(ConfigError, match="include"):
        load_config(path)


def test_opt_out_and_opt_in_rules(tmp_path):
    out = load_config(
        write_config(
            tmp_path,
            '[[exclude]]\nslug = "internal-*"\nreason = "internal"\n'
            '[[exclude]]\nrepo = "Canonical/Old-*"\nreason = "archived"\n',
        )
    )
    assert out.exclusion("internal-notes", None).reason == "internal"
    assert out.exclusion("anything", "canonical/old-project").reason == "archived"
    assert out.exclusion("juju", "canonical/juju") is None
    assert out.is_included("anything", None)

    manual = load_config(
        write_config(
            tmp_path, '[tracking]\nmode = "manual"\n[[include]]\nslug = "ulwazi"\n'
        )
    )
    assert manual.is_included("ulwazi", None)
    assert not manual.is_included("juju", "canonical/juju")


def test_graphql_queries_are_well_formed_and_batched():
    queries: list[str] = []

    class Recorder(GitHub):
        def _graphql(self, query: str) -> dict[str, Any]:
            queries.append(query)
            return {}

    github = Recorder(None, Cache(None))
    repos = [("canonical", f"repo-{index}") for index in range(95)]
    infos = github.repo_infos(repos)
    assert len(queries) == 3  # 40 + 40 + 15 repositories
    assert set(infos) == set(repos)
    assert all(
        info is None for info in infos.values()
    )  # an empty answer is "not visible"

    dates = github.docs_commit_dates(
        [("canonical", "a", OID, "docs"), ("canonical", "b", OID, ".")]
    )
    assert dates == {
        ("canonical", "a", OID, "docs"): None,
        ("canonical", "b", OID, "."): None,
    }
    for query in queries:
        assert query.count("{") == query.count("}")
        assert "(" in query
        assert query.count("(") == query.count(")")
    assert 'path: "docs"' in queries[-1]
    assert queries[-1].count("path:") == 1  # the repository root has no path filter

    with pytest.raises(pipeline.GitHubError, match="Unsupported repository name"):
        github.repo_infos([("canonical", 'bad"name')])
    with pytest.raises(pipeline.GitHubError, match="Not a commit id"):
        github.docs_commit_dates([("canonical", "a", "HEAD", "docs")])


def test_cache_survives_concurrent_writes_of_the_same_key(tmp_path):
    from concurrent.futures import ThreadPoolExecutor  # noqa: PLC0415

    cache = Cache(tmp_path)
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda _: cache.put("raw", "same-key", b"data"), range(200)))
    assert cache.get("raw", "same-key").data == b"data"
    cache.put("raw", "missing", None)
    hit = cache.get("raw", "missing")
    assert hit is not None
    assert hit.data is None
    assert cache.get("raw", "never-stored") is None
    assert Cache(None).get("raw", "same-key") is None


# ---------------------------------------------------------------------------
# Detection layer
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://github.com/canonical/ulwazi", ("github.com", "canonical", "ulwazi")),
        (
            "https://github.com/canonical/ulwazi.git",
            ("github.com", "canonical", "ulwazi"),
        ),
        ("git@github.com:canonical/ulwazi.git", ("github.com", "canonical", "ulwazi")),
        (
            "ssh://git@github.com/canonical/ulwazi/",
            ("github.com", "canonical", "ulwazi"),
        ),
        ("https://launchpad.net/juju", ("launchpad.net", None, None)),
        ("", None),
        ("not a url", None),
    ],
)
def test_parse_repo_url(url, expected):
    assert parse_repo_url(url) == expected


def test_privacy_rules():
    business = "https://app.readthedocs.com"
    community = "https://app.readthedocs.org"
    assert is_public(
        {"privacy_level": "public"}, base_url=business, assume_public=False
    )
    assert not is_public(
        {"privacy_level": "private"}, base_url=business, assume_public=True
    )
    assert not is_public({}, base_url=business, assume_public=False)
    assert is_public({}, base_url=business, assume_public=True)
    assert is_public({}, base_url=community, assume_public=False)

    # A private Business project whose default version is public (like
    # canonical-ulwazi) is listed; a private version, an API error or a
    # missing default version keeps it out.
    class FakeRtd(RtdClient):
        def __init__(self) -> None:
            super().__init__(business, "token", Cache(None))

        def list_projects(self, organization):
            yield {"slug": "public-one", "privacy_level": "public"}
            for slug in ("open-docs", PRIVATE_NAME, "broken", "no-version"):
                yield {
                    "slug": slug,
                    "privacy_level": "private",
                    "default_version": None if slug == "no-version" else "main",
                    "readthedocs_yaml_path": None,
                    "repository": {"url": f"git@github.com:canonical/{slug}.git"},
                }

        def version_privacy(self, slug, version):
            if slug == "broken":
                raise RtdError("HTTP 500")
            return "public" if slug == "open-docs" else "private"

    kept = detect_from_api(FakeRtd(), "canonical", include_builds=False)
    assert [p.slug for p in kept] == ["public-one", "open-docs"]
    assert kept[1].repo_url == "https://github.com/canonical/open-docs"
    assert PRIVATE_NAME not in json.dumps([vars(p) for p in kept])


def test_file_import_drops_private_and_translations(tmp_path):
    export = tmp_path / "projects.json"
    export.write_text(
        json.dumps(
            [
                {
                    "slug": "public-one",
                    "privacy_level": "public",
                    "repository": {"url": "https://github.com/canonical/one"},
                },
                {
                    "slug": PRIVATE_NAME,
                    "privacy_level": "private",
                    "repository": {"url": "https://github.com/canonical/secret"},
                },
                {
                    "slug": "public-one-de",
                    "privacy_level": "public",
                    "translation_of": "public-one",
                },
                {"slug": "no-privacy-column"},
            ]
        ),
        encoding="utf-8",
    )
    base = "https://app.readthedocs.com"
    kept = detect_from_file(export, base_url=base)
    assert [p.slug for p in kept] == ["public-one"]
    assert kept[0].repo_owner == "canonical"
    assert kept[0].docs_url.startswith("https://")
    assert PRIVATE_NAME not in json.dumps([vars(p) for p in kept])
    trusted = detect_from_file(export, base_url=base, assume_public=True)
    assert {p.slug for p in trusted} == {"public-one", "no-privacy-column"}


def test_file_import_reads_csv(tmp_path):
    export = tmp_path / "projects.csv"
    export.write_text(
        "Slug,Repository URL,Privacy Level\n"
        "one,https://github.com/canonical/one,public\n"
        "two,https://github.com/canonical/two,private\n",
        encoding="utf-8",
    )
    kept = detect_from_file(export, base_url="https://app.readthedocs.com")
    assert [(p.slug, p.repo_name) for p in kept] == [("one", "one")]


# ---------------------------------------------------------------------------
# Requirements and docs location
# ---------------------------------------------------------------------------


def test_requirements_parsing():
    found = parse_requirements_txt(
        "# comment\nulwazi~=1.0  # theme\nSphinx_Roles==1.0\n-r other.txt\n"
        "git+https://github.com/canonical/ulwazi.git@main#egg=ulwazi\n"
    )
    assert not found["ulwazi"].vcs  # the first declaration wins
    assert found["sphinx-roles"].specifier == "==1.0"
    found = parse_requirements_txt("ulwazi~=1.0\nsphinx_roles>=1,<2\n")
    assert found["ulwazi"].accepts("1.0.3")
    assert not found["ulwazi"].accepts("2.0")
    assert found["sphinx-roles"].accepts("1.5")
    vcs = parse_requirements_txt(
        "git+https://github.com/canonical/ulwazi.git#egg=ulwazi"
    )
    assert vcs["ulwazi"].display == "git"


def test_pyproject_parsing():
    found = parse_pyproject(
        '[project]\ndependencies = ["ulwazi~=1.0"]\n'
        '[dependency-groups]\ndocs = ["sphinx-design", {include-group = "x"}]\n'
    )
    assert set(found) == {"ulwazi", "sphinx-design"}
    assert parse_pyproject("not toml [") == {}


RTD_YAML = """\
version: 2
sphinx:
  configuration: docs/custom/conf.py
python:
  install:
    - requirements: docs/requirements.txt
"""


def test_readthedocs_yaml_parsing():
    assert sphinx_configuration(RTD_YAML) == "docs/custom/conf.py"
    assert sphinx_configuration("version: 2\n") is None
    assert python_requirements(RTD_YAML) == ["docs/requirements.txt"]


def test_locate_prefers_version_file_then_configuration_then_tree():
    files, _ = make_files({"docs/_dev/version": "2.0", "docs/conf.py": ""})
    found = locate_docs(files, rtd_yaml=None)
    assert (found.path, found.version_file) == ("docs", "docs/_dev/version")

    files, _ = make_files({"documentation/conf.py": ""})
    found = locate_docs(files, rtd_yaml=None)
    assert (found.path, found.how) == ("documentation", "common location")

    files, _ = make_files({"product/site/conf.py": ""})
    assert locate_docs(files, rtd_yaml=None).path == "product/site"

    files, _ = make_files({"docs/conf.py": "", "elsewhere/_dev/version": "2.0"})
    assert locate_docs(files, rtd_yaml=None).path == "docs"
    assert locate_docs(files, rtd_yaml=None, override="elsewhere").path == "elsewhere"

    files, _ = make_files({"README.md": ""})
    assert locate_docs(files, rtd_yaml=None) is None


def test_locate_keeps_leading_dots():
    files, _ = make_files({"docs/.sphinx/version": "1.6", "docs/conf.py": ""})
    assert locate_docs(files, rtd_yaml=None).version_file == "docs/.sphinx/version"


# ---------------------------------------------------------------------------
# Sphinx Stack version detection and the 3.0 correction
# ---------------------------------------------------------------------------


def test_version_file_is_authoritative():
    result = stack_of({"docs/_dev/version": "2.0\n", "docs/conf.py": ""})
    assert (result.version, result.corrected, result.kind) == ("2.0", False, "released")

    result = stack_of({"docs/.sphinx/version": "1.6\n", "docs/conf.py": ""})
    assert (result.version, result.is_latest) == ("1.6", False)

    result = stack_of({"docs/_dev/version": "3.0\n"})
    assert (result.version, result.is_latest) == ("3.0", True)


def test_stale_3_0_file_is_corrected_by_the_release_changes():
    result = stack_of(
        {
            "docs/_dev/version": "2.0\n",
            "docs/requirements.txt": "ulwazi~=1.0\nsphinx-roles~=1.0\n",
        }
    )
    assert (result.version, result.declared, result.corrected) == ("3.0", "2.0", True)
    assert result.is_latest
    text = next(e.text for e in result.evidence if e.label == "Version corrected")
    assert "ulwazi instead of canonical-sphinx" in text
    assert "sphinx-roles >= 1.0" in text

    # The full 3.0 template is corrected too; signs can also come from conf.py.
    assert (
        stack_of(UPSTREAM_FILES[("canonical", "sphinx-stack", "3.0")]).version == "3.0"
    )
    files = {
        "docs/_dev/version": "2.0\n",
        "docs/conf.py": CONF_3_0,
        "docs/requirements.txt": "ulwazi\n",
    }
    assert stack_of(files).version == "3.0"


def test_files_from_main_between_releases_are_not_3_0():
    # Regression: canonical/opensearch-operator (2.0 + update_sp.py copied
    # from main) and other charm docs were reported as 3.0.
    result = stack_of(MAIN_BEFORE_3_0)
    assert (result.version, result.corrected) == ("2.0", False)


def test_ulwazi_alone_or_dependency_bumps_alone_are_not_enough():
    only_ulwazi = {"docs/_dev/version": "2.0\n", "docs/requirements.txt": "ulwazi\n"}
    assert stack_of(only_ulwazi).version == "2.0"
    only_bumps = {
        "docs/_dev/version": "2.0\n",
        "docs/requirements.txt": "canonical-sphinx~=0.6\nsphinx-roles~=1.0\n"
        "sphinx-terminal~=1.1\nsphinx-llm~=1.1\n",
    }
    assert stack_of(only_bumps).version == "2.0"


def test_signs_already_on_main_before_the_release_are_ignored(caplog):
    upstream = dict(UPSTREAM_FILES)
    baseline = ("canonical", "sphinx-stack", KNOWN_ISSUES[0].baseline)
    # Pretend main had already switched to Ulwazi before the release.
    upstream[baseline] = {
        **MAIN_BEFORE_3_0,
        "docs/requirements.txt": "ulwazi~=1.0\nsphinx-roles~=0.1\n",
    }
    files = {"docs/_dev/version": "2.0\n", "docs/requirements.txt": REQUIREMENTS_3_0}
    with caplog.at_level("WARNING", logger="adoption"):
        result = stack_of(files, upstream=upstream)
    assert (result.version, result.corrected) == ("2.0", False)
    assert "'requirements.txt lists ulwazi instead of canonical-sphinx'" in caplog.text
    assert "does not separate" in caplog.text
    # conf.py still separates the releases, so it alone can still correct.
    files["docs/conf.py"] = CONF_3_0
    assert stack_of(files, upstream=upstream).version == "3.0"


def test_correction_switches_off_when_upstream_fixes_the_tag():
    fixed = {
        ("canonical", "sphinx-stack", "2.0"): UPSTREAM_FILES[
            ("canonical", "sphinx-stack", "2.0")
        ],
        ("canonical", "sphinx-stack", "3.0"): {
            **UPSTREAM_FILES[("canonical", "sphinx-stack", "3.0")],
            "docs/_dev/version": "3.0\n",
        },
    }
    result = stack_of(
        {"docs/_dev/version": "2.0\n", "docs/requirements.txt": REQUIREMENTS_3_0},
        upstream=fixed,
    )
    assert (result.version, result.corrected) == ("2.0", False)


def test_correction_can_be_disabled_and_only_touches_2_0():
    files, upstream = make_files(
        {"docs/_dev/version": "2.0\n", "docs/requirements.txt": REQUIREMENTS_3_0}
    )
    docs = locate_docs(files, rtd_yaml=None)
    assert (
        detect_stack(files, docs, upstream, latest="3.0", correct=False).version
        == "2.0"
    )
    files, upstream = make_files(
        {"docs/_dev/version": "1.6\n", "docs/requirements.txt": REQUIREMENTS_3_0}
    )
    docs = locate_docs(files, rtd_yaml=None)
    assert detect_stack(files, docs, upstream, latest="3.0").version == "1.6"


def test_legacy_and_missing_stack():
    result = stack_of({"docs/custom_conf.py": "", "docs/conf.py": ""})
    assert (result.detected, result.kind, result.version) == (True, "legacy", "< 1.0")
    result = stack_of({"docs/conf.py": ""})
    assert not result.detected
    result = stack_of({"README.md": ""})
    assert not result.detected
    result = stack_of({"docs/_dev/version": "garbage text\n", "docs/conf.py": ""})
    assert not result.detected


def test_correct_version_matches_git_blob_hash():
    # `git hash-object` of "hello\n" is a well-known value.
    assert git_blob_sha(b"hello\n") == "ce013625030ba8dba906f756967f9e9ca394464a"
    assert correct_version("1.6", None) is None  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Ulwazi in the repository, in releases and on the live site
# ---------------------------------------------------------------------------


def test_parse_conf_reads_theme_and_extensions():
    facts = parse_conf(
        'html_theme = "ulwazi"\nextensions = ["myst_parser", "ulwazi"]\n'
        'extensions += ["sphinx_design"]\nextensions.append("sphinx_roles")\n'
    )
    assert facts.theme == "ulwazi"
    assert facts.extensions == {
        "myst_parser",
        "ulwazi",
        "sphinx_design",
        "sphinx_roles",
    }
    assert parse_conf("html_theme = os.environ['T']\n").theme == "<dynamic>"
    assert parse_conf("html_theme = 'furo'\nthis is not python(\n").theme == "furo"


def test_repo_analysis_reads_conf_and_requirements():
    files, _ = make_files(
        {
            "docs/_dev/version": "3.0",
            "docs/conf.py": 'html_theme = "ulwazi"\nextensions = ["ulwazi"]\n',
            "docs/requirements.txt": "ulwazi~=1.0\n",
        }
    )
    docs = locate_docs(files, rtd_yaml=None)
    result = analyse_repo(files, docs, None)
    assert result.uses_theme
    assert result.extension_enabled
    assert result.requirement.display == "~=1.0"
    assert result.requirement_file == "docs/requirements.txt"

    files, _ = make_files(
        {
            "docs/conf.py": "html_theme = 'furo'\n",
            "docs/pyproject.toml": '[project]\ndependencies=["ulwazi"]\n',
        }
    )
    docs = locate_docs(files, rtd_yaml=None)
    result = analyse_repo(files, docs, None)
    assert not result.uses_theme
    assert result.requirement_file == "docs/pyproject.toml"


def test_asset_checksum_matches_sphinx(tmp_path):
    from sphinx.builders.html._assets import _file_checksum  # noqa: PLC0415

    content = b"body {\r\n  color: red;\r\n}\n"
    (tmp_path / "x.css").write_bytes(content)
    assert asset_checksum(content) == _file_checksum(tmp_path, "x.css")
    stripped = content.replace(b"\r", b"")
    assert asset_checksum(content) == f"{zlib.crc32(stripped):08x}"


def release(version: str, css: str, *, uploaded: str = "2026-01-01") -> Release:
    return Release(
        version,
        dt.datetime.fromisoformat(uploaded).replace(tzinfo=dt.UTC),
        {"css/vanilla-main.css": css, "js/search.js": f"s{css[:7]}"},
    )


CATALOGUE = Catalogue(
    [
        release("1.0.0", "00000001", uploaded="2026-10-12"),
        release("1.0.1", "00000002", uploaded="2026-10-16"),
        release("1.0.2", "00000002", uploaded="2026-10-17"),
        release("1.0.3", "00000003", uploaded="2026-11-20"),
    ]
)


def test_catalogue_matching():
    exact = CATALOGUE.match({"css/vanilla-main.css": "00000003"})
    assert [r.version for r in exact] == ["1.0.3"]
    several = CATALOGUE.match({"css/vanilla-main.css": "00000002"})
    assert [r.version for r in several] == ["1.0.1", "1.0.2"]
    assert CATALOGUE.match({"css/vanilla-main.css": "deadbeef"}) == []
    assert CATALOGUE.match({"css/default.css": "00000003"}) is None
    # A project may override another asset; the stylesheet still decides.
    assert [
        r.version
        for r in CATALOGUE.match(
            {"css/vanilla-main.css": "00000003", "js/search.js": "custom00"}
        )
    ] == ["1.0.3"]


def test_newest_matching_respects_the_build_date():
    assert CATALOGUE.newest_matching("~=1.0").version == "1.0.3"
    built = dt.datetime(2026, 10, 20, tzinfo=dt.UTC)
    assert CATALOGUE.newest_matching("~=1.0", built).version == "1.0.2"
    assert CATALOGUE.newest_matching("<1.0.1").version == "1.0.0"
    assert CATALOGUE.newest_matching(">=9") is None
    assert CATALOGUE.newest_matching("not a specifier") is None


def test_parse_live_page():
    html = (
        '<link rel="stylesheet" href="../_static/css/vanilla-main.css?v=00000003" />'
        '<script src="../_static/js/search.js?v=abcdef01"></script>'
        '<script>localStorage.getItem("ulwazi-theme")</script>'
    )
    uses, assets = parse_page(html)
    assert uses
    assert assets == {"css/vanilla-main.css": "00000003", "js/search.js": "abcdef01"}
    assert parse_page('<link href="_static/furo.css?v=12345678">') == (
        False,
        {"furo.css": "12345678"},
    )
    assert parse_page("<html></html>") == (False, {})


def live(
    *,
    uses: bool,
    assets: dict[str, str] | None = None,
    ok: bool = True,
    error: str | None = None,
) -> LiveResult:
    return LiveResult(
        checked=True, ok=ok, error=error, uses_ulwazi=uses, assets=assets or {}
    )


def repo_with(theme: str | None, requirement: str | None = "~=1.0") -> RepoUlwazi:
    from tools.adoption.process.requirements import Req  # noqa: PLC0415

    return RepoUlwazi(
        theme=theme, requirement=Req("ulwazi", requirement) if requirement else None
    )


def test_ulwazi_version_from_the_live_site():
    result = resolve_ulwazi(
        repo_with("ulwazi"),
        live(uses=True, assets={"css/vanilla-main.css": "00000003"}),
        CATALOGUE,
    )
    assert (result.uses, result.state, result.version, result.precision) == (
        True,
        "live",
        "1.0.3",
        "exact",
    )

    result = resolve_ulwazi(
        None, live(uses=True, assets={"css/vanilla-main.css": "00000002"}), CATALOGUE
    )
    assert (result.version, result.precision) == ("1.0.1\u20131.0.2", "range")

    result = resolve_ulwazi(
        None, live(uses=True, assets={"css/vanilla-main.css": "deadbeef"}), CATALOGUE
    )
    assert (result.version, result.precision) == ("dev", "dev")


def test_ulwazi_pending_deploy_and_not_used():
    result = resolve_ulwazi(repo_with("ulwazi"), live(uses=False), CATALOGUE)
    assert (result.uses, result.state, result.version) == (False, "pending", None)
    result = resolve_ulwazi(repo_with("furo", None), live(uses=False), CATALOGUE)
    assert (result.uses, result.state, result.version) == (False, "none", None)
    assert resolve_ulwazi(None, None, CATALOGUE).state == "none"


def test_ulwazi_falls_back_to_the_repository_when_the_site_is_unreachable():
    blocked = live(uses=False, ok=False, error="HTTP 403")
    built = dt.datetime(2026, 10, 20, tzinfo=dt.UTC)
    result = resolve_ulwazi(repo_with("ulwazi"), blocked, CATALOGUE, built_at=built)
    assert (result.uses, result.state) == (True, "repo")
    assert (result.version, result.precision) == ("1.0.2", "estimated")
    assert resolve_ulwazi(repo_with("furo"), blocked, CATALOGUE).uses is False
    pinned = resolve_ulwazi(None, None, CATALOGUE, pinned="1.0.0")
    assert (pinned.uses, pinned.version, pinned.precision) == (True, "1.0.0", "manual")


# ---------------------------------------------------------------------------
# Statistics and history
# ---------------------------------------------------------------------------


def record(
    slug: str,
    *,
    stack: str | None,
    ulwazi: bool = False,
    reason: str | None = None,
    state: str | None = None,
) -> dict[str, Any]:
    return {
        "slug": slug,
        "repo": {"url": f"https://github.com/canonical/{slug}"},
        "scope": {"reason": reason},
        "sphinx_stack": {
            "detected": stack is not None,
            "version": stack,
            "is_latest": stack == "3.0",
            "corrected": False,
        },
        "ulwazi": {
            "uses": ulwazi,
            "state": state or ("live" if ulwazi else "none"),
            "version": "1.0.3" if ulwazi else None,
        },
    }


def test_summary_counts():
    records = [
        record("a", stack="3.0", ulwazi=True),
        record("b", stack="3.0"),
        record("c", stack="2.0", ulwazi=True),
        record("d", stack="2.0", state="pending"),
        record("e", stack=None, reason="not_sphinx_stack"),
        record("f", stack=None, reason="not_sphinx_stack", ulwazi=True),
        record("g", stack="1.6", reason="archived"),
        record("h", stack=None, reason="error"),
    ]
    summary = summarize(records, latest_stack="3.0", latest_ulwazi="1.0.3", today=TODAY)
    assert summary["total"] == 8
    assert summary["sphinx_stack"] == 4
    assert summary["latest"] == 2
    assert (summary["ulwazi"], summary["ulwazi_percent"]) == (2, 50.0)
    assert summary["ulwazi_elsewhere"] == 1
    assert summary["pending_deploy"] == 1
    assert summary["out_of_scope"] == 4
    assert summary["out_of_scope_reasons"] == {
        "archived": 1,
        "error": 1,
        "not_sphinx_stack": 2,
    }
    assert summary["sphinx_stack_versions"] == {"3.0": 2, "2.0": 2}
    assert summary["errors"] == 1


def test_history_replaces_the_same_day_and_computes_deltas(tmp_path):
    path = tmp_path / "history.jsonl"
    base = {"total": 10, "sphinx_stack": 8, "latest": 2, "ulwazi": 1, "out_of_scope": 2}
    path.write_text(
        json.dumps({"date": "2026-11-18", **base})
        + "\n"
        + json.dumps({"date": "2026-11-26", **base})
        + "\n",
        encoding="utf-8",
    )
    summary = {"date": TODAY.isoformat(), **base, "ulwazi": 3, "total": 11}
    rows = update_history(path, summary)
    rows = update_history(path, {**summary, "ulwazi": 4})
    assert [r["date"] for r in rows] == ["2026-11-18", "2026-11-26", "2026-11-27"]
    assert rows[-1]["ulwazi"] == 4
    change = deltas({**summary, "ulwazi": 4}, rows, today=TODAY)
    assert (change["ulwazi"], change["total"]) == (
        3,
        1,
    )  # against 2026-11-18, a week ago or older
    assert deltas(summary, [], today=TODAY)["ulwazi"] is None


# ---------------------------------------------------------------------------
# The pipeline
# ---------------------------------------------------------------------------


def info(name: str, *, archived: bool = False) -> RepoInfo:
    return RepoInfo(
        owner="canonical",
        name=name,
        url=f"https://github.com/canonical/{name}",
        archived=archived,
        private=False,
        default_branch="main",
        head_oid=OID,
        head_date="2026-11-26T10:00:00+00:00",
    )


def project(
    slug: str, repo: str | None = None, *, host: str = "github.com"
) -> RtdProject:
    return RtdProject(
        slug=slug,
        name=slug,
        docs_url=f"https://documentation.ubuntu.com/{slug}/",
        repo_url=f"https://{host}/canonical/{repo or slug}",
        repo_host=host,
        repo_owner="canonical",
        repo_name=repo or slug,
    )


def build_services(tmp_path: Path, extra_config: str = "") -> pipeline.Services:
    config = load_config(
        write_config(
            tmp_path, extra_config + "\n[detection]\nlive_site_checks = false\n"
        )
    )
    repos: dict[tuple[str, str, str], dict[str, str]] = {
        ("canonical", "adopted", OID): {
            "docs/_dev/version": "2.0\n",
            "docs/conf.py": 'html_theme = "ulwazi"\n',
            "docs/requirements.txt": "ulwazi~=1.0\nsphinx-roles~=1.0\n",
        },
        ("canonical", "plain", OID): {
            "docs/_dev/version": "2.0\n",
            "docs/_dev/check_removed_urls.py": "x",
            "docs/conf.py": "html_theme = 'furo'\n",
        },
        ("canonical", "mkdocs", OID): {"mkdocs.yml": ""},
        ("canonical", "retired", OID): {"docs/_dev/version": "1.6\n"},
        ("canonical", "internal-notes", OID): {"docs/_dev/version": "1.6\n"},
        **UPSTREAM_FILES,
    }
    github = FakeGitHub(repos)
    github.visible = {
        ("canonical", "adopted"): info("adopted"),
        ("canonical", "plain"): info("plain"),
        ("canonical", "mkdocs"): info("mkdocs"),
        ("canonical", "retired"): info("retired", archived=True),
        ("canonical", "internal-notes"): info("internal-notes"),
        ("canonical", PRIVATE_NAME): None,
    }
    return pipeline.Services(
        config, github, Upstream(github, "canonical/sphinx-stack"), CATALOGUE, "3.0"
    )


def test_process_projects_applies_scope_rules(tmp_path):
    services = build_services(
        tmp_path, '[[exclude]]\nslug = "internal-*"\nreason = "internal"\n'
    )
    projects = [
        project("adopted"),
        project("plain"),
        project("mkdocs"),
        project("retired"),
        project("internal-notes"),
        project("launchpad-docs", host="launchpad.net"),
        project("hidden", PRIVATE_NAME),
    ]
    records = {
        r["slug"]: r
        for r in pipeline.process_projects(
            projects, services, previous={}, today=TODAY, live=False
        )
    }
    assert "hidden" not in records  # a private repository is dropped without a trace
    assert PRIVATE_NAME not in json.dumps(records)

    adopted = records["adopted"]
    assert adopted["scope"]["reason"] is None
    assert (
        adopted["sphinx_stack"]["version"],
        adopted["sphinx_stack"]["corrected"],
    ) == ("3.0", True)
    assert (
        adopted["ulwazi"]["state"] == "repo"
    )  # the live check is off, so the repository decides
    assert adopted["ulwazi"]["version"] == "1.0.3"
    assert adopted["repo"]["docs_path"] == "docs"
    assert adopted["activity"]["docs_last_commit_at"] == "2026-11-20T10:00:00+00:00"

    assert records["plain"]["sphinx_stack"]["version"] == "2.0"
    assert records["plain"]["ulwazi"]["version"] is None
    assert records["mkdocs"]["scope"]["reason"] == "not_sphinx_stack"
    assert records["retired"]["scope"]["reason"] == "archived"
    assert records["internal-notes"]["scope"]["reason"] == "opted_out"
    assert records["launchpad-docs"]["scope"]["reason"] == "unsupported_host"


def test_manual_mode_and_overrides(tmp_path):
    services = build_services(
        tmp_path,
        '[tracking]\nmode = "manual"\n[[include]]\nslug = "adopted"\n[[include]]\nslug = "plain"\n'
        '[[override]]\nslug = "plain"\nsphinx_stack = "3.0"\nulwazi = "1.0.2"\nnote = "pinned"\n',
    )
    records = {
        r["slug"]: r
        for r in pipeline.process_projects(
            [project("adopted"), project("plain"), project("mkdocs")],
            services,
            previous={},
            today=TODAY,
            live=False,
        )
    }
    assert records["mkdocs"]["scope"]["reason"] == "not_included"
    plain = records["plain"]
    assert (plain["sphinx_stack"]["version"], plain["ulwazi"]["version"]) == (
        "3.0",
        "1.0.2",
    )
    assert plain["manual"] == ["Sphinx Stack version", "Ulwazi version"]


def test_a_repository_error_is_recorded_not_raised(tmp_path):
    services = build_services(tmp_path)

    def fail(*_args: object) -> bytes | None:
        raise pipeline.GitHubError("HTTP 502 reading canonical/adopted")

    services.github.raw = fail  # type: ignore[method-assign]
    records = pipeline.process_projects(
        [project("adopted")], services, previous={}, today=TODAY, live=False
    )
    assert records[0]["scope"]["reason"] == "error"
    assert "502" in records[0]["scope"]["note"]


def test_run_writes_outputs_and_refuses_when_too_many_fail(tmp_path, monkeypatch):
    data = tmp_path / "data"
    write_json(
        data / "rtd-projects.json",
        {
            "schema_version": 1,
            "projects": [vars(project("adopted")), vars(project("plain"))],
        },
    )
    config = build_services(tmp_path).config

    def fake_catalogue(_cache: Cache, _package: str = "ulwazi") -> Catalogue:
        return CATALOGUE

    services = build_services(tmp_path)
    monkeypatch.setattr(Catalogue, "load", staticmethod(fake_catalogue))
    monkeypatch.setattr(pipeline, "GitHub", lambda _token, _cache: services.github)
    monkeypatch.setattr(pipeline, "Upstream", lambda *_args: services.upstream)

    payload = pipeline.run(
        config=config,
        data_dir=data,
        cache_dir=None,
        github_token=None,
        live=False,
        today=TODAY,
    )
    assert payload["summary"]["sphinx_stack"] == 2
    assert (data / "adoption.json").is_file()
    assert (data / "history.jsonl").read_text().count("\n") == 1

    def fail(*_args: object) -> bytes | None:
        raise pipeline.GitHubError("boom")

    services.github.raw = fail  # type: ignore[method-assign]
    before = (data / "adoption.json").read_text()
    with pytest.raises(pipeline.PublishRefusedError):
        pipeline.run(
            config=config,
            data_dir=data,
            cache_dir=None,
            github_token=None,
            live=False,
            today=TODAY,
        )
    assert (data / "adoption.json").read_text() == before  # the previous data is kept
    assert (data / "adoption.rejected.json").is_file()


def test_run_needs_detection_output_first(tmp_path):
    with pytest.raises(DataError, match="does not exist"):
        pipeline.run(
            config=build_services(tmp_path).config,
            data_dir=tmp_path / "empty",
            cache_dir=None,
            github_token=None,
        )
