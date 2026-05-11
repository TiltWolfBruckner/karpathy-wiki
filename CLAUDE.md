# CLAUDE.md — Wiki Schema

This file is the operating manual for an LLM agent (Claude Code) maintaining this wiki. It defines:

- the directory layout and what each layer is for
- which files the LLM owns vs. which are read-only
- how pages, links, and citations are formatted

Page types and their templates live in **"Page types"** (added in US-003). Workflows for **ingest**, **query**, and **lint** live in their own sections (added in US-004 / US-005 / US-006). Until those sections exist, ask the user before performing those operations rather than improvising.

If a rule below seems to forbid the action you were about to take — modifying a file in `raw/` directly, inventing a new wikilink format, skipping the index update — stop and confirm with the user. The wiki's value comes from consistency; one-off improvisations corrode it.

The reference design for the whole pattern is `llm-wiki.md` at the repo root. The PRD that scopes this build is `tasks/prd-llm-wiki.md`.

## Architecture

Three layers plus per-source sidecars:

- **`raw/`** — original source documents (articles, PDFs, pasted notes). Immutable. The LLM reads these but never modifies them.
- **`raw/info/`** — LLM-owned sidecars, one per source. Holds metadata (`created`, `indexed`, `updated`) and, for PDFs, extracted text. See "Source sidecars" below.
- **`raw/assets/`** — image and binary attachments referenced from sources. LLM-writable (e.g. when an Obsidian Web Clipper download lands here).
- **`wiki/`** — LLM-generated markdown. Source summaries in `wiki/sources/`, entity pages in `wiki/entities/`, concept pages in `wiki/concepts/`, comparisons in `wiki/comparisons/`, overviews in `wiki/overviews/`, plus `wiki/index.md` and `wiki/log.md`. The LLM owns this layer entirely.
- **`CLAUDE.md`** (this file) — the schema. Co-evolves with use; updates require user direction.

Other directories at repo root: `tasks/` (PRDs and planning) and `.claude/commands/` (project slash commands). The LLM does not modify files under either unless explicitly asked.

## File ownership

| Path | LLM reads | LLM modifies | LLM creates |
|---|---|---|---|
| `raw/<file>` (original) | yes | **never** | never (user drops sources here) |
| `raw/info/<basename>.info.md` | yes | yes | yes |
| `raw/info/<basename>.text.md` | yes | yes | yes (PDFs, on first ingest) |
| `raw/assets/**` | yes | yes | yes |
| `wiki/**` | yes | yes | yes |
| `CLAUDE.md` | yes | only when user asks | only when user asks |
| `tasks/**` | yes | only when user asks | only when user asks |
| `README.md` | yes | only when user asks | — |
| `.claude/commands/**` | yes | only when user asks | only when user asks |

**Rule:** the only files the LLM may write anywhere under `raw/` are the sidecars in `raw/info/` and attachments in `raw/assets/`. Never edit a file the user dropped into `raw/` itself — not to fix a typo, not to add frontmatter, not for any reason.

## Source sidecars

For every original at `raw/<basename>.<ext>` (excluding anything under `raw/info/` or `raw/assets/`), maintain a sidecar at `raw/info/<basename>.info.md` with YAML frontmatter:

```yaml
---
title: <human title from the source if available>
url: <original URL if applicable>
source-type: article | pdf | note | transcript | other
created: YYYY-MM-DD   # source's publication date if known; otherwise same as `indexed`
indexed: YYYY-MM-DD   # date the LLM first read this source
updated: YYYY-MM-DD   # date this sidecar was last written
---
```

The body of the `.info.md` is intentionally blank by default — the human-facing summary lives in `wiki/sources/<slug>.md`, not here. The sidecar exists so the citation, index, and lint workflows have stable per-source metadata to read without re-parsing the source.

**For PDFs**, additionally maintain `raw/info/<basename>.text.md` containing the extracted text. Created on first ingest using Read's `pages` parameter (required for files >10 pages — the Read tool will fail without it). Subsequent reads and `grep` target the `.text.md`, not the original PDF.

**Naming:** the sidecar's basename matches the source's basename exactly. Examples:

| Source path | Sidecar(s) |
|---|---|
| `raw/my-article.md` | `raw/info/my-article.info.md` |
| `raw/notes.txt` | `raw/info/notes.info.md` |
| `raw/foo.pdf` | `raw/info/foo.info.md` + `raw/info/foo.text.md` |

Sidecars are **flat** under `raw/info/`, not nested. This means basenames must be globally unique within `raw/` — if the user drops two files with the same basename, lint will flag the collision.

## Naming conventions

- **Filenames:** kebab-case, lowercase, no spaces. Examples: `tolkien-gateway.md`, `vannevar-bush.md`, `merge-freezes.md`.
- **Page titles:** the H1 (`# `) of each wiki page is the human-readable title. Match the filename slug semantically but capitalize naturally. File `vannevar-bush.md` → `# Vannevar Bush`.
- **One concept per page.** Don't bundle two entities on one page. If a source mentions two distinct entities, create two pages.
- **Filenames must be globally unique within the vault.** Obsidian resolves `[[wikilinks]]` by filename (without extension), so `wiki/entities/foo.md` and `wiki/concepts/foo.md` would collide. If a name overlaps, disambiguate with a qualifier: `foo-person.md`, `foo-concept.md`.
- **Sidecar basenames** mirror the source basename exactly (see "Source sidecars").

## Cross-references

Two link styles, two purposes:

1. **Inter-wiki links** — standard Obsidian wikilink: `[[page-name]]`. Use for any reference between wiki pages (entity ↔ concept, concept ↔ source-summary, etc.). Obsidian renders the link, builds backlinks, and includes it in the graph view.
2. **Source citations on wiki pages** — date-tagged wikilink: `[[source-slug|YYYY-MM-DD]]`. The pipe is Obsidian's alias syntax — the date renders as the link text in Reading view but the link still resolves to `wiki/sources/<source-slug>.md`. The date is the source's `created` (publication) date if known, otherwise its `indexed` date — both read from `raw/info/<basename>.info.md`.

**Why date-tagged citations?** When a newer source contradicts an older claim, the date is visible at the citation site and the `lint` workflow can detect the conflict without parsing prose.

**Examples:**

```markdown
The Memex was proposed by [[vannevar-bush]] in his essay [[as-we-may-think|1945-07-01]].

LLMs make the maintenance burden tractable [[llm-wiki|2026-05-10]] because they
don't get bored of bookkeeping.

For the bundling debate, see [[bundled-vs-split-prs]].
```

**Aliases other than dates are not used for source citations.** Inter-wiki links may use the standard alias form `[[page-name|display text]]` only when natural reading requires it (rare).

## Frontmatter

Every page under `wiki/` has YAML frontmatter at the top:

```yaml
---
type: source-summary | entity | concept | comparison | overview
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources:
  - <source-slug>     # filename of a wiki/sources/<slug>.md page, without .md
  - <source-slug>
---
```

- `type`: one of the page types catalogued in "Page types" (US-003).
- `created`: ISO 8601 date this wiki page was first written. Set once, never edited.
- `updated`: ISO 8601 date this page was last meaningfully edited. Bump on content changes; do not bump for whitespace or formatting.
- `sources`: list of source-summary slugs that contributed to this page. **For navigation and lint — not for freshness.** Freshness lives in the inline date-tagged citations (see "Cross-references").

Source-summary pages (`wiki/sources/<slug>.md`) carry additional fields (`indexed`, `url`, `source-type`) mirroring their sidecar. The full template is defined in "Page types" (US-003).

Pages with missing or malformed frontmatter will be flagged by `lint`.

## Date discipline

- Always use ISO 8601 dates: `YYYY-MM-DD`.
- Never invent past dates. If you don't know a source's publication date, set `created: <today>` to match `indexed`. Don't guess.
- "Today" is the date you're running, not the date the source mentions.
- When updating a sidecar, bump `updated` even if no other field changed (it's how lint knows the sidecar was reviewed).

## Page types

Five types. Each has a fixed location, frontmatter shape, required sections, and a clear "when to create".

Quick reference:

| Type | Location | When to create |
|---|---|---|
| `source-summary` | `wiki/sources/<slug>.md` | Every source ingest. One per `raw/<file>`. |
| `entity` | `wiki/entities/<slug>.md` | A discrete, identifiable thing-in-the-world (person, place, organization, named work, software). |
| `concept` | `wiki/concepts/<slug>.md` | An abstraction — idea, technique, principle, pattern. |
| `comparison` | `wiki/comparisons/<slug>.md` | A side-by-side analysis of 2+ entities/concepts (often filed from a query answer). |
| `overview` | `wiki/overviews/<slug>.md` | A roadmap / "start here" page once a topic cluster has accumulated several pages. |

### Entity vs. concept — decision rule

The most common waffling point. Default question: **does this thing have a proper name and exactly one canonical instance you could point at?**

- **Entity** — yes, one canonical instance. "Vannevar Bush" (a specific person), "Tolkien Gateway" (a specific website), "Memex" (a specific 1945 proposal), "GPT-4" (a specific model), "As We May Think" (a specific essay).
- **Concept** — no, it's an abstraction or category that can have many instances. "Associative trails" (an idea), "personal knowledge management" (a practice), "transformer architecture" (a class of models), "RAG" (a technique).

**Tiebreakers:**

- A specific paper/book is an entity; the technique it describes is a concept. (`rag-paper.md` = entity; `rag.md` = concept.)
- A specific software project is an entity; the pattern it embodies is a concept.
- When in doubt, **default to concept**. Concepts merge cleanly later; entities accumulate identity-specific structure that's hard to undo.

If the same name applies to both an entity and a concept (rare), create both with disambiguating slugs and cross-link them.

### `source-summary`

**Location:** `wiki/sources/<slug>.md` — one per ingested source. Slug matches the source basename (`raw/llm-wiki.md` → `wiki/sources/llm-wiki.md`).

**Frontmatter** — note this type uses `source:` (singular pointer) rather than `sources:`:

```yaml
---
type: source-summary
created: YYYY-MM-DD       # date this summary page was written
updated: YYYY-MM-DD       # bump on meaningful edits
source: <raw-basename>    # filename in raw/ without extension
indexed: YYYY-MM-DD       # mirror of sidecar's `indexed`
url: <if applicable>      # mirror of sidecar's `url`
source-type: article | pdf | note | transcript | other
---
```

**Required sections:**
1. `# <Title of the source>` (H1)
2. **Citation** — where the source lives (`raw/<file>`) and original URL if any
3. **Abstract** — 2–4 sentences on what the source is
4. **Key claims** — bulleted list of the source's main assertions, in source order
5. **Entities** — bulleted list of `[[entity-slug]]` wikilinks for entities the source covers
6. **Concepts** — bulleted list of `[[concept-slug]]` wikilinks for concepts the source covers
7. **Notes** — optional: caveats, unresolved questions, things that don't fit above

**Worked example:**

```markdown
---
type: source-summary
created: 2026-05-10
updated: 2026-05-10
source: llm-wiki
indexed: 2026-05-10
url:
source-type: note
---

# LLM Wiki — A pattern for building personal knowledge bases using LLMs

## Citation

`raw/llm-wiki.md` (no original URL — repo-internal design doc)

## Abstract

Describes a pattern where an LLM agent incrementally builds and maintains a persistent
markdown wiki from raw source documents, instead of doing RAG from scratch on every
query. Three layers (raw, wiki, schema) plus operations for ingest, query, and lint.

## Key claims

- Maintenance burden, not reading or thinking, is what kills human-maintained wikis.
- A persistent wiki accumulates synthesis; RAG re-derives it on every query.
- The LLM should own all wiki writes; the human curates sources and asks questions.
- `index.md` + `log.md` plus grep is sufficient retrieval at moderate scale.

## Entities

- [[obsidian]]
- [[claude-code]]
- [[tolkien-gateway]]
- [[vannevar-bush]]

## Concepts

- [[memex]]
- [[rag]]
- [[personal-knowledge-management]]

## Notes

The reference doc explicitly leaves directory layout, conventions, and tooling to the
implementer. Many decisions in this wiki's CLAUDE.md are choices, not the only path.
```

### `entity`

**Location:** `wiki/entities/<slug>.md`

**When to create:** when a source mentions a thing-in-the-world that warrants its own page (referenced multiple times across sources, or central to a source). Don't pre-create entities the wiki doesn't yet need.

**Frontmatter:**

```yaml
---
type: entity
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources:
  - <source-slug>
entity-kind: person | place | organization | work | software | other
aliases: [<other names this entity goes by>]   # optional
---
```

**Required sections:**
1. `# <Entity Name>` (H1, naturally capitalized)
2. **Summary** — 1–2 paragraph definition / "what is this thing"
3. **Key facts** — bulleted properties (dates, locations, roles as relevant)
4. **Related** — `[[wikilinks]]` to related entities and concepts, organized as **Entities:** / **Concepts:** sub-bullets
5. **Sources** — date-tagged citations `[[source-slug|YYYY-MM-DD]]`, one per supporting source

**Worked example:**

```markdown
---
type: entity
created: 2026-05-10
updated: 2026-05-10
sources:
  - llm-wiki
entity-kind: person
aliases: [Bush, V. Bush]
---

# Vannevar Bush

## Summary

American engineer and science administrator (1890–1974). Best known to the PKM community
for his 1945 essay "As We May Think," which proposed the Memex — a personal knowledge
store with associative trails between documents.

## Key facts

- Born 1890, died 1974
- Director of the U.S. Office of Scientific Research and Development during WWII
- Authored "As We May Think" in *The Atlantic*, July 1945

## Related

**Entities:**
- [[as-we-may-think]] — his 1945 essay

**Concepts:**
- [[memex]] — the personal knowledge store he proposed
- [[associative-trails]]

## Sources

- [[llm-wiki|2026-05-10]] — references Bush's vision as a precursor to the LLM-wiki pattern
```

### `concept`

**Location:** `wiki/concepts/<slug>.md`

**When to create:** when a source introduces or significantly uses an abstract idea, technique, or pattern worth a standalone page. Same restraint as entities — don't pre-create.

**Frontmatter:**

```yaml
---
type: concept
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources:
  - <source-slug>
---
```

**Required sections:**
1. `# <Concept Name>` (H1)
2. **Definition** — 1–3 sentences. What is this idea?
3. **Why it matters** — 1 paragraph on the concept's significance / where it appears
4. **Related** — `[[wikilinks]]` (Entities / Concepts sub-bullets)
5. **Sources** — date-tagged citations

**Worked example:**

```markdown
---
type: concept
created: 2026-05-10
updated: 2026-05-10
sources:
  - llm-wiki
---

# Memex

## Definition

A hypothetical personal knowledge device, proposed by [[vannevar-bush]] in 1945, that
would store a person's books, records, and communications and let them follow associative
trails between documents.

## Why it matters

The Memex is the spiritual ancestor of personal knowledge management systems, hypertext,
and — per [[llm-wiki|2026-05-10]] — the LLM-maintained wiki pattern. Bush correctly
identified that the connections between documents matter as much as the documents
themselves; what he couldn't solve was who maintains the connections.

## Related

**Entities:**
- [[vannevar-bush]]
- [[as-we-may-think]]

**Concepts:**
- [[associative-trails]]
- [[personal-knowledge-management]]

## Sources

- [[llm-wiki|2026-05-10]]
```

### `comparison`

**Location:** `wiki/comparisons/<slug>.md`

**When to create:** when a query answer compares 2+ entities/concepts in a way the user wants preserved (per the filing rule in the Query workflow), or when a source explicitly compares N things. Slug names the comparison: `rag-vs-fine-tuning.md`, `memex-vs-web.md`.

**Frontmatter:**

```yaml
---
type: comparison
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources:
  - <source-slug>
compares:
  - <slug-of-thing-1>
  - <slug-of-thing-2>
---
```

**Required sections:**
1. `# <Thing A> vs. <Thing B>` (H1)
2. **What's compared** — bulleted list of `[[wikilinks]]` to the things being compared
3. **Comparison** — markdown table with axes as rows and the things as columns. If a table doesn't fit, use one `### <axis>` heading per axis with prose underneath.
4. **Tradeoffs** — 1–2 paragraphs on when to prefer which
5. **Sources** — date-tagged citations

**Worked example:**

```markdown
---
type: comparison
created: 2026-05-10
updated: 2026-05-10
sources:
  - llm-wiki
compares:
  - rag
  - llm-wiki-pattern
---

# RAG vs. LLM-Maintained Wiki

## What's compared

- [[rag]] — retrieval at query time from raw sources
- [[llm-wiki-pattern]] — incremental compilation into a persistent wiki

## Comparison

| Axis | RAG | LLM-maintained wiki |
|---|---|---|
| When work happens | Per-query | At ingest time, then amortized |
| Synthesis | Re-derived each query | Compiled once, kept current |
| Cross-references | Implicit in embeddings | Explicit `[[wikilinks]]` |
| Human inspection | Embedding chunks (opaque) | Markdown pages (readable) |
| Maintenance | None — always re-derives | Required, but the LLM does it |

## Tradeoffs

RAG wins when the corpus is huge, the queries are unpredictable, and you don't care about
human inspection of intermediate state. The wiki pattern wins when accumulation matters —
when you want to ask the same question in six months and get a richer answer because of
everything that's been read between now and then.

## Sources

- [[llm-wiki|2026-05-10]]
```

### `overview`

**Location:** `wiki/overviews/<slug>.md`

**When to create:** when a topic cluster has accumulated ~5+ pages and a roadmap helps. Don't pre-create overviews — wait until the volume justifies one.

**Frontmatter:**

```yaml
---
type: overview
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources:
  - <source-slug>
covers:
  - <slug-of-page-1>
  - <slug-of-page-2>
---
```

**Required sections:**
1. `# <Topic>` (H1)
2. **Scope** — 1–2 sentences on what this overview covers (and what it doesn't)
3. **Reading order** — ordered list of `[[wikilinks]]` with a one-line annotation each
4. **Open questions** — bulleted list of things the wiki doesn't yet answer about this topic
5. **Sources** — date-tagged citations

**Worked example:**

```markdown
---
type: overview
created: 2026-05-10
updated: 2026-05-10
sources:
  - llm-wiki
covers:
  - vannevar-bush
  - memex
  - associative-trails
  - personal-knowledge-management
  - llm-wiki-pattern
---

# Personal Knowledge Management — Memex to LLM Wikis

## Scope

A reading roadmap from Vannevar Bush's 1945 Memex proposal to today's LLM-maintained
wikis. Covers the conceptual lineage; does not cover commercial PKM tooling (Notion,
Roam, Obsidian as products).

## Reading order

1. [[vannevar-bush]] — the originator of the personal-curation vision
2. [[as-we-may-think|1945-07-01]] — his 1945 essay (start here for primary source)
3. [[memex]] — the device he proposed
4. [[associative-trails]] — the navigation primitive Bush couldn't solve
5. [[personal-knowledge-management]] — the modern practice
6. [[llm-wiki-pattern]] — how LLMs make Bush's vision feasible

## Open questions

- What did the early hypertext systems (Xanadu, NLS) get right that's been forgotten?
- How do LLM-maintained wikis compare to community-maintained ones (Wikipedia, fan wikis)?

## Sources

- [[llm-wiki|2026-05-10]]
```

## Ingest workflow

Triggered by either `/ingest <path>` (the slash command in `.claude/commands/ingest.md`) or natural language ("ingest this", "file this article", "process raw/foo.md"). Either way, the workflow below is identical.

**Pre-flight checks:**

- If the trigger gives no path, ask the user which file to ingest.
- If the path is outside `raw/`, ask the user before proceeding — usually the right move is to copy or move the file into `raw/` first, then ingest.
- If the basename collides with an existing file in `raw/` (different extension, same basename), stop and ask. Sidecars are flat under `raw/info/` and basenames must be unique.

### Steps

1. **Read the source.**
   - Markdown / text (`.md`, `.txt`, clipped articles): read directly with the Read tool.
   - PDF: read with Read's `pages` parameter (required for files >10 pages — Read fails without it). For PDFs >20 pages, read in batches.
   - For unfamiliar source types, ask the user before processing.

2. **Create or update the sidecar at `raw/info/<basename>.info.md`.**
   - First ingest: write the full frontmatter (see "Source sidecars"). `created` = source's publication date if you can read it off the source itself (article byline, paper date, etc.), otherwise = today. `indexed` = today. `updated` = today. Fill `title`, `url`, `source-type` when available.
   - Re-ingest: bump `updated` to today. Touch other fields only if the source itself changed.
   - **For PDFs**, also write `raw/info/<basename>.text.md` containing the extracted text (first ingest only, unless the PDF was replaced). All subsequent reads and `grep` target this `.text.md`, not the PDF.

3. **Discuss key takeaways with the user.** Before writing anything under `wiki/`, summarize what you read in 3–6 bullets: the source's main claims, what entities/concepts it covers, any surprises or contradictions with existing wiki pages. Wait for the user's reaction — they may want to emphasize, deemphasize, or skip parts.

4. **Write the source-summary page** at `wiki/sources/<slug>.md`, where `<slug>` matches the source basename. Follow the template in "Page types > source-summary" — required sections are title, citation, abstract, key claims, entities, concepts, optional notes; frontmatter uses `source:` (singular) plus `indexed`, `url`, `source-type`.

5. **Identify entity/concept pages to create or update.** Walk through the entities and concepts the source covers. For each:
   - **Page exists, source agrees:** add a new `[[source-slug|YYYY-MM-DD]]` citation in the Sources section and (where relevant) in the body. Update prose if the new source adds detail. Bump `updated:` in frontmatter.
   - **Page does not exist, the entity/concept warrants one:** create it using the template from "Page types". Cite the new source.
   - **Page exists, source contradicts an existing claim:** stop. See "Handling contradictions" below.

6. **Update `wiki/index.md`.** Add or update entries for any new or modified pages. Section order is per "Page types" (Sources / Entities / Concepts / Comparisons / Overviews). Within each section, alphabetical by slug. Entry format: `- [[slug]] — one-line summary`.

7. **Append a log entry to `wiki/log.md`.** Format (full conventions defined in US-007):

   ```markdown
   ## [YYYY-MM-DD] ingest | <Source Title>

   - Sidecar: `raw/info/<basename>.info.md`
   - Summary: [[<slug>]]
   - Pages touched: [[page-1]], [[page-2]], ...
   - Notable: <one line on anything unusual — contradictions resolved, new entities discovered, etc.>
   ```

### Handling contradictions

When a new source's claim contradicts an existing wiki claim:

1. **Stop before writing anything to `wiki/` for the contradicted page.** Surface the contradiction to the user: which claim, which page, which old source it relies on (with date), which new source contradicts it (with date). Read both citations and quote the relevant lines.
2. **Ask the user how to resolve.** Three patterns:
   - **Replace:** the new source supersedes the old. Update the page text; replace the old `[[old-source|YYYY-MM-DD]]` citation with `[[new-source|YYYY-MM-DD]]`. The old `raw/` file and its sidecar are preserved for reference — only the citation moves.
   - **Both:** the page now notes that sources disagree. Cite both with their dates and show the disagreement explicitly.
   - **Keep old:** the user judges the old claim more credible. Add a brief note that a newer source disagrees; cite both.
3. **Log the resolution** in the ingest log entry's `Notable:` line, e.g. "Resolved contradiction on [[memex]]: replaced [[bush-1945|1945-07-01]] citation with [[reanalysis|2024-11-02]]".

Never silently overwrite a contradicted claim. The whole point of date-tagged citations is that disagreements are surfaced, not papered over.

### Source types — quick reference

| Source type | Read with | `.text.md` sidecar? |
|---|---|---|
| Clipped markdown article (`.md`) | Read tool, direct | no |
| Pasted text or note (`.txt`, `.md`) | Read tool, direct | no |
| PDF | Read tool with `pages` parameter (required for >10pp) | **yes** — write extracted text to `raw/info/<basename>.text.md` on first ingest |

## Sections under construction

Added in subsequent user stories — until they exist, ask the user before doing the corresponding operation:

- **Query workflow** (US-005) — how to retrieve from the wiki and cite sources.
- **Lint workflow** (US-006) — health checks and the freshness-conflict detector.
