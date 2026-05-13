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
- **`raw/notion/`** — LLM-owned cache of Notion pages fetched via the Notion MCP. One markdown file per ingested Notion page; overwritten in place on re-ingest (never accumulated). Populated by `/ingest-notion`; never edited by hand. See "Ingest workflow > Notion sources".
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
| `raw/notion/<file>` | yes | yes (overwrite on re-ingest) | yes (via `/ingest-notion` only) |
| `notion-index.md` (repo root) | yes | yes | yes (on first `/ingest-notion`) |
| `wiki/**` | yes | yes | yes |
| `CLAUDE.md` | yes | only when user asks | only when user asks |
| `tasks/**` | yes | only when user asks | only when user asks |
| `README.md` | yes | only when user asks | — |
| `.claude/commands/**` | yes | only when user asks | only when user asks |

**Rule:** the only files the LLM may write anywhere under `raw/` are the sidecars in `raw/info/`, attachments in `raw/assets/`, and the Notion cache in `raw/notion/`. Never edit a file the user dropped into `raw/` directly — not to fix a typo, not to add frontmatter, not for any reason. Files in `raw/notion/` are LLM-managed and overwritten in place by `/ingest-notion`; the user does not drop files there.

## Source sidecars

**Sidecar** = a separate file that carries metadata or derived content about a primary file, kept apart so the primary stays byte-identical to what arrived. (Convention borrowed from data engineering — e.g. camera RAW files + `.xmp` metadata sidecars.) In this wiki, originals live in `raw/` and every sidecar lives flat under `raw/info/`, paired by basename.

For every original at `raw/<basename>.<ext>` (excluding anything under `raw/info/` or `raw/assets/`), maintain a sidecar at `raw/info/<basename>.info.md` with YAML frontmatter:

```yaml
---
title: <human title from the source if available>
url: <original URL if applicable>
source-type: text | pdf | transcript | image | other | notion   # broad structural kind
source-genre: <editorial label>                        # see suggested values below
created: YYYY-MM-DD   # source's publication date if known; otherwise same as `indexed`
indexed: YYYY-MM-DD   # date the LLM first read this source
updated: YYYY-MM-DD   # date this sidecar was last written

# Optional — only set for source-type: notion (see "Ingest workflow > Notion sources"):
notion-page-id: <uuid>            # Notion's stable page identifier, used for re-ingest lookup
notion-last-edited: YYYY-MM-DDTHH:MM:SSZ   # Notion's last_edited_time at ingest — the drift baseline used by /lint-notion
---
```

The `source-type` / `source-genre` split is intentional:

- **`source-type`** is the broad structural kind (closed enum). It tells the workflow how to read the source — `text`/markdown is read directly, `pdf` needs the Read tool's `pages` parameter, `transcript` means the text is derived from audio/video, `image` is image-only material, `notion` is fetched live from Notion via the MCP and cached under `raw/notion/`, `other` is the escape hatch. Allowed values: `text | pdf | transcript | image | other | notion`.
- **`source-genre`** is the editorial label (free-form, with suggestions). It tells the human what kind of *content* this is. Common values: `article | essay | paper | book | design-doc | spec | note | talk | podcast-transcript | video-transcript | social-post | notion-page | other`. Free-form so unusual sources (e.g. `lab-notebook-entry`, `legal-memo`) aren't forced into `other` — but prefer a listed value when it fits.

The body of the `.info.md` is intentionally blank by default — the human-facing summary lives in `wiki/sources/<slug>.md`, not here. The sidecar exists so the citation, index, and lint workflows have stable per-source metadata to read without re-parsing the source.

**For PDFs**, additionally maintain `raw/info/<basename>.text.md` containing the extracted text. Created on first ingest using Read's `pages` parameter (required for files >10 pages — the Read tool will fail without it). Subsequent reads and `grep` target the `.text.md`, not the original PDF.

**Naming:** the sidecar's basename matches the source's basename exactly. Examples:

| Source path | Sidecar(s) |
|---|---|
| `raw/my-article.md` | `raw/info/my-article.info.md` |
| `raw/notes.txt` | `raw/info/notes.info.md` |
| `raw/foo.pdf` | `raw/info/foo.info.md` + `raw/info/foo.text.md` |
| `raw/notion/some-notion-page.md` | `raw/info/some-notion-page.info.md` |

Sidecars are **flat** under `raw/info/`, not nested — even when the source lives in a subdirectory like `raw/notion/`. This means basenames must be globally unique within `raw/` (across all subdirectories). If the user drops two files with the same basename — or a Notion slug collides with an existing source — lint will flag the collision.

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

Source-summary pages (`wiki/sources/<slug>.md`) carry additional fields (`indexed`, `url`, `source-type`, `source-genre`) mirroring their sidecar. The full template is defined in "Page types".

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
source: <raw-basename>    # filename in raw/ without extension (Notion sources: same as the slug used under raw/notion/)
indexed: YYYY-MM-DD       # mirror of sidecar's `indexed`
url: <if applicable>      # mirror of sidecar's `url`
source-type: text | pdf | transcript | image | other | notion   # mirror of sidecar's `source-type`
source-genre: <editorial label>                                  # mirror of sidecar's `source-genre`
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

**Index summary** derives from the **Abstract** section: one line (~120 chars), first sentence of Abstract; abridge if needed but don't substantively paraphrase.

**Worked example:**

```markdown
---
type: source-summary
created: 2026-05-10
updated: 2026-05-10
source: llm-wiki
indexed: 2026-05-10
url:
source-type: text
source-genre: design-doc
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

**Index summary** derives from the **Summary** section: one line (~120 chars), first sentence; abridge if needed.

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

**Index summary** derives from the **Definition** section: one line (~120 chars), first sentence; abridge if needed.

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

**Index summary** derives from the **Tradeoffs** section: one line (~120 chars), first sentence of Tradeoffs; abridge if needed.

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

**Index summary** derives from the **Scope** section: one line (~120 chars), first sentence; abridge if needed.

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

**For Notion pages** the trigger is `/ingest-notion <notion-url-or-id>` and the fetch + sidecar steps differ — see "Notion sources" below. From step 3 onward (discussing takeaways, writing the source-summary, updating entity/concept pages, `wiki/index.md`, `wiki/log.md`) the workflow is identical to the file-based path.

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

3. **Discuss key takeaways with the user.** Before writing anything under `wiki/`, summarize what you read in 3–6 bullets: the source's main claims, what entities/concepts it covers, any surprises or contradictions with existing wiki pages. **Wait for the user's reaction — the pause is canonical, not optional.** They may want to emphasize, deemphasize, or skip parts. Non-interactive batch runs only happen when the user has explicitly directed them in the session (e.g. the US-008 validation skip was a one-off at user direction, not a workflow mode).

4. **Write the source-summary page** at `wiki/sources/<slug>.md`, where `<slug>` matches the source basename. Follow the template in "Page types > source-summary" — required sections are title, citation, abstract, key claims, entities, concepts, optional notes; frontmatter uses `source:` (singular) plus `indexed`, `url`, `source-type`.

5. **Identify entity/concept pages to create or update.** Walk through the entities and concepts the source covers. For each:
   - **Page exists, source agrees:** add a new `[[source-slug|YYYY-MM-DD]]` citation in the Sources section and (where relevant) in the body. Update prose if the new source adds detail. Bump `updated:` in frontmatter.
   - **Page does not exist, the entity/concept warrants one:** create it using the template from "Page types". Cite the new source.
   - **Page exists, source contradicts an existing claim:** stop. See "Handling contradictions" below.

6. **Update `wiki/index.md`.** Add or update entries for any new or modified pages. Section order: Sources / Entities / Concepts / Comparisons / Overviews. Alphabetical by slug within each section. Entry format: `- [[slug]] — one-line summary`. **Canonical conventions in `wiki/index.md`'s HTML comment** — re-read it before each update.

7. **Append a log entry to `wiki/log.md`.** Newest entries go at the bottom. Format (canonical conventions in `wiki/log.md`'s HTML comment):

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
| Notion page | `mcp__claude_ai_Notion__notion-fetch` (Notion MCP) — body is flattened to markdown and written to `raw/notion/<slug>.md` | no — the cached `.md` under `raw/notion/` *is* the readable form |

### Notion sources

Notion pages are a second input track. Triggered by `/ingest-notion <notion-url-or-id>` (the slash command in `.claude/commands/ingest-notion.md`) or natural-language equivalents ("ingest this Notion page", "pull this from Notion"). The bulk of the workflow is identical to the file-based path — only the source-fetch and sidecar-creation steps differ, plus one extra step that keeps the Notion-side index page current. After those Notion-specific steps, hand off to step 3 of the base workflow.

**Why a separate variant?** Notion pages live in the cloud, not under `raw/`. The LLM fetches them via the Notion MCP, caches the markdown body under `raw/notion/`, writes a sidecar at `raw/info/<slug>.info.md`, and (for traceability) appends an entry to a single **Notion index page** in the user's workspace. From step 3 onward the cached `raw/notion/<slug>.md` is treated like any other raw source — the wiki layer doesn't care that it came from Notion.

**Bootstrap — the Notion index page**

A single Notion page tracks every Notion document this wiki has ingested. Its location is stored in `notion-index.md` at the repo root (gitignored — machine-specific):

```yaml
---
notion-index-page-id: <uuid>
notion-index-page-url: https://www.notion.so/...
---

# Notion ingest index

The Notion page at the URL above is the registry of every Notion document
this wiki has ingested. Maintained by `/ingest-notion`.
```

If `notion-index.md` is missing or has an empty `notion-index-page-id`, **stop and ask the user for the URL of the Notion page they want to use as the index**. Write the file, then proceed. **Do not auto-create the Notion page** — the user picks where in their workspace it lives.

**Pre-flight (Notion sources only):**

- If `$ARGUMENTS` is empty, ask which Notion page to ingest.
- Resolve `$ARGUMENTS` to a Notion page ID. Accepted forms: full Notion URL, bare UUID, or share link. If unresolvable, stop and ask.
- Read `notion-index.md`. If missing or empty, run the bootstrap above.
- Re-ingest detection: `grep -l "notion-page-id: <uuid>" raw/info/*.info.md`. If a sidecar with that page ID exists, this is a re-ingest — use the **overwrite path** in step 2 below.

**Filename convention — slug is frozen at first ingest**

One file per Notion page. Ever. The slug derived from the Notion title at first ingest becomes the page's permanent identifier in this wiki — `raw/notion/<slug>.md` and `raw/info/<slug>.info.md` and (downstream) `wiki/sources/<slug>.md`. **The slug never changes** — not when the Notion title is renamed, not on re-ingest, not on lint. This keeps every `[[slug|YYYY-MM-DD]]` citation across the wiki stable forever. The Notion title is just a *label* stored in the sidecar's `title:` field; it can drift independently of the slug.

**Notion-specific steps (replacing steps 1–2 of the base workflow):**

1. **Fetch the page via `mcp__claude_ai_Notion__notion-fetch`.** Capture: page title, body, URL, page ID, `last_edited_time`, and `created_time` if the MCP exposes it. Flatten the body to plain markdown (most Notion blocks have a direct markdown equivalent; for anything unrecognized, preserve as a fenced HTML block and note in the source-summary's "Notes" section later).

2. **Write the cached source at `raw/notion/<slug>.md`:**

   - **First ingest** (no sidecar matched the page ID in pre-flight): slugify the current Notion title (kebab-case, lowercase, ASCII-only), then write `raw/notion/<slug>.md` with the fetched body. If the chosen slug collides with an existing basename anywhere under `raw/`, append a short qualifier (`<slug>-notion`) and proceed.
   - **Re-ingest** (sidecar exists for this page ID): use the **existing slug** from the matched sidecar, regardless of whether the current Notion title would slugify differently. **Overwrite** `raw/notion/<slug>.md` with the fresh body. No version suffixes, no second file, no rename. Exactly one cached file per Notion page exists when this step finishes.

3. **Write or update the sidecar at `raw/info/<slug>.info.md`:**

   ```yaml
   ---
   title: <current Notion page title>
   url: <current Notion URL>
   source-type: notion
   source-genre: notion-page
   notion-page-id: <uuid>
   notion-last-edited: <Notion's last_edited_time, ISO 8601>
   created: <Notion's created_time if exposed, else today>
   indexed: <first-ingest date — preserved across re-ingests>
   updated: <today>
   ---
   ```

   On re-ingest, refresh `title`, `url`, `notion-last-edited`, and `updated`. Preserve `indexed` and `created` (they record first contact, not the latest). Bump `updated` even if the body came back byte-identical — the sidecar is "reviewed as of today".

4. **Append an entry to the Notion index page** via `mcp__claude_ai_Notion__notion-update-page`. Bullet format:

   ```
   - <Page Title> — ingested YYYY-MM-DD → wiki/sources/<slug>.md
     (link: <original notion url>)
   ```

   Append-only. Don't try to de-duplicate prior entries — a second ingest just adds a second line, and the most recent one is the canonical "current" status (mirrors how `wiki/log.md` works).

**Hand off** to step 3 of the base workflow ("Discuss key takeaways with the user"). Everything from there — source-summary at `wiki/sources/<slug>.md`, entity/concept updates, `wiki/index.md`, `wiki/log.md` — is identical to file-based ingest.

**Title drift is not a filename rename.** If the user renames the Notion page after ingest, the next `/ingest-notion <url>` refreshes the `title:` field in the sidecar but does **not** rename `raw/notion/<slug>.md` or `wiki/sources/<slug>.md`. The slug is the wiki's stable handle; the title is metadata. `/lint-notion` reports title drift as informational only.

## Query workflow

Triggered by `/query <question>` (the slash command in `.claude/commands/query.md`) or any natural-language question against the wiki. Same workflow either way, whether the question is a one-liner ("when did Bush propose the Memex?") or open-ended ("how do LLM-maintained wikis differ from RAG?").

If the question is genuinely outside the wiki's scope (small talk, unrelated tasks), answer normally — don't force a wiki retrieval pass for everything.

### Steps

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

### Citation rules in answers

- Every wiki page referenced: `[[page-slug]]`. Obsidian renders the link.
- Every source cited: `[[source-slug|YYYY-MM-DD]]` — date is the source's `created` if known, otherwise `indexed`.
- Multiple sources on the same claim: cite each. "X is widely accepted ([[a|2023-04-01]], [[b|2024-09-15]])."
- If a claim's source is already contradicted by a newer source elsewhere in the wiki, surface that in the answer — don't paper over it. Mention that `lint` can audit similar freshness conflicts across the wiki.
- **Never invent a wikilink to a page that doesn't exist** to make an answer look better-cited. Broken wikilinks are corrosive.

### Filing rule

After answering, **offer to file the answer as a new wiki page** if any of these triggers fire:

- (a) The answer cites ≥2 wiki pages.
- (b) The answer introduces a new comparison or synthesis not present in any existing page.
- (c) The answer is multi-paragraph and addresses a non-trivial query.

Filing happens **only with user confirmation.** When offering, suggest a page type (typically `comparison`, `concept`, or `overview`) and a candidate slug. Phrase the offer concretely: "Want me to file this as `wiki/comparisons/rag-vs-wiki.md`?"

**Bias toward offering.** The wiki's value compounds when explorations get filed; one-off chats lose the synthesis.

If the user accepts:
- Use the relevant template from "Page types".
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

### Fallback — wiki has no relevant content

If the wiki has nothing relevant:

1. **Say so explicitly.** Don't paraphrase training-data knowledge as if it came from the wiki. Make the gap visible.
2. **Suggest sources to ingest.** Concrete: "Nothing in the wiki on [topic]. To answer this from the wiki, it would need a source on X, Y, or Z — drop one in `raw/` and re-ask, or share what you have."
3. **Optionally answer from general knowledge** with an explicit `(not in wiki)` caveat so the user can choose to ingest a source and re-ask if they want the answer filed.

## Lint workflow

Triggered by `/lint` (the slash command in `.claude/commands/lint.md`) or a natural-language request: "lint the wiki", "run a lint pass", "check the wiki for issues". For the opt-in staleness check, the user invokes `/lint staleness` or natural-language equivalents like "lint with staleness" / "lint and check for old pages".

**Lint never modifies files on its own.** It surfaces findings and proposed fixes; the user confirms what to apply.

**`/lint` is offline-only.** It never makes Notion network calls. Cloud freshness for ingested Notion pages (content drift, title drift, deletion, etc.) lives entirely in the separate `/lint-notion` workflow below — that command is user-invoked when Notion sources are suspected stale.

### Default checks

Run all of these and produce one report section per check (even if empty — empty sections confirm the check ran).

1. **Contradictions between pages.** Pages that make incompatible claims about the same entity/concept. Detect by reading related pages (use the index plus cross-references); flag when claims about the same thing diverge.

2. **Freshness conflicts.** Wiki pages where a date-tagged citation `[[old-source|YYYY-MM-DD]]` is contradicted by a newer date-tagged citation on the same claim — either elsewhere on the same page, or on a related page. The dates make this detectable without parsing prose. Flag the page, both sources, and the date delta.

3. **Orphan pages.** Wiki pages with no inbound `[[wikilinks]]`. Detect by enumerating all page slugs, then `grep`-ing the rest of the wiki for each. Source-summary pages are partially exempt (often only linked from a single entity/concept page) but should be flagged when no entity/concept references them at all.

4. **Missing pages — important concepts/entities mentioned but unwritten.** Run `python3 scripts/lint-wikilinks.py wiki/ --check missing-pages`. A finding fires when a wikilink in a source-summary's `## Entities` or `## Concepts` H2 section points to a slug with no matching page anywhere under `wiki/`. Reported once per target, with every referring location listed.

5. **Missing cross-references.** Pages that mention a known entity/concept in prose without `[[wikilink]]`-ing it. Heuristic: for each existing page slug, grep the rest of the wiki for the corresponding natural-language name; if a match has no surrounding wikilink, flag.

6. **Frontmatter validity.** Every wiki page has YAML frontmatter with the fields required by its `type` (see "Page types"). Check: `type` is one of the five values, `created`/`updated` are valid ISO 8601 dates, `sources:` (or `source:` for source-summary) references slugs that exist.

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

### Broken vs. missing-page dedup

Checks 4 (missing pages) and 7 (broken wikilinks) return **disjoint** findings. A wikilink target classified as `missing-page` does not also fire `broken` for its other occurrences. The dedup is **per-target**, not per-occurrence: even if `[[X]]` is broken on three different pages, if any one of those occurrences sits inside a source-summary's `## Entities` or `## Concepts` H2 section, all three get rolled into a single `missing-page` finding (with all referring locations listed). The Python tool enforces this in its classifier; the lint report should not show the same target in both sections.

Rationale: one action ("create the page") resolves the missing-page *and* every related broken-link occurrence. Reporting both is redundant noise.

### Optional: staleness check

Only when invoked as `lint with staleness` (or equivalent NL — "lint including stale", "lint and check for old pages"). **Default lint does not include this** — it grows noisy as the wiki ages.

- Flag any wiki page whose `updated:` frontmatter is more than **6 months** ago, as a candidate for review.
- Finding format: page path, `updated:` date, age, suggested action ("re-read against newer sources" or "confirm still accurate").
- Staleness alone is not a defect — just a prompt to look.

### Report format

A single markdown report, one H2 per check (even when empty). Within each H2, one bullet per finding with:

- **File path(s)** — affected page(s), relative to repo root
- **One-line description** — what's wrong
- **Suggested fix** — concrete action the user can approve

Shape:

```markdown
# Wiki lint report — 2026-05-10

## Contradictions

(none)

## Freshness conflicts

- `wiki/concepts/memex.md`
  - Cites `[[bush-1945|1945-07-01]]` for the trail-following claim, but `[[modern-reanalysis|2024-11-02]]` (also cited on the page) disputes it.
  - **Suggested fix:** Resolve per "Handling contradictions" — Replace, Both, or Keep old.

## Orphan pages

- `wiki/entities/obscure-thing.md`
  - No inbound wikilinks from any other page.
  - **Suggested fix:** Link from a related page, merge into an existing one, or delete.

## Missing pages

- `[[associative-trails]]` — no wiki page exists for this slug
  Referenced from:
    - `wiki/sources/llm-wiki.md:14` (Entities/Concepts section — this occurrence is what triggers the classification)
    - `wiki/concepts/memex.md:22`   (would have been a separate broken-wikilink finding; per-target dedup rolls it into this entry)
  - **Suggested fix:** Create a `concept` page using the template in "Page types > concept". One file resolves all referring locations.

## Missing cross-references

(none)

## Frontmatter validity

(none)

## Broken wikilinks

- `wiki/concepts/memex.md:18`  `[[as-we-may-think]]`
  - Target doesn't resolve. The occurrence sits in the page's "Related" section, not a source-summary's `## Entities` or `## Concepts` H2 — so it stays in the broken-wikilinks category (per "Broken vs. missing-page dedup" above).
  - **Suggested fix:** Create `wiki/entities/as-we-may-think.md` (Bush's essay is an entity per the entity-vs-concept rule), or fix the link target.

## Missing source sidecars

- `raw/some-article.md`
  - No `raw/info/some-article.info.md`.
  - **Suggested fix:** Run `/ingest raw/some-article.md` to create the sidecar (and the wiki summary if not yet ingested).
```

### After producing the report

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

### Performance note

At small scale (tens of pages) run checks sequentially. At larger scale, the file-system checks (broken wikilinks, missing sidecars) can run in parallel with the prose-reading checks (contradictions, missing cross-references) since they touch disjoint inputs.

## Lint-notion workflow

Triggered by `/lint-notion` (the slash command in `.claude/commands/lint-notion.md`) or natural-language equivalents ("lint notion sources", "check if Notion pages are stale", "audit notion freshness"). This is the **cloud-freshness pass** for Notion sources — distinct from the offline `/lint` above.

**Like `/lint`, `/lint-notion` never modifies files.** It produces a report; the user fixes findings by re-running `/ingest-notion <url>` on the affected page (which overwrites the cached copy in place — see "Ingest workflow > Notion sources > Filename convention").

**Two modes:**

- **Inventory mode** (`/lint-notion` with no argument) — enumerate every sidecar under `raw/info/` with `source-type: notion` and check each against Notion.
- **Single-page mode** (`/lint-notion <notion-url-or-id>`) — resolve the argument to a page ID, find its sidecar via `grep -l "notion-page-id: <uuid>" raw/info/*.info.md`, and check just that page. The escape hatch for "I edited one Notion doc, don't crawl my whole inventory."

  If the page ID isn't found in any sidecar, stop and tell the user the page hasn't been ingested (suggest `/ingest-notion <url>` first).

**Performance note.** Every Notion-sourced page is one Notion MCP `notion-fetch` call (metadata-only if the MCP supports it; full fetch otherwise). Inventory mode costs N round-trips at N ingested pages — non-trivial at scale. Single-page mode is one call. `/lint-notion` never runs on a schedule; it is purely user-invoked.

### Drift modes — what's checked

A locally-cached Notion source goes stale the moment the page is edited in Notion. The local copy is a snapshot, not a live mirror.

| # | Drift mode | Detect via | Severity | Default? |
|---|---|---|---|---|
| 1 | **Content drift** — page body edited in Notion | current `last_edited_time` > sidecar's `notion-last-edited` | High — wiki claims cite a stale snapshot | **Yes** |
| 2 | **Title drift** — page renamed | current Notion title ≠ sidecar `title` | Low — informational; slug is frozen so no filename changes | **Yes** (informational) |
| 3 | **Deletion / archival** — page gone | fetch returns "not found" or `archived: true` | High — citation dangles | **Yes** |
| 4 | **Permissions revoked** — integration lost access | fetch returns 401/403 | Medium — distinct from deletion; may resolve when the user re-grants access | **Yes** (separate category from deleted) |
| 5 | **URL change** — page moved, slug regenerated | current URL ≠ sidecar `url`, but the page ID still resolves | Low — cosmetic; the stable ID means fetches still work | Opt-in (`--check urls`) |
| 6 | **Index page drift** — registry page hand-edited | parse the index page; compare its bullet list against expected entries (one per Notion-sourced sidecar) | Low — append-only design tolerates this | Opt-in (`--check index`) |
| 7 | **Wiki-side link rot from index page** — an entry's `→ wiki/sources/<slug>.md` no longer exists locally | for each index entry, check the referenced wiki file | Low | **Yes** (cheap, runs once on the index page itself) |

**Out of scope** (future work, not in v1):

- **DB-properties drift** — Notion pages can carry database properties (Status, Tags, Date) that change independently of the body. Would require snapshotting properties in the sidecar at ingest, which we don't do.
- **Embedded sub-page / synced-block drift** — Notion pages can embed child databases, synced blocks, linked pages. Detecting drift in these requires walking the full block tree per page; too expensive.

### Argument syntax

```
/lint-notion                            # inventory mode, default checks (1-4, 7)
/lint-notion <notion-url-or-id>         # single-page mode, default checks 1-4
/lint-notion --check <category>         # inventory mode, only the named category
/lint-notion <url> --check <category>   # single-page, only the named category
```

`--check <category>` accepts: `content | title | deleted | inaccessible | urls | index | all`. Default (no flag) runs `content`, `title`, `deleted`, `inaccessible`, and in inventory mode also `index` (the wiki-side link rot check on entries of the index page). `urls` and the full `index` integrity check are opt-in.

### Default checks (what runs without flags)

For each ingested Notion source (inventory mode) or the single specified page (single-page mode):

1. **Fetch metadata via `mcp__claude_ai_Notion__notion-fetch`.** Capture: current title, current URL, `last_edited_time`, `archived` flag (if exposed), and any error response (404, 401/403).

2. **Content drift (#1):** if `last_edited_time` > sidecar's `notion-last-edited`, flag.

3. **Title drift (#2):** if current Notion title ≠ sidecar `title`, flag as **informational** — slug does not change; the user can re-ingest to refresh the title metadata if they want.

4. **Deletion / archival (#3):** if the fetch returned not-found or `archived: true`, flag.

5. **Permissions revoked (#4):** if the fetch returned 401/403, flag (separate category from #3 — different recovery path).

In inventory mode, after the per-page loop, also run:

6. **Index-page link rot (#7):** read the Notion index page; parse the `→ wiki/sources/<slug>.md` references; for each, check the file exists locally. Flag any that don't.

### Opt-in checks (only with `--check`)

- **`--check urls`:** for each page where the fetch succeeded, compare current Notion URL to sidecar `url`. Flag drift. Cosmetic only — the page ID is stable.
- **`--check index`:** parse the Notion index page; compare its bullet entries to the expected set (one bullet per Notion-sourced sidecar). Flag missing or extra entries. This is the integrity check for the index page itself, separate from #7.

### Report format

A single markdown report, one H2 per check category (even when empty — empty sections confirm the check ran).

```markdown
# Notion lint report — 2026-05-13

Mode: inventory (N pages checked) | single-page (<slug>)

## Content drift

- `raw/info/foo.info.md`
  - Notion `last_edited_time` 2026-05-13T09:14:00Z is newer than sidecar `notion-last-edited` 2026-05-11T18:00:00Z.
  - **Suggested fix:** `/ingest-notion <url>` to overwrite the cached copy and refresh downstream wiki pages.

## Title drift (informational)

- `raw/info/foo.info.md`
  - Sidecar `title:` "Initial Draft" → current Notion title "Initial Draft (revised)".
  - **Suggested fix:** Re-run `/ingest-notion <url>` to refresh the metadata. The slug and filenames do not change.

## Deleted or archived

(none)

## Permissions revoked

(none)

## Index-page link rot

- Index entry references `wiki/sources/old-doc.md` — no such file in the wiki.
  - **Suggested fix:** Either restore the wiki page, or manually remove the stale entry from the Notion index page.
```

### After producing the report

1. **Do not apply fixes automatically.** Surface the report; wait for the user.
2. Resolutions are user-initiated: re-run `/ingest-notion <url>` for stale content / title; decide manually how to handle deleted pages (keep as historical citation, strip, or wait).
3. **Append a log entry** to `wiki/log.md` (canonical conventions in its HTML comment):

   ```markdown
   ## [YYYY-MM-DD] lint-notion | <inventory | <slug>>

   - Checked: <N pages>
   - Findings: <count by category, e.g. "2 content-drift, 1 title-drift (informational), 0 deleted, 0 inaccessible, 0 index-rot">
   - Applied: <count of fixes the user approved (typically 0 — fixes go through /ingest-notion)>
   - Notable: <one line on anything unusual>
   ```
