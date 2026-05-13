---
description: Ask the wiki a question — read the wiki (not raw/), cite with [[wikilinks]] and date-tagged source citations
argument-hint: <natural-language question>
---

Run the **Query workflow** against the question:

`$ARGUMENTS`

This SKILL.md is the canonical source of truth — the numbered steps (read `wiki/index.md` first → identify candidate pages → `grep` `wiki/` if needed → read the candidates → synthesize with `[[wikilinks]]` and date-tagged `[[source-slug|YYYY-MM-DD]]` citations → apply the filing rule), the citation rules, the filing rule, and the empty-wiki fallback all live below. Follow it exactly; do not improvise.

## Pre-flight

- If `$ARGUMENTS` is empty, ask the user what their question is. **Do not guess.**
- If the question is genuinely outside the wiki's scope (small talk, unrelated tasks), answer normally without forcing a full retrieval pass.

## Steps

1. **Read `wiki/index.md` first.** It's the canonical list of every page in the wiki, grouped by type. Identify candidate pages whose one-line summaries match the query.

2. **If the index is enough**, skip to step 4. The index suffices for simple lookups ("which page covers X?", "do we have a page on Y?").

3. **If the index isn't enough, grep `wiki/`.** Canonical patterns:

   - List files matching a keyword: `grep -rli "<keyword>" wiki/`
   - Show keyword in context (2 lines after): `grep -rni -A 2 "<keyword>" wiki/`
   - Restrict to one type: `grep -rli "<keyword>" wiki/concepts/`
   - Find pages citing a specific source: `grep -rli "\[\[<source-slug>|" wiki/`
   - Enumerate every wikilink target in the wiki: `grep -rohE "\[\[[a-z0-9-]+" wiki/ | sort -u`

   Use `-i` for case-insensitive (filenames are kebab-case, headings are natural-case). Search `wiki/` only — don't grep `raw/` for query work; that's what the wiki exists to avoid.

4. **Read the candidate pages.** Use the Read tool — the index is one line per page, the actual page is where claims live.

5. **Synthesize the answer.** Cite wiki pages with `[[wikilink]]` and sources with date-tagged `[[source-slug|YYYY-MM-DD]]`. Quote dates explicitly when claims are date-sensitive ("As of [[llm-wiki|2026-05-10]], the pattern is still abstract, not a packaged tool.").

6. **Apply the filing rule** (below). If the answer meets a trigger, offer to file it as a new wiki page before moving on.

## Citation rules in answers

- Every wiki page referenced: `[[page-slug]]`. Obsidian renders the link.
- Every source cited: `[[source-slug|YYYY-MM-DD]]` — date is the source's `created` if known, otherwise `indexed`.
- Multiple sources on the same claim: cite each. "X is widely accepted ([[a|2023-04-01]], [[b|2024-09-15]])."
- If a claim's source is already contradicted by a newer source elsewhere in the wiki, surface that in the answer — don't paper over it. Mention that `lint` can audit similar freshness conflicts across the wiki.
- **Never invent a wikilink to a page that doesn't exist** to make an answer look better-cited. Broken wikilinks are corrosive.

## Filing rule

After answering, **offer to file the answer as a new wiki page** if any of these triggers fire:

- (a) The answer cites ≥2 wiki pages.
- (b) The answer introduces a new comparison or synthesis not present in any existing page.
- (c) The answer is multi-paragraph and addresses a non-trivial query.

Filing happens **only with user confirmation.** When offering, suggest a page type (typically `comparison`, `concept`, or `overview`) and a candidate slug. Phrase the offer concretely: "Want me to file this as `wiki/comparisons/rag-vs-wiki.md`?"

**Bias toward offering.** The wiki's value compounds when explorations get filed; one-off chats lose the synthesis.

If the user accepts:
- Use the relevant template from `CLAUDE.md > Page types` (worked examples in `docs/page-type-examples.md`).
- Update `wiki/index.md` (per its HTML-comment conventions).
- Append a log entry to `wiki/log.md` (canonical conventions in its HTML comment):

   ```markdown
   ## [YYYY-MM-DD] query | <one-line question>

   - Question: <full or summarized question>
   - Filed: [[<new-page-slug>]]
   - Pages touched: [[page-1]], [[page-2]], ...
   - Notable: <one line — contradictions surfaced, fresh source needed, etc.>
   ```

If the user declines, don't push. **Don't log declined queries** — the wiki only records what compounds. The answer stays in chat history; if the user wants it back later, they'll re-ask.

## Fallback — wiki has no relevant content

If the wiki has nothing relevant:

1. **Say so explicitly.** Don't paraphrase training-data knowledge as if it came from the wiki. Make the gap visible.
2. **Suggest sources to ingest.** Concrete: "Nothing in the wiki on [topic]. To answer this from the wiki, it would need a source on X, Y, or Z — drop one in `raw/` and re-ask, or share what you have."
3. **Optionally answer from general knowledge** with an explicit `(not in wiki)` caveat so the user can choose to ingest a source and re-ask if they want the answer filed.
