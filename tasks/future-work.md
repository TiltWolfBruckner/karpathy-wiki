# Future Work

Items deliberately deferred from v1. Each has enough scope to be its own user story (or a small batch) when picked up; the design questions below are the open issues to resolve first.

## Image-heavy source handling

**What:** Support sources that are primarily images or rely heavily on inline images — whiteboard photos, diagram-rich slides, screenshots-as-documentation, comics, infographics. In v1 the system is text-and-PDF only (with PDFs read as text via the Read tool's `pages` parameter).

**Why deferred:** The reference design notes that LLMs can't natively read markdown with inline images in one pass — the workaround is a two-pass workflow (text first, then view referenced images separately). That's doable but adds enough complexity that bundling it with v1 would have slowed everything else. Real-use feedback will help shape the workflow before the design is pinned.

**Open design questions:**

- Where do extracted/clipped images live? The current scaffolding has `raw/assets/` but the relationship between an image and its source's sidecar is unspecified.
- Does the image pass produce its own sidecar (e.g. `raw/info/<basename>.images.md` with per-image descriptions) or extend the existing `.info.md`?
- For sources with hundreds of images (e.g. an annotated slide deck), how does the LLM scope which images to actually view? Read every one? Sample? Skip unless the user asks?
- `source-type: image` exists in the v1 enum but the workflow doesn't cover it yet. Does an image-only source produce a different source-summary template?

**Rough scope:** 2–3 stories. Sidecar extension, ingest workflow changes for the image-pass, lint rules for image-bearing sources.

## CLI search at scale (qmd or similar)

**What:** Add a real search index over `wiki/` — hybrid BM25 + vector search with LLM re-ranking, on-device — for wikis where `index.md` + `grep` stops being enough. The reference design suggests [qmd](https://github.com/tobi/qmd) as the canonical option; both a CLI and an MCP server are available.

**Why deferred:** At v1 scale `index.md` + `grep` is sufficient and adds no dependencies. The query workflow already names the canonical `grep` patterns. Adding a search tool now would be premature; better to feel the pain at moderate scale first and let the threshold drive the design.

**Open design questions:**

- Threshold for adoption: how many pages or sources before `grep` stops working well? Need real-use data — could be 200 pages or 2000.
- Local CLI vs. MCP server: `qmd` ships both. Pick one as the integration mode, or document when each fits.
- Integration with the existing query workflow: does the LLM call `qmd` via Bash, or as an MCP tool? If MCP, `CLAUDE.md > Query workflow` needs a third retrieval mode alongside `index.md` and `grep`.
- Index freshness: who triggers reindex? Every ingest (synchronous)? A separate `/reindex` command? A lint check that warns when the index is stale?
- What gets indexed: `wiki/` only, or also `raw/info/*.text.md` (extracted PDF text)?

**Rough scope:** 1–2 stories. Tool install + integration into the query workflow, plus a lint rule for index freshness if the tool requires a separate reindex step.

## Marp / matplotlib / canvas output formats

**What:** Let queries produce non-markdown artifacts — slide decks (Marp), charts (matplotlib), Obsidian canvases — and file them back into the wiki when useful, alongside markdown answers.

**Why deferred:** Markdown answers are sufficient for v1, and adding output formats requires deciding where each format lives in the wiki, whether the LLM has the right tools (matplotlib needs Python + a runtime), and how lint handles non-markdown files.

**Open design questions:**

- Where do generated artifacts live? `wiki/outputs/`? Adjacent to the source-summary or comparison page that produced them?
- Frontmatter for non-markdown files: if a chart is `foo.py` + `foo.png`, which is the canonical "page"? Both as first-class artifacts, or one as primary and the other as a sidecar-style derivative?
- For Marp slide decks: do they get their own `type: slide-deck` in the page type catalog, or are they an output format of an existing type (overview, comparison)?
- Charts often have a source dataset — does the wiki need a `data/` layer alongside `raw/` and `wiki/`?
- How does the filing rule from the query workflow apply when the natural output is a chart, not prose?

**Rough scope:** 3–4 stories — one per output format, each fairly self-contained. Marp is the easiest to start with (pure markdown + plugin).

## Automation (hooks, cron, background ingest)

**What:** Reduce the user-initiated friction. Auto-ingest sources dropped into `raw/`, scheduled lint passes, background processing of accumulated material. In v1 every operation requires explicit user invocation.

**Why deferred:** v1 is deliberately user-initiated for every operation — keeps the interaction model simple and the user in the loop. Automation introduces failure modes (silent ingest failures, lint reports nobody reads, contradictions resolved without confirmation) that need careful design.

**Open design questions:**

- Trigger: file-system watcher (fswatch / inotify)? Claude Code hooks? Cron? `launchd` on macOS?
- Failure handling: if an auto-ingest hits a contradiction (requires user confirmation per the ingest workflow), where does that surface? A queue? A notification? Halt the auto-process?
- User opt-in: per-source, per-directory, or session-wide? Default to off or on?
- Logging: do automated runs get the same `wiki/log.md` treatment, or a separate channel to avoid drowning user-initiated entries?
- Safety: automated reads of `raw/` mean anything dropped in gets processed without confirmation — is that what the user actually wants for, say, draft personal notes?
- Cost/quota: background LLM calls have real cost — does the user see a usage projection before enabling?

**Rough scope:** 2–3 stories minimum. Trigger mechanism, failure-handling / escalation UX, log and safety-UX changes.

## Notion ingestor — deferred extensions

**What:** Extensions to the Notion ingestor beyond the v1 scope of single-page ingest + cloud-freshness lint via `/ingest-notion` and `/lint-notion`. The v1 covers: cache one Notion page per invocation to `raw/notion/<slug>.md` with a flat sidecar, append a back-link entry to a single Notion index page, and detect content/title/deleted/inaccessible drift plus index-page link rot through user-invoked lint.

**Why deferred:** The v1 chooses single-page-at-a-time so each ingest can hit the canonical "discuss key takeaways with the user" pause. Drift detection beyond body/title/deletion would either need richer Notion metadata in the sidecar (DB properties) or expensive workspace-wide traversal (sub-page / synced-block drift). Both buy real value but are not load-bearing for a usable v1.

**Open design questions:**

- **Batch ingest by Notion query.** Today `/ingest-notion <url>` ingests one page. The user could want to ingest a whole Notion database, search result, or section of their workspace. Open: how does the "discuss key takeaways" pause work in a batch? Per-page (slow but faithful) or per-batch (fast but loses the per-source nuance)? Where does the failure-recovery sit if page 7 of 30 hits a contradiction?
- **DB-properties drift (`/lint-notion` drift mode #7).** Notion database pages carry properties (Status, Tags, Date, Person) that change independently of the body. Worth snapshotting at ingest, then diffing on lint. Open: which properties matter? All? User-configured allowlist? Where does the snapshot live — extend `notion-last-edited` into a `notion-snapshot:` map, or a separate `.notion-meta.md` sidecar?
- **Embedded sub-page / synced-block drift (`/lint-notion` drift mode #8).** Notion pages can embed child databases, synced blocks from elsewhere, linked pages — the parent's `last_edited_time` may or may not propagate through these. Detecting drift in embeds requires walking the full block tree. Open: heuristic (recursive `last_edited_time` rollup if the API exposes it) vs. full block walk; per-page cost ceiling before the user gets warned.
- **Two-way sync — wiki notes back into Notion.** Today the only Notion-side artifact is the index page. The wiki source-summary could be mirrored back as a comment on the original Notion page, so users browsing Notion see "this has been read by the wiki, summary here". Open: comment vs. property vs. linked-database row; how to keep them in sync; what happens when the wiki summary changes.
- **Auto-creating the Notion index page.** v1 requires the user to point at an existing page; the slash command stops cleanly and asks. The bootstrap could optionally create the page itself (via `mcp__claude_ai_Notion__notion-create-pages`) if the user grants a parent. Open: parent picker UX in a CLI context; whether to make this opt-in or default.
- **Image extraction from Notion pages.** Notion pages with embedded images currently get only their text. If the image-heavy-source-handling work above lands, Notion ingest should plug into it — download images to `raw/assets/`, reference them in the cached `raw/notion/<slug>.md`.
- **Scheduled / cron-based freshness scans.** v1 is purely user-invoked (`/lint-notion`). Pairs with the "Automation" item above — a background hook that runs `/lint-notion` weekly and surfaces a digest. Open: how findings reach the user without spamming.

**Rough scope:** 4–6 stories — batch ingest, DB-properties drift, embedded-block drift, two-way sync, image handling (bundle with the image-handling future-work), and a scheduled-lint hook (bundle with the automation future-work).
