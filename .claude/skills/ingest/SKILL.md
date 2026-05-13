---
description: Ingest a source from raw/ into the wiki — sidecar, summary, entity/concept updates, index, log
argument-hint: <path-to-file-in-raw/>
---

Run the **Ingest workflow** against:

`$ARGUMENTS`

This SKILL.md is the canonical source of truth for the steps, source-type handling (markdown / text / PDF), pre-flight checks, contradiction-resolution patterns, and the log-entry format. Follow it exactly — do not improvise. The schema this workflow operates against is defined in `CLAUDE.md` (source sidecars, page types, cross-references). For Notion sources, see the companion skill `.claude/skills/ingest-notion/SKILL.md`.

## Pre-flight checks

- If `$ARGUMENTS` is empty, ask the user which file to ingest. **Do not guess.**
- If `$ARGUMENTS` points to a file outside `raw/`, stop and ask the user before proceeding. Usually the right move is to copy the file into `raw/` first, then ingest the copy — but confirm with the user rather than copying silently.
- If `$ARGUMENTS` points to a file under `raw/info/` or `raw/assets/`, stop — those are sidecar / attachment directories, not source originals.
- If `$ARGUMENTS` points to a file under `raw/notion/`, stop and tell the user to use `/ingest-notion <url>` instead — Notion sources have their own workflow.
- If `$ARGUMENTS`'s basename collides with an existing file in `raw/` (different extension, same basename), stop and ask. Sidecars are flat under `raw/info/` and basenames must be unique.

## Steps

1. **Read the source.**
   - Markdown / text (`.md`, `.txt`, clipped articles): read directly with the Read tool.
   - PDF: read with Read's `pages` parameter (required for files >10 pages — Read fails without it). For PDFs >20 pages, read in batches.
   - For unfamiliar source types, ask the user before processing.

2. **Create or update the sidecar at `raw/info/<basename>.info.md`.**
   - First ingest: write the full frontmatter (see `CLAUDE.md > Source sidecars`). `created` = source's publication date if you can read it off the source itself (article byline, paper date, etc.), otherwise = today. `indexed` = today. `updated` = today. Fill `title`, `url`, `source-type` when available.
   - Re-ingest: bump `updated` to today. Touch other fields only if the source itself changed.
   - **For PDFs**, also write `raw/info/<basename>.text.md` containing the extracted text (first ingest only, unless the PDF was replaced). All subsequent reads and `grep` target this `.text.md`, not the PDF.

3. **Discuss key takeaways with the user.** Before writing anything under `wiki/`, summarize what you read in 3–6 bullets: the source's main claims, what entities/concepts it covers, any surprises or contradictions with existing wiki pages. **Wait for the user's reaction — the pause is canonical, not optional.** They may want to emphasize, deemphasize, or skip parts. Non-interactive batch runs only happen when the user has explicitly directed them in the session (e.g. the US-008 validation skip was a one-off at user direction, not a workflow mode).

4. **Write the source-summary page** at `wiki/sources/<slug>.md`, where `<slug>` matches the source basename. Follow the template in `CLAUDE.md > Page types > source-summary` — required sections are title, citation, abstract, key claims, entities, concepts, optional notes; frontmatter uses `source:` (singular) plus `indexed`, `url`, `source-type`. A full worked example lives in `docs/page-type-examples.md > source-summary`.

5. **Identify entity/concept pages to create or update.** Walk through the entities and concepts the source covers. For each:
   - **Page exists, source agrees:** add a new `[[source-slug|YYYY-MM-DD]]` citation in the Sources section and (where relevant) in the body. Update prose if the new source adds detail. Bump `updated:` in frontmatter.
   - **Page does not exist, the entity/concept warrants one:** create it using the template from `CLAUDE.md > Page types` (worked examples in `docs/page-type-examples.md`). Cite the new source.
   - **Page exists, source contradicts an existing claim:** stop. See "Handling contradictions" below.

6. **Update `wiki/index.md`.** Add or update entries for any new or modified pages. Section order: Sources / Entities / Concepts / Comparisons / Overviews. Alphabetical by slug within each section. Entry format: `- [[slug]] — one-line summary`. **Canonical conventions in `wiki/index.md`'s HTML comment** — re-read it before each update.

7. **Append a log entry to `wiki/log.md`.** Newest entries go at the bottom. Format (canonical conventions in `wiki/log.md`'s HTML comment):

   ```markdown
   ## [YYYY-MM-DD] ingest | <Source Title>

   - Sidecar: `raw/info/<basename>.info.md`
   - Summary: [[<slug>]]
   - Pages touched: [[page-1]], [[page-2]], ...
   - Notable: <one line on anything unusual — contradictions resolved, new entities discovered, etc.>
   ```

## Handling contradictions

When a new source's claim contradicts an existing wiki claim:

1. **Stop before writing anything to `wiki/` for the contradicted page.** Surface the contradiction to the user: which claim, which page, which old source it relies on (with date), which new source contradicts it (with date). Read both citations and quote the relevant lines.
2. **Ask the user how to resolve.** Three patterns:
   - **Replace:** the new source supersedes the old. Update the page text; replace the old `[[old-source|YYYY-MM-DD]]` citation with `[[new-source|YYYY-MM-DD]]`. The old `raw/` file and its sidecar are preserved for reference — only the citation moves.
   - **Both:** the page now notes that sources disagree. Cite both with their dates and show the disagreement explicitly.
   - **Keep old:** the user judges the old claim more credible. Add a brief note that a newer source disagrees; cite both.
3. **Log the resolution** in the ingest log entry's `Notable:` line, e.g. "Resolved contradiction on [[memex]]: replaced [[bush-1945|1945-07-01]] citation with [[reanalysis|2024-11-02]]".

Never silently overwrite a contradicted claim. The whole point of date-tagged citations is that disagreements are surfaced, not papered over.

## Source types — quick reference

| Source type | Read with | `.text.md` sidecar? |
|---|---|---|
| Clipped markdown article (`.md`) | Read tool, direct | no |
| Pasted text or note (`.txt`, `.md`) | Read tool, direct | no |
| PDF | Read tool with `pages` parameter (required for >10pp) | **yes** — write extracted text to `raw/info/<basename>.text.md` on first ingest |
| Notion page | Handled by the separate `.claude/skills/ingest-notion/` skill — body is fetched via `mcp__claude_ai_Notion__notion-fetch` and cached under `raw/notion/<slug>.md` | no — the cached `.md` under `raw/notion/` *is* the readable form |
