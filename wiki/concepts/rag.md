---
type: concept
created: 2026-05-11
updated: 2026-05-11
sources:
  - llm-wiki
---

# RAG

## Definition

Retrieval-augmented generation. A pattern where an LLM answers a query by first retrieving
relevant chunks from a document collection (typically via embedding similarity) and then
generating an answer grounded in those chunks. Retrieval and synthesis happen on every
query — the system rediscovers what's relevant each time.

## Why it matters

RAG is the standard pattern for LLM+document workflows (NotebookLM, ChatGPT file uploads,
most knowledge-base bots). The [[llm-wiki-pattern]] is positioned as an alternative: where
RAG re-derives synthesis on every query from raw fragments, the LLM-wiki compiles synthesis
once into a persistent artifact and keeps it current. RAG wins when the corpus is huge and
queries are unpredictable; the wiki pattern wins when accumulation matters — when asking
the same question in six months should produce a richer answer because of everything read
in between.

## Related

**Concepts:**
- [[llm-wiki-pattern]] — the contrasting pattern

## Sources

- [[llm-wiki|2026-05-11]] — contrasts RAG against the LLM-maintained wiki pattern
