---
description: Ask the wiki a question — read the wiki (not raw/), cite with [[wikilinks]] and date-tagged source citations
argument-hint: <natural-language question>
---

Run the **Query workflow** defined in `CLAUDE.md > Query workflow` against the question:

`$ARGUMENTS`

`CLAUDE.md > Query workflow` is the canonical source of truth — the numbered steps (read `wiki/index.md` first → identify candidate pages → `grep` `wiki/` if needed → read the candidates → synthesize with `[[wikilinks]]` and date-tagged `[[source-slug|YYYY-MM-DD]]` citations → apply the filing rule), the citation rules, the filing rule, and the empty-wiki fallback all live there. Follow it exactly; do not improvise. If `CLAUDE.md` is unavailable, stop and tell the user — do not attempt to reconstruct the workflow.

**Pre-flight:**

- If `$ARGUMENTS` is empty, ask the user what their question is. Do not guess.
- If the question is genuinely outside the wiki's scope (small talk, unrelated tasks), answer normally without forcing a full retrieval pass — `CLAUDE.md > Query workflow` documents this exception.

Once a question is in hand, run the numbered steps in `CLAUDE.md > Query workflow` from step 1. Apply the filing rule at the end — if any trigger fires, offer to file the answer with a concrete suggested page type and slug.
