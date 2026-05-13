---
description: Run the wiki lint — contradictions, freshness, orphans, missing pages, broken links, missing sidecars. Pass "staleness" to also flag pages older than 6 months.
argument-hint: "" | staleness
---

Run the **Lint workflow** against:

`$ARGUMENTS`

This SKILL.md is the canonical source of truth — the eight default checks, the optional staleness check, the broken-vs-missing-page dedup rule, and the "never apply fixes automatically" rule all live below. The report format is in the bundled file `sample-report.md`. Follow it exactly; do not improvise. For cloud-freshness checks on Notion sources, see the companion skill `.claude/skills/lint-notion/`.

**Argument interpretation:**

- Empty `$ARGUMENTS` → run the default checks only (no staleness).
- `$ARGUMENTS` contains the word `staleness` (case-insensitive, anywhere in the string) → run the default checks AND the optional staleness check (flag wiki pages whose `updated:` frontmatter is more than 6 months old).
- Any other non-empty `$ARGUMENTS` → stop and ask the user what they meant. Do not guess.

**Lint never modifies files on its own.** It surfaces findings and proposed fixes; the user confirms what to apply.

**`/lint` is offline-only.** It never makes Notion network calls. Cloud freshness for ingested Notion pages (content drift, title drift, deletion, etc.) lives entirely in the separate `.claude/skills/lint-notion/` skill — that command is user-invoked when Notion sources are suspected stale.

## Default checks

Run all of these and produce one report section per check (even if empty — empty sections confirm the check ran). The expected report shape is in `sample-report.md` (alongside this SKILL.md).

1. **Contradictions between pages.** Pages that make incompatible claims about the same entity/concept. Detect by reading related pages (use the index plus cross-references); flag when claims about the same thing diverge.

2. **Freshness conflicts.** Wiki pages where a date-tagged citation `[[old-source|YYYY-MM-DD]]` is contradicted by a newer date-tagged citation on the same claim — either elsewhere on the same page, or on a related page. The dates make this detectable without parsing prose. Flag the page, both sources, and the date delta.

3. **Orphan pages.** Wiki pages with no inbound `[[wikilinks]]`. Detect by enumerating all page slugs, then `grep`-ing the rest of the wiki for each. Source-summary pages are partially exempt (often only linked from a single entity/concept page) but should be flagged when no entity/concept references them at all.

4. **Missing pages — important concepts/entities mentioned but unwritten.** Run `python3 scripts/lint-wikilinks.py wiki/ --check missing-pages`. A finding fires when a wikilink in a source-summary's `## Entities` or `## Concepts` H2 section points to a slug with no matching page anywhere under `wiki/`. Reported once per target, with every referring location listed.

5. **Missing cross-references.** Pages that mention a known entity/concept in prose without `[[wikilink]]`-ing it. Heuristic: for each existing page slug, grep the rest of the wiki for the corresponding natural-language name; if a match has no surrounding wikilink, flag.

6. **Frontmatter validity.** Every wiki page has YAML frontmatter with the fields required by its `type` (see `CLAUDE.md > Page types`). Check: `type` is one of the five values, `created`/`updated` are valid ISO 8601 dates, `sources:` (or `source:` for source-summary) references slugs that exist.

7. **Broken `[[wikilinks]]`.** Run `python3 scripts/lint-wikilinks.py wiki/ --check broken`. Every result is a real broken link — the tool skips HTML comments, fenced code blocks, and inline code spans, so template content (e.g. `[[slug]]` / `[[page-1]]` placeholders inside `wiki/index.md` and `wiki/log.md`'s HTML conventions) does not false-positive.

8. **Missing source sidecars.** For every file in `raw/` outside `raw/info/` and `raw/assets/`, there must be a matching `raw/info/<basename>.info.md`. PDFs additionally need `raw/info/<basename>.text.md`. Detect:

   ```bash
   # originals (excluding info/ and assets/), at any depth in raw/
   find raw -type f -not -path 'raw/info/*' -not -path 'raw/assets/*' -not -name '.*'
   # for each, expect raw/info/<basename>.info.md (and .text.md for *.pdf)
   ```

   Also flag **orphan sidecars** — `.info.md` or `.text.md` files in `raw/info/` whose original no longer exists.

   Nested sources under `raw/notion/` follow the same convention — sidecars stay flat at `raw/info/<basename>.info.md`. The `find` command above already picks them up; the basename-to-sidecar mapping doesn't change.

   `notion-index.md` at the repo root is a config artifact, not a source — exempt from this check.

## Broken vs. missing-page dedup

Checks 4 (missing pages) and 7 (broken wikilinks) return **disjoint** findings. A wikilink target classified as `missing-page` does not also fire `broken` for its other occurrences. The dedup is **per-target**, not per-occurrence: even if `[[X]]` is broken on three different pages, if any one of those occurrences sits inside a source-summary's `## Entities` or `## Concepts` H2 section, all three get rolled into a single `missing-page` finding (with all referring locations listed). The Python tool enforces this in its classifier; the lint report should not show the same target in both sections.

Rationale: one action ("create the page") resolves the missing-page *and* every related broken-link occurrence. Reporting both is redundant noise.

## Optional: staleness check

Only when `$ARGUMENTS` matches the staleness trigger described above. **Default lint does not include this** — it grows noisy as the wiki ages.

- Flag any wiki page whose `updated:` frontmatter is more than **6 months** ago, as a candidate for review.
- Finding format: page path, `updated:` date, age, suggested action ("re-read against newer sources" or "confirm still accurate").
- Staleness alone is not a defect — just a prompt to look.

## Report format

A single markdown report, one H2 per check (even when empty). Within each H2, one bullet per finding with:

- **File path(s)** — affected page(s), relative to repo root
- **One-line description** — what's wrong
- **Suggested fix** — concrete action the user can approve

For the exact expected shape (with worked findings across all categories), see `sample-report.md` next to this SKILL.md.

## After producing the report

1. **Do not apply fixes automatically.** Surface the report; wait for the user.
2. The user will say "apply all", "apply these", or "ignore for now". For each approved fix, perform it and confirm the lint finding is resolved.
3. **Append a log entry** to `wiki/log.md` (canonical conventions in its HTML comment):

   ```markdown
   ## [YYYY-MM-DD] lint | <default | with staleness>

   - Findings: <count by category, e.g. "1 contradiction, 2 missing pages, 0 broken links">
   - Applied: <count of fixes the user approved>
   - Deferred: <count left for later>
   - Notable: <anything unusual — e.g. cluster of stale pages on one topic>
   ```

## Performance note

At small scale (tens of pages) run checks sequentially. At larger scale, the file-system checks (broken wikilinks, missing sidecars) can run in parallel with the prose-reading checks (contradictions, missing cross-references) since they touch disjoint inputs.
