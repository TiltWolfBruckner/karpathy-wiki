---
description: Ingest a Notion page via the Notion MCP — cache to raw/notion/, write sidecar, append to Notion index page, then run the standard wiki-build steps
argument-hint: <notion-url-or-page-id>
---

Run the **Notion ingest workflow** against:

`$ARGUMENTS`

This SKILL.md covers the Notion-specific parts of the ingest pipeline. After steps 1–4 below, **hand off to `.claude/skills/ingest/SKILL.md` from step 3** ("Discuss key takeaways with the user") and continue from there — the cached `raw/notion/<slug>.md` is treated like any other raw source after this point. The schema (source sidecars, page types) is defined in `CLAUDE.md`.

## Why a separate variant?

Notion pages live in the cloud, not under `raw/`. The LLM fetches them via the Notion MCP, caches the markdown body under `raw/notion/`, writes a sidecar at `raw/info/<slug>.info.md`, and (for traceability) appends an entry to a single **Notion index page** in the user's workspace. From the hand-off point onward the cached file is just another raw source.

## Bootstrap — the Notion index page

A single Notion page tracks every Notion document this wiki has ingested. Its location is stored in `notion-index.md` at the repo root (gitignored — machine-specific):

```yaml
---
notion-index-page-id: <uuid>
notion-index-page-url: https://www.notion.so/...
---

# Notion ingest index

The Notion page at the URL above is the registry of every Notion document
this wiki has ingested. Maintained by `/ingest-notion`.
```

If `notion-index.md` is missing or has an empty `notion-index-page-id`, **stop and ask the user for the URL of the Notion page they want to use as the index**. Write the file, then proceed. **Do not auto-create the Notion page** — the user picks where in their workspace it lives.

## Pre-flight

- If `$ARGUMENTS` is empty, ask which Notion page to ingest. **Do not guess.**
- Resolve `$ARGUMENTS` to a Notion page ID. Accepted forms: full Notion URL, bare UUID, or share link. If unresolvable, stop and ask.
- Read `notion-index.md`. If missing or empty, run the bootstrap above.
- Re-ingest detection: `grep -l "notion-page-id: <uuid>" raw/info/*.info.md`. If a sidecar with that page ID exists, this is a re-ingest — use the **overwrite path** in step 2 below.

## Filename convention — slug is frozen at first ingest

One file per Notion page. Ever. The slug derived from the Notion title at first ingest becomes the page's permanent identifier in this wiki — `raw/notion/<slug>.md` and `raw/info/<slug>.info.md` and (downstream) `wiki/sources/<slug>.md`. **The slug never changes** — not when the Notion title is renamed, not on re-ingest, not on lint. This keeps every `[[slug|YYYY-MM-DD]]` citation across the wiki stable forever. The Notion title is just a *label* stored in the sidecar's `title:` field; it can drift independently of the slug.

## Steps

1. **Fetch the page via `mcp__claude_ai_Notion__notion-fetch`.** Capture: page title, body, URL, page ID, `last_edited_time`, and `created_time` if the MCP exposes it. Flatten the body to plain markdown (most Notion blocks have a direct markdown equivalent; for anything unrecognized, preserve as a fenced HTML block and note in the source-summary's "Notes" section later).

2. **Write the cached source at `raw/notion/<slug>.md`:**

   - **First ingest** (no sidecar matched the page ID in pre-flight): slugify the current Notion title (kebab-case, lowercase, ASCII-only), then write `raw/notion/<slug>.md` with the fetched body. If the chosen slug collides with an existing basename anywhere under `raw/`, append a short qualifier (`<slug>-notion`) and proceed.
   - **Re-ingest** (sidecar exists for this page ID): use the **existing slug** from the matched sidecar, regardless of whether the current Notion title would slugify differently. **Overwrite** `raw/notion/<slug>.md` with the fresh body. No version suffixes, no second file, no rename. Exactly one cached file per Notion page exists when this step finishes.

3. **Write or update the sidecar at `raw/info/<slug>.info.md`:**

   ```yaml
   ---
   title: <current Notion page title>
   url: <current Notion URL>
   source-type: notion
   source-genre: notion-page
   notion-page-id: <uuid>
   notion-last-edited: <Notion's last_edited_time, ISO 8601>
   created: <Notion's created_time if exposed, else today>
   indexed: <first-ingest date — preserved across re-ingests>
   updated: <today>
   ---
   ```

   On re-ingest, refresh `title`, `url`, `notion-last-edited`, and `updated`. Preserve `indexed` and `created` (they record first contact, not the latest). Bump `updated` even if the body came back byte-identical — the sidecar is "reviewed as of today".

4. **Append an entry to the Notion index page** via `mcp__claude_ai_Notion__notion-update-page`. Bullet format:

   ```
   - <Page Title> — ingested YYYY-MM-DD → wiki/sources/<slug>.md
     (link: <original notion url>)
   ```

   Append-only. Don't try to de-duplicate prior entries — a second ingest just adds a second line, and the most recent one is the canonical "current" status (mirrors how `wiki/log.md` works).

## Hand-off

After step 4, **continue from step 3 of `.claude/skills/ingest/SKILL.md`** ("Discuss key takeaways with the user"). Everything from there — source-summary at `wiki/sources/<slug>.md`, entity/concept updates, `wiki/index.md`, `wiki/log.md` — is identical to file-based ingest.

## Title drift is not a filename rename

If the user renames the Notion page after ingest, the next `/ingest-notion <url>` refreshes the `title:` field in the sidecar but does **not** rename `raw/notion/<slug>.md` or `wiki/sources/<slug>.md`. The slug is the wiki's stable handle; the title is metadata. `/lint-notion` reports title drift as informational only.
