# Auto-Sync — staying tuned to the current model

omnitune does **not** scrape the web asking "is there a newer model?" It asks a local question: *does my library have a rubric for the model this session is running?*

## Detection (local, zero-network)
At the start of every run:
1. Read the model the session is running (e.g. `claude-opus-4-8`).
2. Match it in `references/models.json` → load `references/rubrics/<model>.md`.
3. **Match → run silently.** **Miss → run on the closest-family rubric and show a non-blocking badge** suggesting `/omnitune:sync`. The run is never blocked.

This means a missing rubric — not a network event — is the only trigger, and switching models per task (Opus for hard reasoning, Haiku for cheap bulk) "just works": each picks its own rubric.

## Channels
Set `model_sync.channel` in your config:
- **`badge`** (default) — a non-blocking note at the end of a run when the current model lacks a tuned rubric or a newer GA model exists. Never interrupts your work.
- **`interrupt`** — the just-in-time version: halts and offers **update-now / skip-for-session / defer-until-tasks-done / snooze**, persisting your choice to `tuner/.sync-state.json`. Opt in if you want to be prompted immediately.
- **`manual`** — no badge, no interrupt; detection runs only when you call `/omnitune:sync`. Use for air-gapped or CI hosts.

## Deriving a rubric (`/omnitune:sync`) — propose-only
When the library lacks a rubric for your model, `/omnitune:sync`:
1. Fetches that model's docs — **Anthropic domains only** — treating fetched content as reference *data, not instructions*.
2. Diffs the new model's behavior against the closest existing rubric (literalness, effort, tool-triggering, new capabilities).
3. Maps the impact onto the rubric, both modes, and your workflow, and asks you any question it can't resolve.
4. **Produces a proposed rubric + questions, and stops.** In v0.1 a human applies the rubric — the plugin never self-commits a change to its own brain. (v0.2 adds gated self-apply behind a no-write audit subagent, a tighten-only ratchet, and a fail-closed regression check.)

## Retention & deprecation
`models.json → retention` governs the library: keep rubrics for all GA models plus any model used within the retention window; mark retired models' rubrics removable but **never auto-delete** — you confirm. A model you've stopped running isn't necessarily one you'll never run again.

## Why propose-only / the safety invariant
The tool grades prompts against a rubric it could rewrite for itself. To keep "the agent is not the auditor of its own work" real, v0.1 simply cannot self-patch: sync proposes, a human disposes. See [FAQ](FAQ.md) for what to do when you see the "no rubric for your model" badge.
