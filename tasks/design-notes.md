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

## US-004

- **Pre-flight check for basename collisions in `raw/`.** Beyond the PRD acceptance, the workflow now stops if a new source's basename clashes with an existing one (sidecars are flat under `raw/info/`). Cheap, prevents silent overwrites.
- **Three contradiction-resolution patterns documented (Replace / Both / Keep old).** PRD just said "pause and confirm". Adding the three named patterns gives the user a vocabulary to choose between rather than free-form negotiation.
- **Workflow log-entry body uses bullets** (Sidecar / Summary / Pages touched / Notable). Not in PRD; chosen so log entries are scannable and `grep`-able.

## US-005

- **Canonical grep patterns documented inline.** PRD said "documents the canonical grep/find patterns" but didn't specify which. Picked the five most common: list by keyword, with-context, by type, by source citation, all wikilink targets.
- **"Don't log declined queries" rule.** PRD's filing rule didn't explicitly say what happens when the user declines. Added the rule that declined queries leave no trace in `log.md` ("the wiki only records what compounds"). This avoids polluting the log with chat-history noise.
- **Bias toward offering** — emphasized in the workflow text. The user's filing rule answer combined "concrete trigger" and "always offer non-trivial" — the workflow leans into the second by suggesting page type and slug concretely instead of asking permission abstractly.

## US-006

- **Detailed `find`/`grep` commands inline for the file-system checks** (broken wikilinks, missing sidecars). PRD just listed the checks; including the commands makes the workflow runnable without re-deriving the patterns each session.
- **Orphan-sidecar detection added** (`.info.md` / `.text.md` files in `raw/info/` whose original no longer exists). PRD only said "missing sidecars"; the inverse case is just as corrosive and cheap to check.
- **Performance note (sequential at small scale, parallel at larger scale)** added — not in acceptance, but answers the obvious "how slow does this get" question once the wiki has hundreds of pages.
- **Sections-under-construction placeholder removed entirely** (it was empty after US-006). The CLAUDE.md no longer claims anything is missing.

## US-007

- **Empty index sections have no `(none)` placeholder** — just the H2 with nothing under it. Cleaner; LLM doesn't need to remove placeholders when adding the first entry.
- **Index summary rule pinned to "first meaningful sentence" of Definition/Summary/Abstract.** PRD just said "one-line summary"; specifying which sentence avoids wording drift across ingests.
- **Log conventions duplicate the per-op body bullets** in the HTML comment. Means the LLM doesn't need to cross-reference CLAUDE.md every time it writes a log entry — `wiki/log.md` carries the spec.
- **Confirmed: declined queries are not logged.** Restated in the log-conventions HTML comment so it's explicit at the file level.
