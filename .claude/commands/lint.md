---
description: Run the wiki lint — contradictions, freshness, orphans, missing pages, broken links, missing sidecars. Pass "staleness" to also flag pages older than 6 months.
argument-hint: "" | staleness
---

Run the **Lint workflow** defined in `CLAUDE.md > Lint workflow`.

Argument: `$ARGUMENTS`

`CLAUDE.md > Lint workflow` is the canonical source of truth — the eight default checks, the optional staleness check, the broken-vs-missing-page dedup rule, the report format, and the "never apply fixes automatically" rule all live there. Follow it exactly; do not improvise. If `CLAUDE.md` is unavailable, stop and tell the user.

**Argument interpretation:**

- Empty `$ARGUMENTS` → run the default checks only (no staleness).
- `$ARGUMENTS` contains the word `staleness` (case-insensitive, anywhere in the string) → run the default checks AND the optional staleness check (flag wiki pages whose `updated:` frontmatter is more than 6 months old).
- Any other non-empty `$ARGUMENTS` → stop and ask the user what they meant. Do not guess.

The broken-wikilinks (check #7) and missing-pages (check #4) checks delegate to `python3 scripts/lint-wikilinks.py wiki/`. The other six checks are inline per `CLAUDE.md > Lint workflow`. Produce a single structured markdown report, surface it to the user, and wait for approval before applying any fixes — lint never modifies files on its own.

After the user approves and you've applied fixes, append the lint log entry per `CLAUDE.md > Lint workflow` step 3 (canonical conventions in `wiki/log.md`'s HTML comment).
