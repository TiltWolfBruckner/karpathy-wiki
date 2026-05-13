---
description: Ingest a Notion page via the Notion MCP — cache to raw/notion/, write sidecar, append to Notion index page, then run the standard wiki-build steps
argument-hint: <notion-url-or-page-id>
---

Run the **Ingest workflow > Notion sources** subsection defined in `CLAUDE.md > Ingest workflow > Notion sources` against:

`$ARGUMENTS`

`CLAUDE.md > Ingest workflow > Notion sources` is the canonical source of truth — the Notion-index-page bootstrap, the slug-frozen-at-first-ingest rule, the overwrite-in-place re-ingest behavior, the sidecar frontmatter shape (including `notion-page-id` and `notion-last-edited`), the index-page append step, and the hand-off to step 3 of the base ingest workflow all live there. Follow it exactly; do not improvise. If `CLAUDE.md` is unavailable, stop and tell the user.

**Pre-flight (mirrored from the workflow; restated here so the slash command stops cleanly when arguments are bad):**

- If `$ARGUMENTS` is empty, ask the user which Notion page to ingest. **Do not guess.**
- Resolve `$ARGUMENTS` to a Notion page ID. Accepted forms: full Notion URL, bare UUID, or share link. If you cannot resolve it, stop and ask.
- Read `notion-index.md` at the repo root. If it is missing or has an empty `notion-index-page-id:`, stop and ask the user for the URL of the Notion page they want to use as the registry; write `notion-index.md` (with the YAML frontmatter shown in `CLAUDE.md > Ingest workflow > Notion sources > Bootstrap`), then proceed. **Do not auto-create the Notion page.**
- Check for re-ingest with `grep -l "notion-page-id: <uuid>" raw/info/*.info.md`. If a matching sidecar exists, this is a re-ingest — use the existing slug and **overwrite** `raw/notion/<slug>.md` in place. Never create a second cached file for the same Notion page.

Once pre-flight passes, run the Notion-specific steps (1–4) in `CLAUDE.md > Ingest workflow > Notion sources`, then hand off to **step 3 of the base ingest workflow** ("Discuss key takeaways with the user") and continue from there.
