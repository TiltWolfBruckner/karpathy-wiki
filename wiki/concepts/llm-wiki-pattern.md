---
type: concept
created: 2026-05-11
updated: 2026-05-11
sources:
  - llm-wiki
---

# LLM-Maintained Wiki Pattern

## Definition

A pattern where an LLM agent incrementally builds and maintains a persistent, interlinked
markdown wiki from raw source documents. Sources are read once and integrated into entity
pages, concept pages, and source summaries; queries are answered against the compiled wiki
rather than the raw corpus. Three layers (raw sources, the wiki, the schema file) plus
three operations (ingest, query, lint). Contrast with [[rag]].

## Why it matters

The pattern resolves the historical maintenance burden that kills human-maintained wikis.
The bookkeeping — updating cross-references, keeping summaries current, flagging
contradictions across dozens of pages — is what LLMs do well and humans avoid. With the
LLM doing maintenance, the wiki stays current and knowledge compounds with every source
ingested. The pattern is a modern realization of [[vannevar-bush]]'s [[memex]] vision —
Bush proposed the curated personal store but couldn't solve who would maintain it.

## Related

**Entities:**
- [[vannevar-bush]] — originator of the spiritual ancestor
- [[obsidian]] — common human-facing viewer for the wiki

**Concepts:**
- [[memex]] — historical precursor
- [[rag]] — the contrasting pattern

## Sources

- [[llm-wiki|2026-05-11]] — the reference design for this pattern
