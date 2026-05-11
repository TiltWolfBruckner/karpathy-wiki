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

## Viewing in Obsidian

Open this directory as an Obsidian vault. Wikilinks (`[[page]]`), backlinks, and the graph view all work out of the box. Per-vault state lives in `.obsidian/` (gitignored).

## Notes

- The wiki is just markdown + git. Version history, branching, and diffing all work normally.
- The `tasks/` directory holds PRDs and planning docs.
- The `.claude/commands/` directory will hold project-scoped slash commands (currently `/ingest`).
- `CLAUDE.md` is expected to drift as you discover what conventions work for your domain — treat it like configuration, not stone.
