---
description: Ingest a source from raw/ into the wiki — sidecar, summary, entity/concept updates, index, log
argument-hint: <path-to-file-in-raw/>
---

Run the **Ingest workflow** defined in `CLAUDE.md > Ingest workflow` against:

`$ARGUMENTS`

`CLAUDE.md > Ingest workflow` is the canonical source of truth for the steps, source-type handling (markdown / text / PDF), pre-flight checks, contradiction-resolution patterns, and the log-entry format. Follow it exactly — do not improvise. If `CLAUDE.md` is unavailable for any reason, stop and tell the user; do not attempt to reconstruct the workflow from memory.

**Pre-flight (mirrored from the workflow; restated here so the slash command stops cleanly when arguments are bad):**

- If `$ARGUMENTS` is empty, ask the user which file to ingest. **Do not guess.**
- If `$ARGUMENTS` points to a file outside `raw/`, stop and ask the user before proceeding. Usually the right move is to copy the file into `raw/` first, then ingest the copy — but confirm with the user rather than copying silently.
- If `$ARGUMENTS` points to a file under `raw/info/` or `raw/assets/`, stop — those are sidecar / attachment directories, not source originals.
- If `$ARGUMENTS`'s basename collides with an existing file in `raw/` (different extension, same basename), stop and ask. Sidecars are flat under `raw/info/` and basenames must be unique.

Once pre-flight passes, run the numbered steps in `CLAUDE.md > Ingest workflow` from step 1.
