#!/usr/bin/env python3
"""Lint wikilinks under wiki/.

Walks every *.md file, finds every [[slug]] and [[slug|alias]] reference,
skipping HTML comments, fenced code blocks, and inline code spans (so template
content inside wiki/index.md and wiki/log.md's HTML conventions doesn't fire
false positives).

Classifies each wikilink target into one of three DISJOINT categories:

    resolved      target page exists somewhere under wiki/
    missing-page  target doesn't exist AND at least one occurrence sits inside
                  a source-summary page's "## Entities" or "## Concepts" H2
                  section. Reported ONCE per target with all referring locations.
    broken        target doesn't exist AND no occurrence is in a source-summary
                  Entities/Concepts section. Reported per-occurrence.

Per-target dedup: a target classified as missing-page does not also fire as
broken for its other occurrences. The single action ("create the page")
resolves all of them.

Usage:
    python3 scripts/lint-wikilinks.py [PATH]
                                      [--check {broken,missing-pages,all}]
                                      [--format {text,json}]

Defaults: PATH=wiki/, check=all, format=text.
Exit code: non-zero when there are findings under the requested checks.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# A wikilink target is kebab-case slug; an optional |alias may follow.
WIKILINK_RE = re.compile(r"\[\[([a-z0-9-]+)(?:\|[^\]]*)?\]\]")
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
FENCED_CODE_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
H2_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


def strip_skipped_regions(text: str) -> str:
    """Blank out HTML comments, fenced code blocks, and inline code spans.

    Multi-line regions are replaced with the same number of newlines so line
    numbers in the residual text still align with the original.
    """

    def blank_keep_newlines(m: re.Match[str]) -> str:
        return "\n" * m.group(0).count("\n")

    text = HTML_COMMENT_RE.sub(blank_keep_newlines, text)
    text = FENCED_CODE_RE.sub(blank_keep_newlines, text)
    text = INLINE_CODE_RE.sub(lambda m: " " * len(m.group(0)), text)
    return text


def find_wikilinks(text: str):
    """Yield (line_number, target, match_text) for each wikilink."""
    for line_no, line in enumerate(text.splitlines(), start=1):
        for m in WIKILINK_RE.finditer(line):
            yield line_no, m.group(1), m.group(0)


def section_for_line(text: str, target_line: int) -> str | None:
    """Return the H2 section title that target_line falls under, or None."""
    current: str | None = None
    for line_no, line in enumerate(text.splitlines(), start=1):
        m = H2_RE.match(line)
        if m:
            current = m.group(1).strip()
        if line_no == target_line:
            return current
    return current  # target_line past EOF — return whatever the last section was


def all_page_slugs(wiki_root: Path) -> set[str]:
    """Set of basename-without-extension for every *.md under wiki_root."""
    return {p.stem for p in wiki_root.rglob("*.md")}


def lint(wiki_root: Path) -> dict:
    pages = all_page_slugs(wiki_root)

    # target -> list of occurrence dicts
    occurrences: dict[str, list[dict]] = {}

    for md_path in sorted(wiki_root.rglob("*.md")):
        raw = md_path.read_text(encoding="utf-8")
        stripped = strip_skipped_regions(raw)
        is_source_summary = md_path.parent.name == "sources"

        for line_no, target, match_text in find_wikilinks(stripped):
            in_summary_section = False
            if is_source_summary:
                section = section_for_line(stripped, line_no)
                if section in ("Entities", "Concepts"):
                    in_summary_section = True

            occurrences.setdefault(target, []).append(
                {
                    "file": str(md_path),
                    "line": line_no,
                    "match": match_text,
                    "in_summary_section": in_summary_section,
                }
            )

    findings: dict[str, list[dict]] = {
        "resolved": [],
        "broken": [],
        "missing-page": [],
    }

    for target, occs in occurrences.items():
        if target in pages:
            for occ in occs:
                findings["resolved"].append(
                    {"target": target, "file": occ["file"], "line": occ["line"]}
                )
            continue

        if any(o["in_summary_section"] for o in occs):
            findings["missing-page"].append(
                {
                    "target": target,
                    "referenced_from": [
                        {"file": o["file"], "line": o["line"]} for o in occs
                    ],
                }
            )
        else:
            for occ in occs:
                findings["broken"].append(
                    {
                        "target": target,
                        "file": occ["file"],
                        "line": occ["line"],
                        "match": occ["match"],
                    }
                )

    return findings


def format_text(findings: dict, checks: set[str]) -> str:
    lines: list[str] = []

    if "broken" in checks:
        lines.append("# Broken wikilinks")
        if not findings["broken"]:
            lines.append("(none)")
        else:
            for f in findings["broken"]:
                lines.append(f"- {f['file']}:{f['line']}  {f['match']}")
        lines.append("")

    if "missing-pages" in checks:
        lines.append("# Missing pages")
        if not findings["missing-page"]:
            lines.append("(none)")
        else:
            for f in findings["missing-page"]:
                lines.append(f"- [[{f['target']}]] — no wiki page exists for this slug")
                lines.append("  Referenced from:")
                for ref in f["referenced_from"]:
                    lines.append(f"    - {ref['file']}:{ref['line']}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    p = argparse.ArgumentParser(description="Lint wikilinks under a wiki directory.")
    p.add_argument(
        "path",
        nargs="?",
        default="wiki",
        type=Path,
        help="Wiki root directory (default: wiki)",
    )
    p.add_argument(
        "--check",
        choices=["broken", "missing-pages", "all"],
        default="all",
        help="Which check(s) to run (default: all)",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    args = p.parse_args()

    if not args.path.is_dir():
        print(f"error: {args.path} is not a directory", file=sys.stderr)
        return 2

    findings = lint(args.path)

    if args.check == "all":
        active = {"broken", "missing-pages"}
    else:
        active = {args.check}

    if args.format == "json":
        out: dict[str, list] = {}
        if "broken" in active:
            out["broken"] = findings["broken"]
        if "missing-pages" in active:
            out["missing-page"] = findings["missing-page"]
        print(json.dumps(out, indent=2))
    else:
        print(format_text(findings, active), end="")

    relevant_count = 0
    if "broken" in active:
        relevant_count += len(findings["broken"])
    if "missing-pages" in active:
        relevant_count += len(findings["missing-page"])
    return 0 if relevant_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
