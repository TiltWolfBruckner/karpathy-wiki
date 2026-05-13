---
description: Cloud-freshness lint for Notion sources — content drift, title drift, deletion, inaccessibility, and index-page link rot. Pass a Notion URL/ID to lint just one page.
argument-hint: "" | <notion-url-or-id> | --check <category> | <url> --check <category>
---

Run the **Lint-notion workflow** defined in `CLAUDE.md > Lint-notion workflow`.

Argument: `$ARGUMENTS`

`CLAUDE.md > Lint-notion workflow` is the canonical source of truth — the inventory vs. single-page modes, the drift modes table, the default checks (content / title / deleted / inaccessible / index-page link rot), the opt-in checks (`urls`, `index`), the report format, and the "never apply fixes automatically" rule all live there. Follow it exactly; do not improvise. If `CLAUDE.md` is unavailable, stop and tell the user.

**Argument interpretation:**

- Empty `$ARGUMENTS` → **inventory mode** with default checks. Enumerate every `raw/info/*.info.md` with `source-type: notion`; check each against Notion via `mcp__claude_ai_Notion__notion-fetch`; then run the index-page link-rot check once on the Notion index page.
- `$ARGUMENTS` is a Notion URL or page ID (no `--check`) → **single-page mode** with default checks (content / title / deleted / inaccessible). Skip the index-page link-rot check unless `--check index` is also passed. If the resolved page ID isn't present in any sidecar, stop and tell the user the page hasn't been ingested.
- `$ARGUMENTS` contains `--check <category>` → run only that category. Accepted values: `content | title | deleted | inaccessible | urls | index | all`.
- `$ARGUMENTS` combines a URL/ID and `--check <category>` → single-page mode, only the named category.
- Any other shape → stop and ask the user what they meant. Do not guess.

`/lint-notion` **never modifies files**. Like `/lint`, it surfaces a report. Fixes are user-initiated: re-run `/ingest-notion <url>` to refresh a stale or renamed page (this overwrites the cached copy in place per the slug-frozen rule); decide manually how to handle deleted / inaccessible pages.

After producing the report and surfacing it to the user, append the `lint-notion` log entry per `CLAUDE.md > Lint-notion workflow > After producing the report` (canonical conventions in `wiki/log.md`'s HTML comment).
