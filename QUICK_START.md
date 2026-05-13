# Quick Start

A fast on-ramp for using this repo as a personal LLM-maintained wiki. The audience is **users** — you point Claude Code at the repo, add your own sources, and let it build out a wiki for you. You don't need to modify the schema or the workflow specs to get going.

## Clone

```bash
git clone git@github.com:TiltWolfBruckner/karpathy-wiki.git
cd karpathy-wiki
```

(HTTPS works too: `git clone https://github.com/TiltWolfBruckner/karpathy-wiki.git`.)

> **Don't push back to this repo.** Your sources, your wiki, and your log are personal — the upstream is the scaffolding, not a shared knowledge base. If you want a remote backup, **fork to a private repo of your own** and push there instead. Treat this clone as the starting point of your own wiki, not a working copy you sync upstream.

## How to use

1. **Open the repo in Claude Code.** Point Claude Code at this directory; it will read `CLAUDE.md` automatically.

2. **Add a source.**
   - **Files (articles, notes, PDFs):** drop them into `raw/`. Markdown clipped from the web works well — see the Obsidian Web Clipper tip below.
   - **Notion pages:** no local file needed — you'll pass the page URL in the next step.

3. **Ingest a file:** `/ingest raw/<file>` (or say "ingest this"). Claude reads the document and updates the wiki content and links — you never need to directly edit the wiki yourself.

4. **Ingest a Notion page:** `/ingest-notion <notion-url-or-id>`. On your first Notion ingest, you'll be asked for the URL of a Notion page to use as a registry — Claude will add a back-link entry there on every ingest. The registry pointer is stored in `notion-index.md` at the repo root (gitignored, machine-specific). Downstream flow is identical to a file ingest.

5. **Query the wiki:** `/query <question>` or just ask a question. Claude searches the wiki (not the raw sources) and answers with `[[wikilinks]]` and date-tagged source citations. Substantial answers may be offered as new wiki pages.

6. **Lint periodically.**
   - `/lint` — flags contradictions, freshness conflicts, orphans, missing pages, missing cross-references, broken wikilinks, and missing sidecars. Offline-only; never modifies files.
   - `/lint staleness` — same plus flags wiki pages whose `updated:` is more than 6 months old.
   - `/lint-notion` — separate cloud-freshness pass that checks ingested Notion pages against the live Notion state. Use `/lint-notion <url>` to check just one page when you know a specific Notion doc has changed.

## Tips

- **Scale.** The `index.md` + `grep` retrieval that `/query` uses works comfortably at moderate scale — roughly **~100 sources and a few hundred wiki pages**. Beyond that, performance starts to degrade and you'll want a real search index. (future enhancement outlined in llm-wiki.md)

- **`CLAUDE.md` co-evolves with use.** Treat it as configuration, not stone. As you discover what conventions work for your domain — naming patterns, page-type tweaks, lint rules that matter, ingest preferences — update `CLAUDE.md` to match. The schema is *meant* to drift; it's how the system adapts to the shape of *your* knowledge base. Ask Claude to help you refactor it when you notice friction.

**OPTIONAL**
- **Use Obsidian as the viewer.** Open the repo as an Obsidian vault — wikilinks, backlinks, and the graph view all work out of the box. The graph view is the fastest way to see the shape of your wiki: hubs, orphans, clusters. Per-vault state lives in `.obsidian/` and is already gitignored. The [Obsidian Web Clipper](https://obsidian.md/clipper) browser extension is the easiest way to get web articles into `raw/` as clean markdown.
