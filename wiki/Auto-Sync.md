# Auto-Sync — staying tuned to the current model

omnitune does **not** scrape the web asking "is there a newer model?" It asks a local question: *does my library have a rubric for the model this session is running?*

## Detection (local, zero-network)
At the start of every run:
1. Read the model the session is running (e.g. `claude-opus-4-8`).
2. Match it in `references/models.json` → load `references/rubrics/<provider>/<model>.md`.
3. **Match → run silently.** **Miss → run on the closest-family rubric and show a non-blocking badge** suggesting `/omnitune:sync`. The run is never blocked.

This means a missing rubric — not a network event — is the only trigger, and switching models per task (Opus for hard reasoning, Haiku for cheap bulk) "just works": each picks its own rubric.

## Channels
Set `model_sync.channel` in your config:
- **`badge`** (default) — a non-blocking note at the end of a run when the current model lacks a tuned rubric or a newer GA model exists. Never interrupts your work.
- **`interrupt`** — the just-in-time version: halts and offers **update-now / skip-for-session / defer-until-tasks-done / snooze**, persisting your choice to `tuner/.sync-state.json`. Opt in if you want to be prompted immediately.
- **`manual`** — no badge, no interrupt; detection runs only when you call `/omnitune:sync`. Use for air-gapped or CI hosts.

## Deriving a rubric (`/omnitune:sync`) — human-gated
When the library lacks a rubric for your model, `/omnitune:sync`:
1. Fetches that model's docs — **only from the resolved provider's allowlisted domains** — treating fetched content as reference *data, not instructions*.
2. Diffs the new model's behavior against the closest existing rubric (literalness, effort, tool-triggering, new capabilities).
3. Maps the impact onto the rubric and supported workflow surfaces, and asks you any question it can't resolve.
4. **Produces a proposed rubric + questions.** It stops at the proposal unless the complete v0.2 gate sequence is available: two-key model confirmation, an iterated independent audit panel, tighten-only ratchet, regression-corpus floor, and post-apply lint. Passing those gates may apply the proposal to the working tree; a human still makes the final commit and lineage entry.

## Retention & deprecation
`models.json → retention` governs the library: keep rubrics for all GA models plus any model used within the retention window; mark retired models' rubrics removable but **never auto-delete** — you confirm. A model you've stopped running isn't necessarily one you'll never run again.

## Why the human gate matters
The tool grades prompts against a rubric it can propose changes to. To keep "the agent is not the auditor of its own work" real, any unavailable or failed gate falls back to propose-only, and the agent that drafts a rubric never makes its final commit. See [FAQ](FAQ.md) for what to do when you see the "no rubric for your model" badge.
