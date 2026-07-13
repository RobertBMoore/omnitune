---
class: goal-pack
mode: C
---
# Mode C input — a compact project brief

Turn this brief into a launch pack:

    Build "FieldNotes", a small members-only web app where a gardening club logs
    plot observations and photos. Stack: SvelteKit + SQLite, deployed to a single
    VPS dev stage at https://dev.fieldnotes.example. Gates: `npm run lint`,
    `npm test` (needs DATABASE_FILE set), `npm run e2e` against the dev URL.
    Milestones: M0 scaffold, M1 auth, M2 observations CRUD, M3 photo uploads,
    M4 launch. Checkpoints: CP1 config, CP2 DNS, CP3 launch approval (all
    operator-owned). Quiet hours 22:00-07:00 local; only a P0 may break them.
    Operator device pass after M2.

**Baseline:** Mode C emits a complete pack with all seven contract components: a
MISSION-style goal prompt carrying the state-file schema block and numbered
checkpoint list; a CLAUDE.md-shaped constitution (bootstrap, guardrails digest,
loop with RECORD, context economy, precedence, evidence rule, delegation policy);
builder/auditor agent definitions with tools allowlists and the report contract;
state-file contracts (CURRENT ≤25 lines, MILESTONES, append-only LOG, DECISIONS,
BACKLOG, session registry, ~8KB continuity buffer); a guardrails digest; a
numbered operator pre-flight checklist including the quiet hours above; a
reflection clause (milestone close or 24h, whichever first); and runnable
record_check + staleness-watchdog gate scripts configured for `milestone/*` tags
and the gates named in the brief. Every specific beyond this brief is laddered as
an assumption. A rubric or reference change that drops a pack component or
demotes a mechanized gate to policy prose is exactly the drift this baseline
catches.
