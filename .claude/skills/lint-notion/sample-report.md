# Sample lint-notion report

Reference shape for the report produced by `.claude/skills/lint-notion/SKILL.md`. One H2 per check category, even when empty — empty sections confirm the check ran. The mode line at the top distinguishes inventory mode from single-page mode.

```markdown
# Notion lint report — 2026-05-13

Mode: inventory (N pages checked) | single-page (<slug>)

## Content drift

- `raw/info/foo.info.md`
  - Notion `last_edited_time` 2026-05-13T09:14:00Z is newer than sidecar `notion-last-edited` 2026-05-11T18:00:00Z.
  - **Suggested fix:** `/ingest-notion <url>` to overwrite the cached copy and refresh downstream wiki pages.

## Title drift (informational)

- `raw/info/foo.info.md`
  - Sidecar `title:` "Initial Draft" → current Notion title "Initial Draft (revised)".
  - **Suggested fix:** Re-run `/ingest-notion <url>` to refresh the metadata. The slug and filenames do not change.

## Deleted or archived

(none)

## Permissions revoked

(none)

## Index-page link rot

- Index entry references `wiki/sources/old-doc.md` — no such file in the wiki.
  - **Suggested fix:** Either restore the wiki page, or manually remove the stale entry from the Notion index page.
```
