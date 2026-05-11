---
type: entity
created: 2026-05-11
updated: 2026-05-11
sources:
  - llm-wiki
entity-kind: software
aliases: [Obsidian.md]
---

# Obsidian

## Summary

A local-first markdown editor and knowledge management application. In the
[[llm-wiki-pattern]], Obsidian is the user-facing "IDE" — the user views the
LLM-maintained wiki through Obsidian on one side while the LLM agent makes edits on the
other. Obsidian's graph view, backlinks, and `[[wikilink]]` syntax make the wiki's
structure visible and navigable without any custom tooling.

## Key facts

- Operates over plain markdown files in a directory (a "vault")
- Renders `[[wikilinks]]` natively; resolves links by filename within the vault
- Per-vault state lives in `.obsidian/` (gitignored in this repo)
- Plugins commonly paired with the LLM-wiki pattern: Obsidian Web Clipper (clip web pages to markdown), Dataview (frontmatter queries), Marp (slide decks)

## Related

**Concepts:**
- [[llm-wiki-pattern]] — uses Obsidian as the viewer / human-facing IDE

## Sources

- [[llm-wiki|2026-05-11]] — describes Obsidian as the IDE in the pattern
