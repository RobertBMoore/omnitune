---
class: goal-pack
mode: C
---
# Mode C golden — the emitted pack's TOPOLOGY, scored (not just its recording)

Companion to `goal-pack-brief.md`. That fixture protects the seven recording
components; **this one protects the team the pack designs** — the exact dimension
that shipped unchecked and produced "a bad orchestration of agents." It is a
golden reference, not a captured run: it states what a *good* emitted team looks
like for the FieldNotes brief (SvelteKit + SQLite, single VPS dev stage, M0-M4,
two-person build) so that a rubric or reference change dropping tiering, the
dispatch brief, or scale-sizing flips a visible verdict.

## Input brief (as in goal-pack-brief.md)

FieldNotes — a small members-only gardening-club web app. Two people build it
(operator + one dev). Stack: SvelteKit + SQLite, one VPS dev stage. Gates:
`npm run lint`, `npm test` (needs DATABASE_FILE), `npm run e2e` against the dev URL.
Milestones M0 scaffold · M1 auth · M2 observations CRUD · M3 photo uploads ·
M4 launch. Quiet hours 22:00-07:00; only a P0 breaks them. Device pass after M2.

## Golden topology (what a good pack emits)

**Scale tier: Solo/Pair.** ≤1 concurrent writer, ~days-to-weeks horizon → the
lean tier. State files d1-d5 only (drop the session registry and continuity
buffer); reflection **off** (session-close append; the operator reviews at
milestone close); watchdog optional; C2 audit-per-tag **none** — the gate battery
(lint/test/e2e green at HEAD) satisfies it. A combined code/UX auditor is spun up
**only** for the user-facing milestones (M2 CRUD, M3 uploads, M4 launch), not for
the M0 scaffold. **Program apparatus on this pair build would be a topology
failure** (anti-pattern 15).

**Runtime model set (generated on Opus 4.8, but the team is tiered):**

| Role | Tier | model: | effort: | tools: |
|---|---|---|---|---|
| Orchestrator (driver) | frontier | `claude-opus-4-8` | `xhigh` | (the operator's session) |
| Builder | workhorse | `claude-sonnet-5` | `high` | Bash, Read, Edit, Write, Glob, Grep |
| Combined code/UX auditor (user-facing milestones) | workhorse | `claude-sonnet-5` | `high` | Read, Grep, Glob, Bash |
| Scaffold / lint / docs explorer | cheap | `claude-haiku-4-5` | `medium` | Read, Glob, Grep, Bash |

Every role pins `model:` + `effort:` — **no role inherits the session model by
default** (anti-pattern 12). One builder, because the workstreams are not
independent enough to fan out (anti-pattern 13); the auditor is read-only and may
overlap the builder (X6). Correctness serialization holds: one writer on the
milestone branch (X5). Fan-out posture is **Opus's** for the orchestrator (fewer
subagents, blocking-then-integrate is fine) — and would flip to more/async if the
team ran on Fable 5 (X7).

## The four-part dispatch brief (every delegation carries it — X4)

- **objective:** implement M2 observations CRUD on branch `m2-observations`.
- **output format:** the report contract — summary + commit SHAs + each gate's
  final ~5 lines; no diffs or logs.
- **tools/sources:** the files by path (schema, routes, the migration), the dev
  URL, `DATABASE_FILE` for the test gate.
- **boundaries:** do not touch auth (M1, done); commit from the first block; stop
  and report at the milestone tag.

## What this fixture catches

A rubric/reference edit that (a) deletes the delegation-tier layer so the team
goes mono-model, (b) drops the `model:`/`effort:` agent slots, (c) removes the
four-part dispatch brief, (d) hardcodes program apparatus regardless of scale, or
(e) re-flattens correctness and throughput serialization — each drops a topology
assertion above and is the drift this golden baseline exists to surface. The
Step 3.5 topology self-check walks the same X1-X11 invariants on the live emit.
