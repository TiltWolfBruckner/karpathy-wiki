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
- **`wiki/`** — LLM-generated markdown. Source summaries in `wiki/sources/`, entity pages in `wiki/entities/`, concept pages in `wiki/concepts/`, plus `wiki/index.md` and `wiki/log.md`. The LLM owns this layer entirely.
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

## Sections under construction

Added in subsequent user stories — until they exist, ask the user before doing the corresponding operation:

- **Page types** (US-003) — catalog of `source-summary` / `entity` / `concept` / `comparison` / `overview` with templates.
- **Ingest workflow** (US-004) — what happens when a new source lands in `raw/`.
- **Query workflow** (US-005) — how to retrieve from the wiki and cite sources.
- **Lint workflow** (US-006) — health checks and the freshness-conflict detector.
