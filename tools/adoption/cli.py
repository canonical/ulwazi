"""Command-line interface: ``python -m tools.adoption <command>``."""

from __future__ import annotations

import argparse
import functools
import http.server
import logging
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from tools.adoption.cache import Cache
from tools.adoption.config import Config, ConfigError, load_config
from tools.adoption.detect import RTD_PROJECTS_FILE, write_rtd_projects
from tools.adoption.detect.rtd_api import RtdClient, RtdError, detect_from_api
from tools.adoption.detect.rtd_file import detect_from_file
from tools.adoption.http import FetchError
from tools.adoption.models import DataError
from tools.adoption.process import pipeline
from tools.adoption.process.github import GitHubError, find_token
from tools.adoption.render import RenderError, render_site

HERE = Path(__file__).parent
LOG = logging.getLogger("adoption")
EXIT_FAILURE = 1
EXIT_REFUSED = 2


def build_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="python -m tools.adoption",
        description="Track Ulwazi and Sphinx Stack adoption in Read the Docs projects.",
    )
    parser.add_argument("--config", type=Path, default=None, help="path to config.toml")
    parser.add_argument("--data-dir", type=Path, default=HERE / "data")
    parser.add_argument("--cache-dir", type=Path, default=HERE / ".cache")
    parser.add_argument("--build-dir", type=Path, default=HERE / "_build")
    parser.add_argument("-v", "--verbose", action="store_true")
    commands = parser.add_subparsers(dest="command", required=True)

    detect = commands.add_parser("detect", help="layer 1: list public RTD projects")
    _add_detect_options(detect)

    process = commands.add_parser("process", help="layer 2: detect versions")
    _add_process_options(process)

    render = commands.add_parser("render", help="layer 3: build the dashboard")
    _add_render_options(render)

    everything = commands.add_parser("all", help="run all three layers")
    _add_detect_options(everything)
    _add_process_options(everything)
    _add_render_options(everything)

    serve = commands.add_parser("serve", help="serve the built dashboard locally")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8001)
    return parser


def _add_detect_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--file", type=Path, help="import projects from a CSV/JSON export"
    )
    parser.add_argument(
        "--assume-public",
        action="store_true",
        help="treat rows without privacy_level as public (file import)",
    )
    parser.add_argument("--no-builds", action="store_true", help="skip RTD build dates")
    parser.add_argument("--limit", type=int, help="stop after this many projects")


def _add_process_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--only", nargs="+", metavar="SLUG", help="process only these")
    parser.add_argument("--no-live", action="store_true", help="skip live-site checks")


def _add_render_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--input", type=Path, help="adoption.json to render")
    parser.add_argument("--no-css", action="store_true", help="skip compiling the SCSS")


def _detect(args: argparse.Namespace, config: Config) -> None:
    output = args.data_dir / RTD_PROJECTS_FILE
    if args.file:
        projects = detect_from_file(
            args.file,
            base_url=config.rtd_base_url,
            assume_public=args.assume_public,
            limit=args.limit,
        )
        source = "file"
    else:
        token = os.environ.get("RTD_TOKEN")
        if not token:
            raise RtdError(
                "Set RTD_TOKEN to a Read the Docs API token, or use --file with an export"
            )
        client = RtdClient(config.rtd_base_url, token, Cache(args.cache_dir))
        projects = detect_from_api(
            client,
            config.rtd_organization,
            include_builds=not args.no_builds,
            assume_public=args.assume_public,
            limit=args.limit,
        )
        source = "api"
    if not projects:
        raise DataError("No public projects were found")
    write_rtd_projects(output, projects, source=source)
    LOG.info("Wrote %s (%d projects)", output, len(projects))


def _process(args: argparse.Namespace, config: Config) -> None:
    pipeline.run(
        config=config,
        data_dir=args.data_dir,
        cache_dir=args.cache_dir,
        github_token=find_token(),
        only=args.only,
        limit=getattr(args, "limit", None),
        live=not args.no_live,
    )


def _render(args: argparse.Namespace) -> None:
    render_site(
        args.input or args.data_dir / pipeline.ADOPTION_FILE,
        args.data_dir / "history.jsonl",
        args.build_dir,
        compile_css=not args.no_css,
    )


def _serve(args: argparse.Namespace) -> None:
    if not (args.build_dir / "index.html").is_file():
        raise RenderError(f"{args.build_dir}/index.html is missing; run 'render' first")
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=str(args.build_dir)
    )
    with http.server.ThreadingHTTPServer((args.host, args.port), handler) as server:
        LOG.info("Serving http://%s:%d (Ctrl+C to stop)", args.host, args.port)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            LOG.info("Stopped")


def main(argv: Sequence[str] | None = None) -> int:
    """Run the tool and return the process exit code."""
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
        stream=sys.stderr,
    )
    try:
        if args.command == "serve":
            _serve(args)
            return 0
        config = load_config(args.config) if args.command != "render" else None
        if config is not None and args.command in {"detect", "all"}:
            _detect(args, config)
        if config is not None and args.command in {"process", "all"}:
            _process(args, config)
        if args.command in {"render", "all"}:
            _render(args)
    except pipeline.PublishRefusedError as error:
        LOG.error("%s", error)  # noqa: TRY400 - a message, not a traceback
        return EXIT_REFUSED
    except (
        ConfigError,
        DataError,
        RtdError,
        GitHubError,
        FetchError,
        RenderError,
    ) as error:
        LOG.error("%s", error)  # noqa: TRY400 - a message, not a traceback
        return EXIT_FAILURE
    return 0
