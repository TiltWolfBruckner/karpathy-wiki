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

## US-009

- **Slash command is intentionally thin.** `.claude/commands/ingest.md` delegates entirely to `CLAUDE.md > Ingest workflow` for the actual steps; the command file only handles trigger-level pre-flight (empty args, path outside `raw/`, sidecar/asset paths, basename collision). Reason: updates to the workflow take effect without touching the command file.
- **Pre-flight is duplicated** between the slash command and `CLAUDE.md`'s Ingest workflow. Restated at the command level so it stops cleanly when arguments are bad — even before delegating to the workflow.

## US-008 (validation findings — follow-ups for future PRD/CLAUDE.md updates)

The end-to-end validation ingest of `raw/llm-wiki.md` produced all expected artifacts (sidecar, source-summary, 5 entity/concept pages, index/log updates) and exercised the date-tagged citation format. Live wiki content has zero broken wikilinks. Findings to address in a follow-up pass:

- **Broken-wikilink lint check needs comment/code-block awareness.** The canonical grep `grep -rohE '\[\[[a-z0-9-]+' wiki/` produces false positives on template placeholders inside HTML comments (`[[slug]]`, `[[page-1]]`, `[[wikilink]]` etc. in `wiki/index.md` and `wiki/log.md`'s HTML conventions). Real fix: a pre-pass that strips `<!-- … -->` and fenced code blocks before grepping. Not patched mid-validation per US-008 rules.
- **Ingest workflow step 3 (discuss takeaways with user) was not actually paused** during validation. The user's standing direction was "do not pause between user stories", which conflicted with the workflow's "Wait for the user's reaction" instruction. The takeaways were produced inline; the user could have intervened. Real ingests in normal sessions will pause as written. Consider documenting an explicit "validation mode" or "batch mode" override in CLAUDE.md if non-interactive ingests become common.
- **`source-type` vocabulary feels under-specified.** Current options: `article | pdf | note | transcript | other`. The reference design `llm-wiki.md` is a design-pattern description; "note" was the least-bad fit but "design-doc" or "spec" would be more accurate. Consider expanding the vocabulary or making it free-form-string-with-suggestions.
- **"First meaningful sentence" index-summary rule required per-type judgment.** For source-summary the summary came from Abstract; for entities from Summary; for concepts from Definition. The rule worked but isn't self-explanatory — could be tightened: "summary = first sentence of the first H2 in the page body."
- **Missing pages vs. broken wikilinks lint checks partially overlap.** A wikilink in a source-summary's Entities/Concepts list that points to a nonexistent page is BOTH a "missing page" finding and a "broken wikilink" finding. Currently surfaced twice. Consider deduplicating in the report — perhaps the missing-pages check fires first and suppresses broken-wikilink findings for those same targets.
  - **Addressed in US-010/US-011** with per-target dedup in `scripts/lint-wikilinks.py`. A target classified as `missing-page` no longer also fires `broken` findings for its other occurrences. CLAUDE.md's lint workflow now delegates both checks to the script.

## US-010

- **Tool emits full filesystem paths**, not paths relative to the repo root. Reason: the script takes a directory arg, and the caller may pass `wiki/` or `/abs/path/to/wiki/`. Letting the user's invocation determine the path style is simpler than guessing a "repo root" the script can't reliably infer. Drawback: log entries that quote tool output may have noisier paths; in practice the LLM should rewrite to repo-relative when filing reports.
- **`section_for_line` walks the file linearly per call**, which is O(n) per lookup. Fine for current wiki size; if perf matters later, pre-compute a line→section map per file. Not optimizing prematurely.
- **Synthetic test fixture** built inline in the verification Bash command rather than committed as a test file. Reason: keeps the repo small; the script is simple enough that one validation run is sufficient evidence. A real test suite belongs in a future story if the tool grows.
- **`from __future__ import annotations`** used so the `dict | None` style annotations work on Python ≥3.9 (macOS ships 3.9+). Avoids a hard requirement on 3.10's PEP 604 syntax.

## US-011

- **Dedup paragraph placed between the checks list and the optional-staleness section**, framed as a "Broken vs. missing-page dedup" subsection. Reason: it applies to both checks 4 and 7, so factoring it out of either check's bullet is clearer than duplicating.
- **Example report updated to demonstrate dedup in action.** The missing-page example now shows two referring locations (one from a source-summary E/C section, one from a concept body) and annotates that the second occurrence would have been a broken finding but got rolled in. Helps a future LLM session reading the example understand *why* the same target isn't in both sections.
- **Other lint checks deliberately not migrated to the tool.** Only #4 (missing-pages) and #7 (broken wikilinks) call out to `scripts/lint-wikilinks.py`. The other six checks (contradictions, freshness conflicts, orphan pages, missing cross-references, frontmatter validity, missing source sidecars) stay as inline prose-and-shell recipes. Reason: tooling adds value where parsing rigor matters; the other checks involve LLM judgment (contradictions, missing cross-references) or simple `find` operations (sidecars) that don't benefit from a Python wrapper.
