#!/usr/bin/env python3
# This file is part of Ulwazi.
#
# Copyright 2026 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3, as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranties of MERCHANTABILITY, SATISFACTORY
# QUALITY, or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
# License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

"""Remove Vanilla selectors for classes that Ulwazi never uses.

Ulwazi renders all of Vanilla (``@include vanilla`` in ``main.scss``), but
its templates, scripts and HTML hooks use only a fraction of Vanilla's
classes. ``make vanilla-main`` runs this script on the compressed Sass output
to keep the shipped stylesheet small: Read the Docs truncates large static
files.

A selector is dropped only if it requires a class in one of Vanilla's own
namespaces (``p-``, ``u-``, ``l-``, ``is-``, ``has-`` and the grid classes
``row``, ``col-*`` and ``grid-*``) that doesn't occur anywhere in the theme
sources (``ulwazi/``). Element selectors and selectors for any other class
are kept, and rules are never reordered or rewritten, so the cascade of the
remaining rules is unchanged. Classes inside ``:not()``, ``:is()``,
``:where()`` and ``:has()`` and inside attribute selectors are not treated
as required, so those selectors are kept.

A class is "used" if it occurs as a whole word in any theme source file.
Class names built at run time from a prefix (for example
``f"p-notification--{kind}"``) count as used when the prefix itself
(``p-notification--``) occurs, as a word ending in ``-`` or ``_``. Vanilla
classes that only appear in a project's own page content (raw HTML) aren't
covered. To keep one, add it to KEEP below.

Uses only the Python standard library, so it runs before any project
dependencies are installed.

Usage: python prune_vanilla.py THEME_SOURCE_DIR INPUT.css OUTPUT.css
"""

from __future__ import annotations

import hashlib
import re
import sys
from collections.abc import Iterable, Iterator
from pathlib import Path

# Classes to keep even though no theme source mentions them.
KEEP: frozenset[str] = frozenset()

# Vanilla's class namespaces; classes outside them are never pruned.
NAMESPACE_ROOTS = ("p", "u", "l", "is", "has", "row", "col", "grid")
NAMESPACE = re.compile(r"^(?:(?:p|u|l|is|has)-|row(?:$|-)|col(?:$|-)|grid-)")

# Candidate class names (or prefixes ending in "-" or "_") in theme sources.
WORD = re.compile(
    r"(?<![\w-])((?:p|u|l|is|has)-[\w-]*|(?:row|col|grid)(?:-[\w-]*)?)(?![\w])"
)

SOURCE_SUFFIXES = {".py", ".html", ".js", ".scss", ".css", ".toml", ".json", ".txt"}

# At-rules whose block contains rules (pruned recursively).
GROUPING_AT_RULES = {"media", "supports", "container", "layer", "document"}

# Pseudo-classes whose arguments are never treated as required.
LOGICAL_PSEUDO = re.compile(r":(?:not|is|where|has|matches|-webkit-any|-moz-any)\(")
CLASS = re.compile(r"\.(-?[A-Za-z_][\w-]*)")


def vocabulary(theme: Path, outputs: Iterable[Path] = ()) -> tuple[set[str], set[str]]:
    """Return the class names and class-name prefixes used by the theme.

    This script itself is skipped: its documentation names the namespaces
    (as prefixes), which would otherwise keep every Vanilla class.
    """
    skip = {path.resolve() for path in outputs}
    words: set[str] = set()
    prefixes: set[str] = set()
    for path in sorted(theme.rglob("*")):
        if (
            not path.is_file()
            or path.suffix not in SOURCE_SUFFIXES
            or "__pycache__" in path.parts
            or path.resolve() in skip
            or path.name == Path(__file__).name
            or path.name.startswith("vanilla-main.css")
        ):
            continue
        for match in WORD.finditer(path.read_text(encoding="utf-8", errors="replace")):
            token = match.group(1)
            (prefixes if token.endswith(("-", "_")) else words).add(token)
    return words | set(KEEP), prefixes


STAMP = re.compile(
    r"/\*! ulwazi: Vanilla pruned for class vocabulary ([0-9a-f]{16}) \*/"
)


def vocabulary_digest(words: set[str], prefixes: set[str]) -> str:
    """Short digest of a vocabulary, stamped into the CSS to detect staleness."""
    text = "\n".join(sorted(words)) + "\n--\n" + "\n".join(sorted(prefixes))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def stamp(words: set[str], prefixes: set[str]) -> str:
    """Return the comment that records which vocabulary the CSS was pruned for."""
    digest = vocabulary_digest(words, prefixes)
    return f"/*! ulwazi: Vanilla pruned for class vocabulary {digest} */"


def _skip_string(css: str, i: int) -> int:
    """Return the index just past the string literal starting at ``css[i]``."""
    quote = css[i]
    i += 1
    while i < len(css) and css[i] != quote:
        i += 2 if css[i] == "\\" else 1
    return i + 1


def _skip_comment(css: str, i: int) -> int:
    end = css.find("*/", i + 2)
    return len(css) if end == -1 else end + 2


def _find(css: str, i: int, stops: str) -> int:
    """Find the next top-level character in ``stops``, skipping nested parts."""
    depth = 0
    while i < len(css):
        ch = css[i]
        if ch in "\"'":
            i = _skip_string(css, i)
            continue
        if css.startswith("/*", i):
            i = _skip_comment(css, i)
            continue
        if ch == "\\":
            i += 2
            continue
        if depth == 0 and ch in stops:
            return i
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        i += 1
    return len(css)


def _block_end(css: str, i: int) -> int:
    """Given ``css[i] == "{"``, return the index of the matching ``}``."""
    depth = 0
    while i < len(css):
        ch = css[i]
        if ch in "\"'":
            i = _skip_string(css, i)
            continue
        if css.startswith("/*", i):
            i = _skip_comment(css, i)
            continue
        if ch == "\\":
            i += 2
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError("unbalanced braces in CSS")


def split_selectors(prelude: str) -> list[str]:
    """Split a selector list on top-level commas."""
    parts: list[str] = []
    start = 0
    while True:
        end = _find(prelude, start, ",")
        parts.append(prelude[start:end].strip())
        if end >= len(prelude):
            return [part for part in parts if part]
        start = end + 1


def _required_classes(selector: str) -> Iterator[str]:
    """Yield classes an element must have for ``selector`` to match."""
    out: list[str] = []
    i = 0
    while i < len(selector):
        ch = selector[i]
        if ch in "\"'":
            i = _skip_string(selector, i)
            continue
        if ch == "[":
            i = _find(selector, i + 1, "]") + 1
            continue
        match = LOGICAL_PSEUDO.match(selector, i)
        if match:
            i = _find(selector, match.end(), ")") + 1
            continue
        out.append(ch)
        i += 1
    yield from CLASS.findall("".join(out))


def keep_selector(selector: str, words: set[str], prefixes: set[str]) -> bool:
    """Whether ``selector`` can match an element produced by the theme."""
    for name in _required_classes(selector):
        if (
            NAMESPACE.match(name)
            and name not in words
            and not any(name.startswith(prefix) for prefix in prefixes)
        ):
            return False
    return True


def prune(css: str, words: set[str], prefixes: set[str]) -> str:
    """Return ``css`` without the selectors (and rules) the theme can't use."""
    out: list[str] = []
    i = 0
    while i < len(css):
        if css[i].isspace():
            i += 1
            continue
        if css.startswith("/*", i):
            end = _skip_comment(css, i)
            if (
                css.startswith("/*!", i) or css.startswith("/*#", i)
            ) and not STAMP.fullmatch(css[i:end]):
                out.append(css[i:end])  # preserved and source-map comments
            i = end
            continue
        if css[i] == "@":
            stop = _find(css, i, "{;")
            if stop >= len(css) or css[stop] == ";":
                out.append(css[i : stop + 1])
                i = stop + 1
                continue
            end = _block_end(css, stop)
            name = re.match(r"@([\w-]+)", css[i:stop])
            if name and name.group(1).lower() in GROUPING_AT_RULES:
                inner = prune(css[stop + 1 : end], words, prefixes)
                if inner:
                    out.append(css[i:stop].strip() + "{" + inner + "}")
            else:
                out.append(css[i : end + 1])
            i = end + 1
            continue
        stop = _find(css, i, "{")
        if stop >= len(css):
            raise ValueError(f"unexpected trailing CSS: {css[i : i + 60]!r}")
        end = _block_end(css, stop)
        selectors = [
            selector
            for selector in split_selectors(css[i:stop])
            if keep_selector(selector, words, prefixes)
        ]
        if selectors:
            out.append(",".join(selectors) + css[stop : end + 1])
        i = end + 1
    return "".join(out)


def main(argv: list[str]) -> int:
    """Prune the compiled CSS ``argv[1]`` into ``argv[2]`` for theme ``argv[0]``."""
    try:
        theme, source, target = (Path(arg) for arg in argv)
    except ValueError:
        print((__doc__ or "").strip().splitlines()[-1], file=sys.stderr)
        return 2
    raw = source.read_bytes()
    bom = b"\xef\xbb\xbf" if raw.startswith(b"\xef\xbb\xbf") else b""
    css = raw[len(bom) :].decode("utf-8")
    words, prefixes = vocabulary(theme, outputs=[source, target])
    pruned = stamp(words, prefixes) + prune(css, words, prefixes)
    target.write_bytes(bom + pruned.encode("utf-8") + b"\n")
    print(
        f"Pruned unused Vanilla selectors: {len(raw):,} -> "
        f"{len(bom) + len(pruned.encode('utf-8')) + 1:,} bytes"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
