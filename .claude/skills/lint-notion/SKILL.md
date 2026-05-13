---
description: Cloud-freshness lint for Notion sources — content drift, title drift, deletion, inaccessibility, and index-page link rot. Pass a Notion URL/ID to lint just one page.
argument-hint: "" | <notion-url-or-id> | --check <category> | <url> --check <category>
---

Run the **Lint-notion workflow** against:

`$ARGUMENTS`

This SKILL.md is the canonical source of truth — the inventory vs. single-page modes, the drift modes table, the default checks (content / title / deleted / inaccessible / index-page link rot), the opt-in checks (`urls`, `index`), and the "never apply fixes automatically" rule all live below. The report format is in the bundled file `sample-report.md`. Companion to the offline `.claude/skills/lint/` skill.

**Argument interpretation:**

- Empty `$ARGUMENTS` → **inventory mode** with default checks. Enumerate every `raw/info/*.info.md` with `source-type: notion`; check each against Notion via `mcp__claude_ai_Notion__notion-fetch`; then run the index-page link-rot check once on the Notion index page.
- `$ARGUMENTS` is a Notion URL or page ID (no `--check`) → **single-page mode** with default checks (content / title / deleted / inaccessible). Skip the index-page link-rot check unless `--check index` is also passed. If the resolved page ID isn't present in any sidecar, stop and tell the user the page hasn't been ingested.
- `$ARGUMENTS` contains `--check <category>` → run only that category. Accepted values: `content | title | deleted | inaccessible | urls | index | all`.
- `$ARGUMENTS` combines a URL/ID and `--check <category>` → single-page mode, only the named category.
- Any other shape → stop and ask the user what they meant. Do not guess.

`/lint-notion` **never modifies files**. Like `/lint`, it surfaces a report. Fixes are user-initiated: re-run `/ingest-notion <url>` to refresh a stale or renamed page (this overwrites the cached copy in place per the slug-frozen rule); decide manually how to handle deleted / inaccessible pages.

## Two modes

- **Inventory mode** (no argument) — enumerate every sidecar under `raw/info/` with `source-type: notion` and check each against Notion.
- **Single-page mode** (`<notion-url-or-id>`) — resolve the argument to a page ID, find its sidecar via `grep -l "notion-page-id: <uuid>" raw/info/*.info.md`, and check just that page. The escape hatch for "I edited one Notion doc, don't crawl my whole inventory."

  If the page ID isn't found in any sidecar, stop and tell the user the page hasn't been ingested (suggest `/ingest-notion <url>` first).

**Performance note.** Every Notion-sourced page is one Notion MCP `notion-fetch` call (metadata-only if the MCP supports it; full fetch otherwise). Inventory mode costs N round-trips at N ingested pages — non-trivial at scale. Single-page mode is one call. `/lint-notion` never runs on a schedule; it is purely user-invoked.

## Drift modes — what's checked

A locally-cached Notion source goes stale the moment the page is edited in Notion. The local copy is a snapshot, not a live mirror.

| # | Drift mode | Detect via | Severity | Default? |
|---|---|---|---|---|
| 1 | **Content drift** — page body edited in Notion | current `last_edited_time` > sidecar's `notion-last-edited` | High — wiki claims cite a stale snapshot | **Yes** |
| 2 | **Title drift** — page renamed | current Notion title ≠ sidecar `title` | Low — informational; slug is frozen so no filename changes | **Yes** (informational) |
| 3 | **Deletion / archival** — page gone | fetch returns "not found" or `archived: true` | High — citation dangles | **Yes** |
| 4 | **Permissions revoked** — integration lost access | fetch returns 401/403 | Medium — distinct from deletion; may resolve when the user re-grants access | **Yes** (separate category from deleted) |
| 5 | **URL change** — page moved, slug regenerated | current URL ≠ sidecar `url`, but the page ID still resolves | Low — cosmetic; the stable ID means fetches still work | Opt-in (`--check urls`) |
| 6 | **Index page drift** — registry page hand-edited | parse the index page; compare its bullet list against expected entries (one per Notion-sourced sidecar) | Low — append-only design tolerates this | Opt-in (`--check index`) |
| 7 | **Wiki-side link rot from index page** — an entry's `→ wiki/sources/<slug>.md` no longer exists locally | for each index entry, check the referenced wiki file | Low | **Yes** (cheap, runs once on the index page itself) |

**Out of scope** (future work, not in v1):

- **DB-properties drift** — Notion pages can carry database properties (Status, Tags, Date) that change independently of the body. Would require snapshotting properties in the sidecar at ingest, which we don't do.
- **Embedded sub-page / synced-block drift** — Notion pages can embed child databases, synced blocks, linked pages. Detecting drift in these requires walking the full block tree per page; too expensive.

## Argument syntax

```
/lint-notion                            # inventory mode, default checks (1-4, 7)
/lint-notion <notion-url-or-id>         # single-page mode, default checks 1-4
/lint-notion --check <category>         # inventory mode, only the named category
/lint-notion <url> --check <category>   # single-page, only the named category
```

`--check <category>` accepts: `content | title | deleted | inaccessible | urls | index | all`. Default (no flag) runs `content`, `title`, `deleted`, `inaccessible`, and in inventory mode also `index` (the wiki-side link rot check on entries of the index page). `urls` and the full `index` integrity check are opt-in.

## Default checks (what runs without flags)

For each ingested Notion source (inventory mode) or the single specified page (single-page mode):

1. **Fetch metadata via `mcp__claude_ai_Notion__notion-fetch`.** Capture: current title, current URL, `last_edited_time`, `archived` flag (if exposed), and any error response (404, 401/403).

2. **Content drift (#1):** if `last_edited_time` > sidecar's `notion-last-edited`, flag.

3. **Title drift (#2):** if current Notion title ≠ sidecar `title`, flag as **informational** — slug does not change; the user can re-ingest to refresh the title metadata if they want.

4. **Deletion / archival (#3):** if the fetch returned not-found or `archived: true`, flag.

5. **Permissions revoked (#4):** if the fetch returned 401/403, flag (separate category from #3 — different recovery path).

In inventory mode, after the per-page loop, also run:

6. **Index-page link rot (#7):** read the Notion index page; parse the `→ wiki/sources/<slug>.md` references; for each, check the file exists locally. Flag any that don't.

## Opt-in checks (only with `--check`)

- **`--check urls`:** for each page where the fetch succeeded, compare current Notion URL to sidecar `url`. Flag drift. Cosmetic only — the page ID is stable.
- **`--check index`:** parse the Notion index page; compare its bullet entries to the expected set (one bullet per Notion-sourced sidecar). Flag missing or extra entries. This is the integrity check for the index page itself, separate from #7.

## Report format

A single markdown report, one H2 per check category (even when empty — empty sections confirm the check ran). For the exact expected shape (with worked findings in each category), see `sample-report.md` next to this SKILL.md.

## After producing the report

1. **Do not apply fixes automatically.** Surface the report; wait for the user.
2. Resolutions are user-initiated: re-run `/ingest-notion <url>` for stale content / title; decide manually how to handle deleted pages (keep as historical citation, strip, or wait).
3. **Append a log entry** to `wiki/log.md` (canonical conventions in its HTML comment):

   ```markdown
   ## [YYYY-MM-DD] lint-notion | <inventory | <slug>>

   - Checked: <N pages>
   - Findings: <count by category, e.g. "2 content-drift, 1 title-drift (informational), 0 deleted, 0 inaccessible, 0 index-rot">
   - Applied: <count of fixes the user approved (typically 0 — fixes go through /ingest-notion)>
   - Notable: <one line on anything unusual>
   ```
