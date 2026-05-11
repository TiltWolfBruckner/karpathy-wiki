# PRD: LLM-Maintained Personal Wiki

## 1. Introduction / Overview

Build a personal knowledge base that an LLM agent (Claude Code) incrementally constructs and maintains as a directory of interlinked markdown files. Instead of doing RAG from raw sources on every query, the LLM reads each new source once, integrates it into a persistent wiki (entity pages, concept pages, source summaries, cross-references), and answers future questions against the compiled wiki rather than the raw corpus.

The deliverable is **not** the wiki content itself — that grows over time. The deliverable is the **scaffolding and schema** that turn a fresh directory into a disciplined wiki-maintenance environment: a `CLAUDE.md` schema file, the directory layout, conventions for page types and cross-references, workflows for ingest/query/lint, and seeded `index.md` / `log.md` files.

The reference design is `/Users/user/code/wiki/llm-wiki.md`. This PRD instantiates it with the choices the user made: general-purpose / multi-topic domain, standard scope (ingest + query + lint + index + log), source types {web articles via Obsidian Web Clipper, plain text/pasted notes, PDFs}, retrieval via `index.md` + `grep`/`find` (no qmd integration in v1).

## 2. Goals

- A user can drop a new source into `raw/` and ask Claude Code to ingest it; the LLM produces a source summary, updates relevant entity/concept pages, updates `index.md`, and appends a `log.md` entry — without needing per-session instructions.
- A user can ask a question and get a synthesized answer with citations to wiki pages (and through them, to raw sources).
- A user can ask the LLM to lint the wiki and receive a structured report of contradictions, freshness conflicts, stale claims, orphan pages, missing pages, missing cross-references, missing sidecars, and suggested next sources.
- The wiki is general-purpose — no built-in assumption about subject matter — but opinionated about *structure* (page types, naming, cross-references, freshness).
- Originals in `raw/` are byte-identical to what was clipped or dropped in; per-source metadata lives in sidecars under `raw/info/`.
- The whole thing is plain markdown + a `CLAUDE.md`. No databases, no embeddings infrastructure, no required CLI tools beyond what ships with Claude Code.
- Obsidian can open the repo as a vault and the graph view, backlinks, and `[[wikilinks]]` all work.

## 3. User Stories

### US-001: Repository scaffolding
**Description:** As a user setting up the wiki for the first time, I want the right directory structure and supporting files in place so that Claude Code knows where everything lives from session one.

**Acceptance Criteria:**
- [ ] Directories created: `raw/`, `raw/assets/`, `raw/info/`, `wiki/`, `wiki/sources/`, `wiki/entities/`, `wiki/concepts/`, `tasks/`
- [ ] `.gitignore` excludes `.obsidian/`, `.DS_Store`, and any large binary artifacts the user wouldn't want committed
- [ ] `README.md` at repo root explains in <1 page what this is and how to use it (point Claude Code at the repo, drop sources in `raw/`, ask to ingest)
- [ ] `wiki/index.md` and `wiki/log.md` exist as empty/seeded stubs (filled in by US-007)
- [ ] Repo can be opened in Obsidian as a vault (vault root = repo root) without errors
- [ ] Commit with message starting `US-001`

### US-002: CLAUDE.md — architecture and conventions section
**Description:** As Claude Code starting a session in this repo, I want a `CLAUDE.md` that tells me the three-layer architecture, naming conventions, and what files I own vs. read-only, so that I behave as a wiki maintainer instead of a generic chatbot.

**Acceptance Criteria:**
- [ ] `CLAUDE.md` exists at repo root
- [ ] Section: "Architecture" — explains `raw/` (immutable original sources), `raw/info/` (LLM-owned sidecars per source), `wiki/` (LLM-owned markdown), and the schema (this file itself)
- [ ] Section: "File ownership" — explicit: never modify original source files in `raw/`; freely create/update files in `wiki/` and `raw/info/`. The only LLM writes anywhere under `raw/` are the sidecars described in "Source sidecars" below.
- [ ] Section: "Source sidecars" — for every original at `raw/<basename>.<ext>`, the LLM maintains `raw/info/<basename>.info.md` with YAML frontmatter (`created`, `indexed`, `updated`, optional `title` / `url` / `source-type`). For PDFs, also `raw/info/<basename>.text.md` containing the extracted text. Originals in `raw/` are never modified.
- [ ] Section: "Naming conventions" — kebab-case filenames, page titles in H1, one entity/concept per page; wiki filenames must be globally unique within the vault (Obsidian resolves wikilinks by filename)
- [ ] Section: "Cross-references" — Obsidian-style `[[wikilinks]]` for inter-wiki links; for source citations on wiki pages, use date-tagged wikilinks `[[source-slug|YYYY-MM-DD]]` where the date is the source's `created` (publication) date if known, otherwise its `indexed` date — both read from `raw/info/<basename>.info.md`
- [ ] Section: "Frontmatter" — every wiki page has YAML frontmatter with at minimum: `type`, `created`, `updated`, `sources` (list of source-summary page slugs). The frontmatter list is for navigation; date-tagged inline citations are the freshness signal.
- [ ] Commit with message starting `US-002`

### US-003: CLAUDE.md — page type catalog and templates
**Description:** As Claude Code creating a new wiki page, I want a definitive list of page types and a template for each, so that pages are structurally consistent across the wiki.

**Acceptance Criteria:**
- [ ] `CLAUDE.md` section "Page types" enumerates: `source-summary`, `entity`, `concept`, `comparison`, `overview` (and any others derived from the reference doc)
- [ ] For each type, defined: where it lives (subdirectory), required frontmatter fields, required sections, when to create one
- [ ] A worked example template is shown inline for each type (not just described in prose)
- [ ] Decision rule documented for "is this an entity vs. a concept?" so the LLM doesn't waffle
- [ ] Commit with message starting `US-003`

### US-004: CLAUDE.md — ingest workflow
**Description:** As a user dropping a new source into `raw/` and saying "ingest this", I want a deterministic, repeatable workflow that the LLM follows every time, so the wiki stays consistent.

**Acceptance Criteria:**
- [ ] `CLAUDE.md` section "Ingest workflow" with numbered steps: receive trigger (via `/ingest <path>` or natural language) → read source → create/update `raw/info/<basename>.info.md` sidecar (set `indexed: today`; on first ingest also set `created` from the source's publication date if known and `updated: today`; bump `updated: today` on re-ingest) → discuss key takeaways with user → write `wiki/sources/<slug>.md` source summary → identify which entity/concept pages need creation or update → make those edits, citing sources with date-tagged wikilinks `[[source-slug|YYYY-MM-DD]]` → update `wiki/index.md` → append entry to `wiki/log.md`
- [ ] Specifies handling for the three source types: clipped markdown articles (read directly), pasted text / `.md` / `.txt` (read directly), PDFs (extract to `raw/info/<basename>.text.md` on first ingest using Read's `pages` parameter — required for files >10pp; subsequent reads and `grep` target the extracted `.text.md`; the original PDF stays as the immutable source of truth)
- [ ] Specifies the source-summary page must include: title, source citation (URL or file path), `indexed` date, key claims, key entities/concepts mentioned, links to the wiki pages it touched
- [ ] Specifies the LLM should pause and confirm with the user before overwriting wiki claims contradicted by a newer-dated source. After confirmation: update the wiki page with the new claim, replace the older source citation with the newer one (the older raw/ file and its sidecar are preserved for reference), and note the change in `log.md`.
- [ ] Specifies the log entry format (see US-007)
- [ ] Commit with message starting `US-004`

### US-005: CLAUDE.md — query workflow
**Description:** As a user asking a question against the wiki, I want the LLM to retrieve from the wiki (not re-derive from raw) and cite sources, so answers are fast, consistent, and traceable.

**Acceptance Criteria:**
- [ ] `CLAUDE.md` section "Query workflow" with numbered steps: read `wiki/index.md` first → identify candidate pages → use `grep`/`find` for keywords across `wiki/` if the index isn't enough → read the candidate pages → synthesize answer with `[[wikilinks]]` to wiki pages and date-tagged `[[source-slug|YYYY-MM-DD]]` for source citations
- [ ] Specifies that answers cite wiki pages by `[[wikilink]]` and source pages by date-tagged `[[source-slug|YYYY-MM-DD]]` so freshness is visible at the citation site
- [ ] Specifies the filing rule: the LLM **offers** to file an answer as a new wiki page when any of these triggers fire — (a) the answer cites ≥2 wiki pages, (b) the answer introduces a new comparison or synthesis not present in any existing page, or (c) the answer is multi-paragraph and addresses a non-trivial query. Filing happens only with user confirmation.
- [ ] Specifies fallback: if the wiki has no relevant content, say so explicitly rather than hallucinating; suggest sources to ingest
- [ ] Documents the canonical `grep`/`find` patterns the LLM should use (e.g. `grep -rli "<keyword>" wiki/`)
- [ ] Commit with message starting `US-005`

### US-006: CLAUDE.md — lint workflow
**Description:** As a user periodically asking "lint the wiki", I want a structured health-check report that surfaces problems I should fix or sources I should add, so the wiki doesn't rot.

**Acceptance Criteria:**
- [ ] `CLAUDE.md` section "Lint workflow" with default checks: contradictions between pages, **freshness conflicts** (date-tagged citations on the same claim where a newer source contradicts an older one), orphan pages (no inbound `[[wikilinks]]`), important concepts mentioned but lacking their own page, missing cross-references, frontmatter validity, broken `[[wikilinks]]`, and **missing source sidecars** (every file in `raw/` outside `raw/info/` and `raw/assets/` must have a matching `raw/info/<basename>.info.md`; PDFs additionally have `<basename>.text.md`)
- [ ] Optional staleness check: when invoked as `lint with staleness` (or equivalent natural-language request), additionally flag pages whose `updated:` frontmatter is more than 6 months old. Default `lint` does not include this check.
- [ ] Specifies report format: structured markdown sections, each finding with the file path(s), a one-line description, and a suggested fix
- [ ] Specifies the LLM should propose fixes but not apply them without user confirmation
- [ ] Specifies that lint runs should be logged in `log.md` (see US-007)
- [ ] Commit with message starting `US-006`

### US-007: Seed index.md and log.md with conventions
**Description:** As Claude Code, I want `index.md` and `log.md` to already exist with their formatting conventions baked in, so I keep them consistent on first ingest.

**Acceptance Criteria:**
- [ ] `wiki/index.md` exists with: brief header explaining its role, sections for each page type (`## Sources`, `## Entities`, `## Concepts`, `## Comparisons`, `## Overviews`), and an HTML comment at top instructing the LLM how to update it (alphabetical within section; `- [[slug]] — one-line summary`)
- [ ] `wiki/log.md` exists with: brief header, an HTML comment specifying the entry format `## [YYYY-MM-DD] <op> | <title>` where `<op>` ∈ {`ingest`, `query`, `lint`}, followed by a short body
- [ ] Both files reference the convention so it survives schema-file truncation
- [ ] `CLAUDE.md` cross-references US-007's conventions in the ingest, query, and lint sections
- [ ] Commit with message starting `US-007`

### US-008: End-to-end validation ingest
**Description:** As the user, I want to validate the whole system by ingesting one real source end-to-end, confirming the workflow produces the expected files and links.

**Acceptance Criteria:**
- [ ] Place one short test source in `raw/` (the user provides; could be `llm-wiki.md` itself copied in, or any short article)
- [ ] Run the ingest workflow exactly as documented in `CLAUDE.md` — no improvisation
- [ ] Verify the produced artifacts: `raw/info/<basename>.info.md` sidecar exists with valid `created`/`indexed`/`updated` dates (and `<basename>.text.md` for PDFs); `wiki/sources/<slug>.md` source-summary page exists with the right frontmatter and structure; at least one entity or concept page is created or updated; `wiki/index.md` has the new entry in the right section; `wiki/log.md` has a new entry with the right prefix format
- [ ] Verify all `[[wikilinks]]` resolve (no broken links — Obsidian shows no unresolved links in the graph)
- [ ] Verify source citations on wiki pages use the date-tagged `[[source-slug|YYYY-MM-DD]]` format
- [ ] Run a sample query against the wiki and confirm the LLM follows the query workflow (reads index first, cites wiki pages, uses date-tagged source citations)
- [ ] If anything in the workflow felt awkward or ambiguous, file a follow-up note in `tasks/` (do not silently patch `CLAUDE.md` mid-validation)
- [ ] Commit with message starting `US-008`

### US-009: `/ingest` slash command
**Description:** As a user, I want to invoke the ingest workflow with `/ingest <path>` so the trigger is deterministic and I don't have to phrase the request differently each time.

**Acceptance Criteria:**
- [ ] `.claude/commands/ingest.md` exists
- [ ] Command body instructs Claude to run the ingest workflow defined in `CLAUDE.md` against `$ARGUMENTS` (the file path)
- [ ] Command body explicitly references `CLAUDE.md`'s "Ingest workflow" section as the source of truth, so updates to the workflow take effect without changing the command file
- [ ] If `$ARGUMENTS` is empty, the command prompts the user for a path rather than guessing
- [ ] If `$ARGUMENTS` points to a file outside `raw/`, the command flags it and asks the user whether to proceed (e.g. offer to copy into `raw/` first)
- [ ] Validate by running `/ingest <path>` on the same test source used in US-008 and confirming the same workflow output
- [ ] Commit with message starting `US-009`

## 4. Functional Requirements

- FR-1: Repo root contains `CLAUDE.md`, `README.md`, `.gitignore`, `raw/`, `raw/info/`, `wiki/`, `tasks/`, `.claude/commands/`.
- FR-2: `wiki/` is structured into `sources/`, `entities/`, `concepts/` subdirectories; `index.md` and `log.md` live at `wiki/` root.
- FR-3: `CLAUDE.md` covers: architecture, file ownership, source sidecars, naming conventions, cross-references, frontmatter, page types (with templates), ingest workflow, query workflow, lint workflow.
- FR-4: Every wiki page has YAML frontmatter with at minimum `type`, `created`, `updated`, `sources` (list of source-summary slugs).
- FR-5: Inter-wiki links use Obsidian `[[wikilink]]` syntax. Source citations on wiki pages use date-tagged wikilinks `[[source-slug|YYYY-MM-DD]]` where the date is the source's `created` (publication) date if known, otherwise its `indexed` date — both read from `raw/info/<basename>.info.md`.
- FR-6: `index.md` is updated on every ingest. Entries grouped by page type, alphabetical within group, format `- [[slug]] — one-line summary`.
- FR-7: `log.md` is append-only. Each entry begins with `## [YYYY-MM-DD] <op> | <title>` (parseable by `grep "^## \[" wiki/log.md`).
- FR-8: Ingest, query, and lint workflows are each documented as numbered steps in `CLAUDE.md` and the LLM follows them deterministically.
- FR-9: A `/ingest <path>` slash command exists at `.claude/commands/ingest.md` that invokes the ingest workflow. Natural-language triggers ("ingest this", "file this article") are also recognized.
- FR-10: Retrieval uses `wiki/index.md` first, then `grep`/`find` over `wiki/`. No embedding store, no external search service.
- FR-11: Each original in `raw/` (excluding `raw/info/` and `raw/assets/`) has a corresponding `raw/info/<basename>.info.md` sidecar with YAML frontmatter `created`, `indexed`, `updated`, plus optional `title` / `url` / `source-type`. Sidecars are LLM-owned and updated on each ingest.
- FR-12: PDFs in `raw/` are additionally extracted to `raw/info/<basename>.text.md` on first ingest using Read's `pages` parameter (required for files >10pp). Subsequent reads and `grep` target the extracted `.text.md`. The original PDF is never modified.
- FR-13: The LLM must not modify original source files in `raw/`. The only files it may *create* anywhere under `raw/` are the sidecars described in FR-11 and FR-12, all of which live under `raw/info/`.
- FR-14: When new sources contradict existing wiki claims by date, the LLM pauses and confirms with the user before overwriting. On confirmation, it updates the wiki page, replaces the older source citation with the newer one, and logs the change.
- FR-15: The LLM offers to file an answer as a new wiki page when any of these triggers fire: (a) the answer cites ≥2 wiki pages, (b) the answer introduces a new comparison or synthesis, or (c) the answer is multi-paragraph and addresses a non-trivial query. Filing requires user confirmation.
- FR-16: Default `lint` covers: contradictions, freshness conflicts (date-tagged citations on the same claim where a newer source overrides an older one), orphan pages, missing pages, missing cross-references, frontmatter validity, broken `[[wikilinks]]`, and missing source sidecars. When invoked as `lint with staleness`, it additionally flags pages whose `updated:` is more than 6 months old.

## 5. Non-Goals (Out of Scope for v1)

- No CLI search tool (no `qmd`, no embedding index, no MCP search server). Pure `index.md` + `grep`.
- No `/query` or `/lint` slash commands in v1. Only `/ingest`. Query and lint are triggered in natural language.
- No domain-specific schema. The schema is general-purpose; any subject-specific page types are added by the user later.
- No image-heavy source handling. Text and PDFs only in v1; the two-pass image workflow is deferred.
- No Marp slide output, no matplotlib charts, no canvas outputs. Markdown answers only.
- No automation (no hooks, no cron, no background ingest). All operations are user-initiated.
- No multi-user / collaboration features. Single-user, local-only.
- No web UI, no custom Obsidian plugins. Standard Obsidian + Claude Code only.
- No pre-population of the wiki with content. Empty wiki is a valid v1 deliverable.
- No migrations from existing knowledge bases (Notion, Roam, etc.).

## 6. Design Considerations

- **Obsidian compatibility is a hard constraint.** `[[wikilinks]]`, YAML frontmatter, and the directory layout must work in Obsidian without configuration beyond opening the vault.
- **The `CLAUDE.md` is the product.** Treat it like production code: every section earns its place, examples are concrete, no hand-waving. Re-read it from the LLM's perspective and ask "would I actually follow this deterministically?"
- **Templates inline, not in separate files.** Page-type templates live inside `CLAUDE.md` so the LLM always has them in context, not at the end of a tool-call chain.
- **Index conventions are duplicated** in both `CLAUDE.md` and inside `index.md` itself (as an HTML comment). This is intentional — `CLAUDE.md` may be partially loaded; the `index.md` instructions ride along with the file.
- **Sidecars over annotations.** Per-source metadata lives in sidecar `.info.md` files under `raw/info/`, not in the originals. This keeps `raw/` byte-identical to what was clipped/dropped in, and lets sidecars be regenerated or extended without touching sources.
- **Date-tagged citations encode freshness in-line.** `[[source-slug|YYYY-MM-DD]]` makes the date visible in Reading view and lets `lint` reason about contradictions without parsing prose.
- **Schema is co-evolved.** Document in the README that `CLAUDE.md` is expected to drift as the user discovers what works for their domain.

## 7. Technical Considerations

- Read tool's `pages` parameter is required for PDFs >10 pages — call out explicitly in the ingest workflow.
- `grep -rli` is the recommended retrieval primitive; document the exact patterns to avoid the LLM reinventing them per session.
- `.obsidian/` should be gitignored — workspace state varies per machine and pollutes diffs.
- Frontmatter `created` / `updated` / `indexed` should use ISO 8601 dates (`YYYY-MM-DD`), set at edit time. The LLM should not invent past dates.
- Wikilinks in Obsidian resolve by filename (without extension), so filenames must be globally unique within the vault — enforce in the naming-convention section.
- Date-tagged wikilink format `[[target|YYYY-MM-DD]]` uses Obsidian's standard alias syntax — the date renders as the link text in Reading view, and the link still resolves to the target page.

## 8. Success Metrics

- A fresh Claude Code session in the repo can ingest a new source end-to-end without the user explaining the workflow (US-008 demonstrates this).
- Ingesting a single source touches multiple files (target: ≥4 — one sidecar + one source summary + at least one entity/concept + one index update) without user prompting.
- Lint output is actionable — every finding includes a file path and a suggested fix, not vague observations.
- 100% sidecar coverage: every file in `raw/` (outside `raw/info/` and `raw/assets/`) has a matching `.info.md` (and `.text.md` if PDF) at the time `lint` runs clean.
- The user spends time on sourcing and questions, not on bookkeeping (subjective; measured by the user reporting they didn't have to fix wiki structure manually).
- After ~20 sources, the wiki remains internally consistent (no broken `[[wikilinks]]`, no orphan source-summary pages, no missing sidecars) without manual cleanup.

## 9. Resolved Decisions (from planning)

The following decisions were made during PRD planning and are baked into the FRs and stories above. Recorded here so the rationale survives:

- **Layout:** by-type subdirectories (`sources/`, `entities/`, `concepts/`). Predictable and greppable. Revisit if topical scattering becomes painful.
- **Ingest trigger:** `/ingest <path>` slash command (US-009) plus natural-language fallback.
- **Source metadata:** sidecar `.info.md` files under `raw/info/`, one per source. Originals in `raw/` are never modified. Frontmatter tracks `created` (publication date), `indexed` (when the LLM read it), `updated` (when the sidecar was last touched).
- **PDF handling:** extract to `raw/info/<basename>.text.md` (alongside the `.info.md` sidecar) on first ingest. Future reads/grep target the `.text.md`; the original PDF stays as the immutable source of truth.
- **Source citations on wiki pages:** date-tagged wikilinks `[[source-slug|YYYY-MM-DD]]`. The date enables `lint` to detect freshness conflicts (newer source contradicts older claim).
- **Lint staleness:** opt-in only (`lint with staleness`). Default lint stays focused on content checks; staleness with N=6 months is available when explicitly requested.
- **Filing rule for query answers:** offer to file when any of (a) cites ≥2 wiki pages, (b) introduces a new comparison/synthesis, or (c) answer is multi-paragraph for a non-trivial query. Bias toward offering rather than dropping value into chat history.
