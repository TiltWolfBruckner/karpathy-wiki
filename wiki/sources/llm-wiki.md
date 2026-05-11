---
type: source-summary
created: 2026-05-11
updated: 2026-05-11
source: llm-wiki
indexed: 2026-05-11
url:
source-type: note
---

# LLM Wiki — A pattern for building personal knowledge bases using LLMs

## Citation

`raw/llm-wiki.md` (no original URL — repo-internal design doc; the reference design for this very wiki)

## Abstract

Describes a pattern where an LLM agent incrementally builds and maintains a persistent
markdown wiki from raw source documents, instead of doing RAG from scratch on every query.
Three layers (raw, wiki, schema) plus operations for ingest, query, and lint. Positioned
as a modern realization of [[vannevar-bush]]'s 1945 [[memex]] vision — what Bush couldn't
solve was who does the maintenance, and the answer is the LLM.

## Key claims

- Most LLM+document workflows are RAG: retrieve fragments and synthesize per query — nothing accumulates.
- A persistent, LLM-maintained wiki compiles synthesis once and keeps it current; knowledge compounds.
- The LLM owns all wiki writes; the human curates sources, directs analysis, and asks questions.
- The schema (`CLAUDE.md` / `AGENTS.md`) is what makes the LLM a disciplined maintainer rather than a generic chatbot.
- `index.md` + `log.md` plus `grep` is sufficient retrieval at moderate scale (~hundreds of pages); embedding-based RAG is not required.
- Good query answers should be filed back into the wiki as new pages so explorations compound.
- Lint passes catch what humans abandon: contradictions, stale claims, orphans, missing cross-references.
- Maintenance burden — not reading or thinking — is what kills human-maintained wikis; LLMs make that cost near-zero.
- The pattern is domain-agnostic: personal journals, research deep-dives, book companion wikis, internal team wikis, etc.

## Entities

- [[obsidian]]
- [[vannevar-bush]]

## Concepts

- [[llm-wiki-pattern]]
- [[memex]]
- [[rag]]

## Notes

The reference doc is intentionally abstract — directory layout, schema conventions, page
formats, and tooling are all left to the implementer. Specific implementation choices made
during scaffolding are tracked in `tasks/design-notes.md`. Other entities the doc mentions
in passing but doesn't develop deeply (Claude Code, Tolkien Gateway, NotebookLM, qmd, Marp,
Dataview, Obsidian Web Clipper) are intentionally not yet wiki pages — pre-creating pages
the wiki doesn't yet need is discouraged by `CLAUDE.md > Page types`.
