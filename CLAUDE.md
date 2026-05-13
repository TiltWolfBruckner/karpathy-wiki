# CLAUDE.md — Wiki Schema

This file is the operating manual for an LLM agent (Claude Code) maintaining this wiki. It defines:

- the directory layout and what each layer is for
- which files the LLM owns vs. which are read-only
- how pages, links, and citations are formatted
- a one-paragraph summary of each workflow (full specs live in `.claude/skills/<name>/SKILL.md`)

Page-type frontmatter shapes and required sections live in **"Page types"** below; full worked examples in `docs/page-type-examples.md`. Workflows for **ingest**, **ingest-notion**, **query**, **lint**, and **lint-notion** are summarized in **"Workflows"** below — the canonical specs live as skills under `.claude/skills/<name>/SKILL.md` (invoked as slash commands of the same name).

If a rule below seems to forbid the action you were about to take — modifying a file in `raw/` directly, inventing a new wikilink format, skipping the index update — stop and confirm with the user. The wiki's value comes from consistency; one-off improvisations corrode it.

The reference design for the whole pattern is `llm-wiki.md` at the repo root. The PRD that scopes this build is `tasks/prd-llm-wiki.md`.

## Architecture

Three layers plus per-source sidecars:

- **`raw/`** — original source documents (articles, PDFs, pasted notes). Immutable. The LLM reads these but never modifies them.
- **`raw/info/`** — LLM-owned sidecars, one per source. Holds metadata (`created`, `indexed`, `updated`) and, for PDFs, extracted text. See "Source sidecars" below.
- **`raw/assets/`** — image and binary attachments referenced from sources. LLM-writable (e.g. when an Obsidian Web Clipper download lands here).
- **`raw/notion/`** — LLM-owned cache of Notion pages fetched via the Notion MCP. One markdown file per ingested Notion page; overwritten in place on re-ingest (never accumulated). Populated by the `ingest-notion` skill; never edited by hand. See `.claude/skills/ingest-notion/SKILL.md`.
- **`wiki/`** — LLM-generated markdown. Source summaries in `wiki/sources/`, entity pages in `wiki/entities/`, concept pages in `wiki/concepts/`, comparisons in `wiki/comparisons/`, overviews in `wiki/overviews/`, plus `wiki/index.md` and `wiki/log.md`. The LLM owns this layer entirely.
- **`.claude/skills/`** — workflow skills, one directory per skill. Each contains a `SKILL.md` (the canonical workflow spec) plus any bundled reference files. Triggered as slash commands (`/ingest`, `/query`, `/lint`, `/lint-notion`, `/ingest-notion`) or by natural-language matching of the skill descriptions.
- **`docs/`** — shared LLM-readable reference material that isn't bound to a single skill. `docs/page-type-examples.md` holds worked examples for each wiki page type (used by both the ingest and query skills).
- **`CLAUDE.md`** (this file) — the schema. Co-evolves with use; updates require user direction.

Other directory at repo root: `tasks/` (PRDs and planning). The LLM does not modify files under it unless explicitly asked.

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
| `docs/**` | yes | only when user asks | only when user asks |
| `CLAUDE.md` | yes | only when user asks | only when user asks |
| `tasks/**` | yes | only when user asks | only when user asks |
| `README.md` | yes | only when user asks | — |
| `.claude/skills/**` | yes | only when user asks | only when user asks |

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

# Optional — only set for source-type: notion (see .claude/skills/ingest-notion/SKILL.md):
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

- `type`: one of the page types catalogued in "Page types" below.
- `created`: ISO 8601 date this wiki page was first written. Set once, never edited.
- `updated`: ISO 8601 date this page was last meaningfully edited. Bump on content changes; do not bump for whitespace or formatting.
- `sources`: list of source-summary slugs that contributed to this page. **For navigation and lint — not for freshness.** Freshness lives in the inline date-tagged citations (see "Cross-references").

Source-summary pages (`wiki/sources/<slug>.md`) carry additional fields (`indexed`, `url`, `source-type`, `source-genre`) mirroring their sidecar. Per-type frontmatter is detailed in "Page types".

Pages with missing or malformed frontmatter will be flagged by `lint`.

## Date discipline

- Always use ISO 8601 dates: `YYYY-MM-DD`.
- Never invent past dates. If you don't know a source's publication date, set `created: <today>` to match `indexed`. Don't guess.
- "Today" is the date you're running, not the date the source mentions.
- When updating a sidecar, bump `updated` even if no other field changed (it's how lint knows the sidecar was reviewed).

## Workflows

Five canonical workflow skills under `.claude/skills/`. Each has its full specification in its `SKILL.md`; skills are invoked as slash commands (same name) or by natural-language matching of the skill description. The summaries below are pointers and load-bearing principles — read the SKILL.md before performing the workflow.

- **Ingest** (`.claude/skills/ingest/SKILL.md`) — read a source, write a sidecar, **discuss key takeaways with the user (the pause is canonical, not optional)**, write the source-summary page, update entity/concept pages, update `wiki/index.md`, append to `wiki/log.md`. Covers pre-flight, contradictions, source types. Slash command: `/ingest <path>`.
- **Ingest-notion** (`.claude/skills/ingest-notion/SKILL.md`) — Notion-specific variant: fetch via the Notion MCP, cache under `raw/notion/`, write the sidecar (with `notion-page-id` and `notion-last-edited`), append to the Notion-side index page, then hand off to the ingest skill from step 3. Uses a **slug-frozen-at-first-ingest rule** and **overwrites the cached copy in place** on re-ingest — never accumulating versions. Slash command: `/ingest-notion <url>`.
- **Query** (`.claude/skills/query/SKILL.md`) — read `wiki/index.md` first; grep `wiki/` if needed; **never grep `raw/`** (that's what the wiki exists to avoid); cite with `[[wikilink]]` and date-tagged `[[source|YYYY-MM-DD]]`; **offer to file the answer** when it cites ≥2 pages or introduces new synthesis (the filing rule). Slash command: `/query <question>`.
- **Lint** (`.claude/skills/lint/SKILL.md`, with bundled `sample-report.md`) — eight offline checks: contradictions, freshness conflicts, orphans, missing pages, missing cross-refs, frontmatter validity, broken wikilinks, missing sidecars. **Lint never modifies files** — produces a report; user approves fixes. **`/lint` is offline-only** — it never makes Notion network calls. Slash command: `/lint` (or `/lint staleness` for the optional staleness check).
- **Lint-notion** (`.claude/skills/lint-notion/SKILL.md`, with bundled `sample-report.md`) — cloud-freshness pass for Notion sources: content drift, title drift (informational), deletion, permissions revoked, index-page link rot. Inventory mode (no argument) checks every ingested Notion source; single-page mode (`/lint-notion <url>`) checks just one. Opt-in checks (`--check urls`, `--check index`) for cosmetic and integrity sweeps. Like `/lint`, it surfaces a report and never modifies files; fixes are user-initiated via `/ingest-notion <url>`. Slash command: `/lint-notion [<url>] [--check <category>]`.

## Page types

Five types. Each has a fixed location, frontmatter shape, required sections, and a clear "when to create". Full worked examples for every type live in `docs/page-type-examples.md`.

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

**Worked example:** `docs/page-type-examples.md > source-summary`.

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

**Worked example:** `docs/page-type-examples.md > entity`.

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

**Worked example:** `docs/page-type-examples.md > concept`.

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

**Worked example:** `docs/page-type-examples.md > comparison`.

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

**Worked example:** `docs/page-type-examples.md > overview`.
