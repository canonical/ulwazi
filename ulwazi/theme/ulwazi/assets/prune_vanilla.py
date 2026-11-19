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

"""Remove Vanilla selectors for classes that the theme never uses.

A selector is dropped only if it requires a class in a Vanilla namespace
(``p-``, ``u-``, ``l-``, ``is-``, ``has-``, ``row``, ``col-*``, ``grid-*``)
that doesn't appear as a whole word in the theme sources. All other selectors
are kept and rules are never reordered. ``@layer`` blocks are copied
unchanged, because dropping one could change the layer order. Classes built
at run time count as
used when their prefix (ending in ``-`` or ``_``) appears; to keep any other
class, add it to ``KEEP``.

Also writes ``OUTPUT.css.removed-classes.json``, listing the Vanilla classes
that no remaining selector mentions.

Uses only the Python standard library.

Usage: python prune_vanilla.py THEME_SOURCE_DIR INPUT.css OUTPUT.css
"""

from __future__ import annotations

import hashlib
import json
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
# A prefix such as ``p-notification--`` covers names built at run time.
WORD = re.compile(
    r"(?<![\w-])((?:p|u|l|is|has)-[\w-]*|(?:row|col|grid)(?:-[\w-]*)?)(?![\w])"
)

SOURCE_SUFFIXES = {".py", ".html", ".js", ".scss", ".css", ".toml", ".json", ".txt"}

# At-rules whose block contains rules (pruned recursively). Not ``layer``:
# a layer's first block fixes its cascade order, so it must never be dropped.
GROUPING_AT_RULES = {"media", "supports", "container", "document"}

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


def _is_unused(name: str, words: set[str], prefixes: set[str]) -> bool:
    """Whether ``name`` is a Vanilla class that the theme never uses."""
    return (
        NAMESPACE.match(name) is not None
        and name not in words
        and not any(name.startswith(prefix) for prefix in prefixes)
    )


def keep_selector(selector: str, words: set[str], prefixes: set[str]) -> bool:
    """Whether ``selector`` can match an element produced by the theme."""
    return not any(
        _is_unused(name, words, prefixes) for name in _required_classes(selector)
    )


def prune_and_report(
    css: str, words: set[str], prefixes: set[str]
) -> tuple[str, list[str]]:
    """Return the pruned CSS and the sorted removed Vanilla classes.

    A class counts as removed only if a dropped selector required it and no
    kept selector mentions it at all, even inside ``:is()`` or ``:has()``.
    """
    dropped: set[str] = set()
    kept: set[str] = set()
    pruned = _prune(css, words, prefixes, dropped, kept)
    return pruned, sorted(dropped - kept)


def prune(css: str, words: set[str], prefixes: set[str]) -> str:
    """Return ``css`` without the selectors (and rules) the theme can't use."""
    return prune_and_report(css, words, prefixes)[0]


def removed_classes(css: str, words: set[str], prefixes: set[str]) -> list[str]:
    """Return the Vanilla classes that pruning ``css`` leaves unstyled."""
    return prune_and_report(css, words, prefixes)[1]


def _prune(
    css: str, words: set[str], prefixes: set[str], dropped: set[str], kept: set[str]
) -> str:
    """Prune ``css``, collecting classes of dropped and kept selectors."""
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
                inner = _prune(css[stop + 1 : end], words, prefixes, dropped, kept)
                if inner:
                    out.append(css[i:stop].strip() + "{" + inner + "}")
            else:
                out.append(css[i : end + 1])
                kept.update(CLASS.findall(css[stop + 1 : end]))  # still styled
            i = end + 1
            continue
        stop = _find(css, i, "{")
        if stop >= len(css):
            raise ValueError(f"unexpected trailing CSS: {css[i : i + 60]!r}")
        end = _block_end(css, stop)
        selectors = _kept_selectors(css[i:stop], words, prefixes, dropped, kept)
        if selectors:
            out.append(",".join(selectors) + css[stop : end + 1])
        i = end + 1
    return "".join(out)


def _kept_selectors(
    prelude: str, words: set[str], prefixes: set[str], dropped: set[str], kept: set[str]
) -> list[str]:
    """Return the usable selectors of ``prelude``, collecting their classes."""
    selectors: list[str] = []
    for selector in split_selectors(prelude):
        if keep_selector(selector, words, prefixes):
            selectors.append(selector)
            kept.update(CLASS.findall(selector))
        else:
            dropped.update(
                name
                for name in _required_classes(selector)
                if _is_unused(name, words, prefixes)
            )
    return selectors


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
    body, classes = prune_and_report(css, words, prefixes)
    pruned = stamp(words, prefixes) + body
    target.write_bytes(bom + pruned.encode("utf-8") + b"\n")
    manifest = {
        "classes": classes,
        "vocabulary": vocabulary_digest(words, prefixes),
    }
    # Named with a "vanilla-main.css" prefix so vocabulary() skips it on
    # the next run (it lists every removed class as a bare word).
    target.with_name(target.name + ".removed-classes.json").write_text(
        json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        f"Pruned unused Vanilla selectors: {len(raw):,} -> "
        f"{len(bom) + len(pruned.encode('utf-8')) + 1:,} bytes "
        f"({len(manifest['classes'])} removed classes listed for build-time checks)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
