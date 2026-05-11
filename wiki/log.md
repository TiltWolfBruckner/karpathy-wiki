# Wiki Log

<!--
=== Log conventions (canonical — also referenced from CLAUDE.md workflow sections) ===

- Append-only. Newest entries at the BOTTOM (chronological top-to-bottom).
- Entry header:  ## [YYYY-MM-DD] <op> | <title>
    <op> ∈ { ingest, query, lint }
    <title> is the source title (ingest), question summary (query), or lint mode (lint)
- Body bullets per op:
    ingest:
      - Sidecar: raw/info/<basename>.info.md
      - Summary: [[<slug>]]
      - Pages touched: [[page-1]], [[page-2]], ...
      - Notable: <one line on anything unusual>
    query:    (only logged when the user files the answer)
      - Question: <full or summarized question>
      - Filed: [[<new-page-slug>]]
      - Pages touched: [[page-1]], [[page-2]], ...
      - Notable: <one line — contradictions surfaced, fresh source needed, etc.>
    lint:
      - Findings: <count by category, e.g. "1 contradiction, 2 missing pages, 0 broken links">
      - Applied: <count of fixes the user approved>
      - Deferred: <count left for later>
      - Notable: <anything unusual — e.g. cluster of stale pages on one topic>
- Parseable with simple shell:
    grep "^## \[" wiki/log.md          # all entry headers
    grep "^## \[" wiki/log.md | tail -5  # last 5 entries
- Queries the user declines to file are NOT logged here. That's intentional — the wiki only records what compounds.
-->

A chronological record of every ingest, query (when filed), and lint pass. Append-only — newest at the bottom.

## [2026-05-11] ingest | LLM Wiki — A pattern for building personal knowledge bases using LLMs

- Sidecar: `raw/info/llm-wiki.info.md`
- Summary: [[llm-wiki]]
- Pages touched: [[llm-wiki]], [[obsidian]], [[vannevar-bush]], [[llm-wiki-pattern]], [[memex]], [[rag]]
- Notable: First end-to-end validation ingest (US-008). Six wiki pages created from scratch; no contradictions to resolve; no prior wiki state to conflict against. Several entities mentioned in passing in the source (Claude Code, Tolkien Gateway, NotebookLM, qmd, Marp, Dataview, Obsidian Web Clipper) intentionally left without wiki pages per "Page types" guidance against pre-creating.
