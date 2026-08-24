# LLM Wiki

A personal knowledge base maintained by an LLM agent (Claude Code) from a curated collection of source documents. Instead of doing RAG from raw sources on every query, the LLM reads each source once, integrates it into a persistent interlinked wiki, and answers future questions against the compiled wiki.

## What this is

Three layers, plus per-source sidecars:

- **`raw/`** — your original source documents. Articles, PDFs, pasted notes. The LLM reads these but never modifies the originals.
- **`raw/info/`** — per-source sidecars. For each `raw/<file>`, the LLM maintains `raw/info/<basename>.info.md` with metadata (`created`, `indexed`, `updated`). PDFs additionally get `raw/info/<basename>.text.md` with extracted text for grep.
- **`wiki/`** — LLM-generated and LLM-maintained markdown. Source summaries (`wiki/sources/`), entity pages (`wiki/entities/`), concept pages (`wiki/concepts/`), plus `index.md` and `log.md`. You read it; the LLM writes it.
- **`CLAUDE.md`** — the schema. Tells the LLM how the wiki is structured and the workflows for ingest, query, and lint. Co-evolves with use.

The reference design is `llm-wiki.md` at the repo root. The PRD that scopes the build is `tasks/prd-llm-wiki.md`.

## How to use

1. **Open the repo in Claude Code** (point it at this directory).
2. **Drop a source into `raw/`** — clipped article, pasted text, PDF, etc.
3. **Ingest:** run `/ingest raw/<file>` or say "ingest this." The LLM creates the source's sidecar in `raw/info/`, writes a source summary in `wiki/sources/`, updates relevant entity/concept pages with date-tagged citations (`[[source-slug|YYYY-MM-DD]]`), refreshes `wiki/index.md`, and appends a `wiki/log.md` entry.
4. **Query:** ask questions. The LLM searches the wiki (not raw sources) and answers with `[[wikilinks]]` and date-tagged source citations. Substantial answers may be offered as new wiki pages.
5. **Lint:** periodically ask "lint the wiki" to surface contradictions, freshness conflicts, orphan pages, missing cross-references, and missing sidecars. Use "lint with staleness" to additionally flag pages older than 6 months.

## Commands

Five project slash commands, defined in `.claude/commands/`:

| Command | What it does |
|---|---|
| `/ingest <path>` | Ingest a file from `raw/` — writes the sidecar, discusses takeaways with you, then creates the source summary, entity/concept pages, index entry, and log entry. |
| `/ingest-notion <notion-url-or-id>` | Same pipeline for a Notion page — fetches via the Notion MCP, caches to `raw/notion/`, writes a sidecar, appends to the Notion index page, then hands off to the standard flow. |
| `/query <question>` | Ask the wiki a question. Reads `wiki/index.md` (and greps `wiki/` if needed), answers with `[[wikilink]]` citations, and offers to file substantial answers as new pages. |
| `/lint` | Offline consistency pass: contradictions, freshness conflicts, orphan pages, missing pages, missing cross-references, frontmatter validity, broken wikilinks, missing sidecars. Add `staleness` (`/lint staleness`) to also flag pages untouched for 6+ months. Reports only — never fixes without approval. |
| `/lint-notion [url-or-id] [--check <category>]` | Cloud-freshness pass for Notion sources: content drift, title drift, deletion, revoked permissions, index-page link rot. No argument checks all ingested Notion pages; a URL checks just one. Opt-in checks: `--check urls`, `--check index`. |

All five also respond to natural language ("ingest this article", "lint the wiki") — the slash command and the phrasing trigger the identical workflow.

## Viewing in Obsidian

Open this directory as an Obsidian vault. Wikilinks (`[[page]]`), backlinks, and the graph view all work out of the box. Per-vault state lives in `.obsidian/` (gitignored).

## Notes

- The wiki is just markdown + git. Version history, branching, and diffing all work normally.
- The `tasks/` directory holds PRDs and planning docs.
- The `.claude/commands/` directory holds the project-scoped slash commands listed under "Commands" above.
- `CLAUDE.md` is expected to drift as you discover what conventions work for your domain — treat it like configuration, not stone.
