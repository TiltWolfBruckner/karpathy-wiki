# Design Notes — Implementation Choices to Review

Judgment calls made during implementation that go beyond the strict acceptance criteria of `tasks/prd-llm-wiki.md`. Review after all user stories ship; fold accepted ones into the PRD or revise.

## US-002

- **Added "Date discipline" section to `CLAUDE.md`.** Not in acceptance criteria. The date-tagged citations and three sidecar dates needed one canonical rule (ISO 8601, never invent past dates) instead of scattering it across Cross-references, Frontmatter, and Source sidecars.
- **Added "Sections under construction" placeholder at end of `CLAUDE.md`.** Lists the four sections still to come (Page types, Ingest, Query, Lint). Reason: a future LLM session reading a partial CLAUDE.md should see that workflows aren't authorized yet rather than improvising one.
- **File ownership rendered as a table.** Acceptance just said "explicit"; a table makes the read/modify/create matrix unambiguous per path.

## US-003

- **Added `wiki/comparisons/` and `wiki/overviews/` directories.** The PRD's US-007 lists these as index sections (`## Comparisons`, `## Overviews`) and US-003 names them as page types, but US-001's directory list omitted them. Resolved by creating the subdirectories now (with `.gitkeep` markers). Alternative was to put these page types at `wiki/` root — rejected for inconsistency with the by-type layout.
- **Source-summary frontmatter is intentionally different from other page types.** It uses `source: <raw-basename>` to point to the original, and omits the `sources:` list (a source summary isn't built from other sources). All other page types follow the standard `sources: [...]` schema.
- **Entity-vs-concept decision rule prefers concept on ambiguity.** The heuristic in CLAUDE.md says: entity = proper-noun, one canonical instance; concept = abstraction. Borderline cases default to concept. Reason: concept pages are easier to merge later if needed; entity pages tend to accumulate identity-specific structure that's hard to undo.
