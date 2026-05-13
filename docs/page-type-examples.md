# Page-type worked examples

Reference material for the page-type specifications in `CLAUDE.md > Page types`. Each type has a fixed frontmatter shape and required-sections list in `CLAUDE.md` — this file shows what a fully filled-out instance looks like end-to-end. Use these examples as the canonical pattern when writing a new page; consistency with the worked example is more important than creative variation.

## `source-summary`

Specification: `CLAUDE.md > Page types > source-summary`.

```markdown
---
type: source-summary
created: 2026-05-10
updated: 2026-05-10
source: llm-wiki
indexed: 2026-05-10
url:
source-type: text
source-genre: design-doc
---

# LLM Wiki — A pattern for building personal knowledge bases using LLMs

## Citation

`raw/llm-wiki.md` (no original URL — repo-internal design doc)

## Abstract

Describes a pattern where an LLM agent incrementally builds and maintains a persistent
markdown wiki from raw source documents, instead of doing RAG from scratch on every
query. Three layers (raw, wiki, schema) plus operations for ingest, query, and lint.

## Key claims

- Maintenance burden, not reading or thinking, is what kills human-maintained wikis.
- A persistent wiki accumulates synthesis; RAG re-derives it on every query.
- The LLM should own all wiki writes; the human curates sources and asks questions.
- `index.md` + `log.md` plus grep is sufficient retrieval at moderate scale.

## Entities

- [[obsidian]]
- [[claude-code]]
- [[tolkien-gateway]]
- [[vannevar-bush]]

## Concepts

- [[memex]]
- [[rag]]
- [[personal-knowledge-management]]

## Notes

The reference doc explicitly leaves directory layout, conventions, and tooling to the
implementer. Many decisions in this wiki's CLAUDE.md are choices, not the only path.
```

## `entity`

Specification: `CLAUDE.md > Page types > entity`.

```markdown
---
type: entity
created: 2026-05-10
updated: 2026-05-10
sources:
  - llm-wiki
entity-kind: person
aliases: [Bush, V. Bush]
---

# Vannevar Bush

## Summary

American engineer and science administrator (1890–1974). Best known to the PKM community
for his 1945 essay "As We May Think," which proposed the Memex — a personal knowledge
store with associative trails between documents.

## Key facts

- Born 1890, died 1974
- Director of the U.S. Office of Scientific Research and Development during WWII
- Authored "As We May Think" in *The Atlantic*, July 1945

## Related

**Entities:**
- [[as-we-may-think]] — his 1945 essay

**Concepts:**
- [[memex]] — the personal knowledge store he proposed
- [[associative-trails]]

## Sources

- [[llm-wiki|2026-05-10]] — references Bush's vision as a precursor to the LLM-wiki pattern
```

## `concept`

Specification: `CLAUDE.md > Page types > concept`.

```markdown
---
type: concept
created: 2026-05-10
updated: 2026-05-10
sources:
  - llm-wiki
---

# Memex

## Definition

A hypothetical personal knowledge device, proposed by [[vannevar-bush]] in 1945, that
would store a person's books, records, and communications and let them follow associative
trails between documents.

## Why it matters

The Memex is the spiritual ancestor of personal knowledge management systems, hypertext,
and — per [[llm-wiki|2026-05-10]] — the LLM-maintained wiki pattern. Bush correctly
identified that the connections between documents matter as much as the documents
themselves; what he couldn't solve was who maintains the connections.

## Related

**Entities:**
- [[vannevar-bush]]
- [[as-we-may-think]]

**Concepts:**
- [[associative-trails]]
- [[personal-knowledge-management]]

## Sources

- [[llm-wiki|2026-05-10]]
```

## `comparison`

Specification: `CLAUDE.md > Page types > comparison`.

```markdown
---
type: comparison
created: 2026-05-10
updated: 2026-05-10
sources:
  - llm-wiki
compares:
  - rag
  - llm-wiki-pattern
---

# RAG vs. LLM-Maintained Wiki

## What's compared

- [[rag]] — retrieval at query time from raw sources
- [[llm-wiki-pattern]] — incremental compilation into a persistent wiki

## Comparison

| Axis | RAG | LLM-maintained wiki |
|---|---|---|
| When work happens | Per-query | At ingest time, then amortized |
| Synthesis | Re-derived each query | Compiled once, kept current |
| Cross-references | Implicit in embeddings | Explicit `[[wikilinks]]` |
| Human inspection | Embedding chunks (opaque) | Markdown pages (readable) |
| Maintenance | None — always re-derives | Required, but the LLM does it |

## Tradeoffs

RAG wins when the corpus is huge, the queries are unpredictable, and you don't care about
human inspection of intermediate state. The wiki pattern wins when accumulation matters —
when you want to ask the same question in six months and get a richer answer because of
everything that's been read between now and then.

## Sources

- [[llm-wiki|2026-05-10]]
```

## `overview`

Specification: `CLAUDE.md > Page types > overview`.

```markdown
---
type: overview
created: 2026-05-10
updated: 2026-05-10
sources:
  - llm-wiki
covers:
  - vannevar-bush
  - memex
  - associative-trails
  - personal-knowledge-management
  - llm-wiki-pattern
---

# Personal Knowledge Management — Memex to LLM Wikis

## Scope

A reading roadmap from Vannevar Bush's 1945 Memex proposal to today's LLM-maintained
wikis. Covers the conceptual lineage; does not cover commercial PKM tooling (Notion,
Roam, Obsidian as products).

## Reading order

1. [[vannevar-bush]] — the originator of the personal-curation vision
2. [[as-we-may-think|1945-07-01]] — his 1945 essay (start here for primary source)
3. [[memex]] — the device he proposed
4. [[associative-trails]] — the navigation primitive Bush couldn't solve
5. [[personal-knowledge-management]] — the modern practice
6. [[llm-wiki-pattern]] — how LLMs make Bush's vision feasible

## Open questions

- What did the early hypertext systems (Xanadu, NLS) get right that's been forgotten?
- How do LLM-maintained wikis compare to community-maintained ones (Wikipedia, fan wikis)?

## Sources

- [[llm-wiki|2026-05-10]]
```
