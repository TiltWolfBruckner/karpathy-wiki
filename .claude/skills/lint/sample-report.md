# Sample lint report

Reference shape for the report produced by `.claude/skills/lint/SKILL.md`. One H2 per check, even when empty — empty sections confirm the check ran. Within each H2, one bullet per finding with the affected path, a one-line description, and a concrete suggested fix.

```markdown
# Wiki lint report — 2026-05-10

## Contradictions

(none)

## Freshness conflicts

- `wiki/concepts/memex.md`
  - Cites `[[bush-1945|1945-07-01]]` for the trail-following claim, but `[[modern-reanalysis|2024-11-02]]` (also cited on the page) disputes it.
  - **Suggested fix:** Resolve per "Handling contradictions" in `.claude/skills/ingest/SKILL.md` — Replace, Both, or Keep old.

## Orphan pages

- `wiki/entities/obscure-thing.md`
  - No inbound wikilinks from any other page.
  - **Suggested fix:** Link from a related page, merge into an existing one, or delete.

## Missing pages

- `[[associative-trails]]` — no wiki page exists for this slug
  Referenced from:
    - `wiki/sources/llm-wiki.md:14` (Entities/Concepts section — this occurrence is what triggers the classification)
    - `wiki/concepts/memex.md:22`   (would have been a separate broken-wikilink finding; per-target dedup rolls it into this entry)
  - **Suggested fix:** Create a `concept` page using the template in `CLAUDE.md > Page types > concept` (worked example in `docs/page-type-examples.md`). One file resolves all referring locations.

## Missing cross-references

(none)

## Frontmatter validity

(none)

## Broken wikilinks

- `wiki/concepts/memex.md:18`  `[[as-we-may-think]]`
  - Target doesn't resolve. The occurrence sits in the page's "Related" section, not a source-summary's `## Entities` or `## Concepts` H2 — so it stays in the broken-wikilinks category (per "Broken vs. missing-page dedup" in `SKILL.md`).
  - **Suggested fix:** Create `wiki/entities/as-we-may-think.md` (Bush's essay is an entity per the entity-vs-concept rule), or fix the link target.

## Missing source sidecars

- `raw/some-article.md`
  - No `raw/info/some-article.info.md`.
  - **Suggested fix:** Run `/ingest raw/some-article.md` to create the sidecar (and the wiki summary if not yet ingested).
```
