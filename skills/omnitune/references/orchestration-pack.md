---
name: orchestration-pack
description: >-
  Knowledge source for omnitune Mode C (tune-goal) — the contract a launch-ready
  orchestration pack must satisfy: pack components, the invariants packs encode
  as mechanized gates or brief binding rules, the gate-script contracts, the
  reflection clause, and a traceability table proving no field lesson was
  dropped. Provider-shared and model-agnostic: Mode C composes this file with
  the session model's rubric (references/rubrics/<provider>/<model>.md + _core.md)
  for model-specific steering.
lastReviewed: 2026-07-13
---

# Orchestration pack contract — omnitune Mode C

## Evidence base

Distilled from a multi-day, high-change single-orchestrator field build and its
independent orchestration audit (ten severity-ranked findings, `P0-1`..`P3-9`
below), plus the fifteen starting rules distilled from the same build (`T1`..`T15`
below). The audit's verdict: the architecture held — state in files, judgment in
the orchestrator, labor in disposable subagents, evidence over memory — and what
decayed was recording. Every failure was preventable at launch-pack time. This
file therefore encodes recording discipline as machinery, not advice.

Two meta-rules bind everything below, and this file honors them in its own writing:

- **Gates, not prose.** Every invariant a script can check ships in the pack as a
  blocking script. Policy prose that a script could enforce is a pack defect.
- **Brief binding rules, not case lists.** Where an invariant needs judgment, the
  pack states it as one short binding rule in the constitution. Enumerated case
  lists rot; rules transfer.

## The pack contract

A complete pack contains exactly these components. Mode C emits all of them; a
pack missing any one is incomplete.

**(a) Goal prompt** — the MISSION-style statute book: the mission in one section;
phases and milestones with a per-milestone reading map; the state-file schema
block verbatim (see d); the numbered checkpoint list with what each blocks; the
definition of done.

**(b) Constitution** — CLAUDE.md-shaped, auto-loads every session, under ~90
lines: a bootstrap block (fresh start vs resume-from-CURRENT; never re-scaffold,
never restart a milestone because context was lost); the guardrails digest (e);
the loop, one line per step, with RECORD explicit; the context-economy rules; the
precedence order (guardrails > checkpoints > spec > milestone definitions > own
notes); the evidence rule; the delegation policy in two lines. The goal prompt is
the statute book; this file is the constitution.

**(c) Agent definitions** — builder(s) and read-only auditor(s), each with a
`tools:` allowlist from day one and the binding report contract in the body:
summary of what changed and why + commit SHAs + each gate command with only its
final ~5 output lines; never diffs, full logs, or file bodies. Crash posture:
commit the first coherent piece within the first work block. Model, effort, and
verbosity defaults come from the session model's rubric at emit time — never
hardcoded here.

**(d) State-file contracts:**

1. CURRENT block — a resume pointer, ≤25 lines (milestone, loop step, branch +
   HEAD SHA, one-sentence next action, waiting-on, blockers, one pointer line per
   parallel track), every line under the state-file line cap.
2. MILESTONES table — `| M | Status | Tag | Evidence |`; must agree with git tags (G1).
3. LOG — append-only, newest first; every milestone close gets an entry (G1).
4. DECISIONS — numbered ADRs, appended in order, for every deviation from the goal prompt.
5. BACKLOG — parked ideas and low-severity findings; never built from in v1.
6. Session registry — one line per live session/worktree inside CURRENT: driver,
   branch, charter pointer, last-heartbeat timestamp.
7. Continuity buffer — newest-entry-first, rotated daily, hard-capped (~8KB) so
   the session-start injection always arrives inline, never as a truncated attachment.

**(e) Guardrails digest** — environment/account pin verified before the first
destructive-capable command of any session; the never-list, with destructive
command patterns denied at the settings layer, not by promise; secrets placement
(never in code, logs, commits, or chat; a named secret store); operator-only
items recorded and raised at checkpoints, never silently attempted. All present
from session one.

**(f) Operator pre-flight checklist** — numbered, covering launch-day setup: the
host MCP/plugin disable list; an injected-catalog size audit; the numbered
checkpoints and what each blocks; the device-pass calendar (the first operator
experience pass early, on the core user journey); quiet hours and which severity
may break them.

**(g) Gate scripts** — mechanized, shipped as runnable files: record_check
(G1/G2) and the staleness watchdog (G4), instantiated from `pack-templates/`
with the pack's CONFIG filled in from the brief.

## Mechanized gates (what packs ship as blocking scripts)

### G1 — record_check (blocking; run before every integration merge and every tag)

Template: `pack-templates/record_check.py` (stdlib-only python3; CONFIG dict at
the top). Fails on:

- C1 — uncommitted files under `verification/` or `audits/`
- C2 — a milestone tag without a filed per-auditor audit report under `audits/`
- C3 — CURRENT-block HEAD SHA missing or ≠ `git rev-parse HEAD`
- C4 — MILESTONES table disagreeing with git tags (a closed row without its tag;
  a milestone tag whose row is missing or not closed)
- C5 — a closed milestone with no LOG entry
- C6 — CURRENT block over its line cap (default 25)
- C7 — any state-file line over the line-length cap (~500 chars)

Warns (never blocks) on:

- W1 — unpushed main or tags
- W2 — undeleted merged milestone branches

### G2 — red-gate consumption (the rule the script's exit code binds)

A red G1 halts the loop step that invoked it: the merge or tag does not proceed
until every failing line carries a committed one-line disposition — `product
defect` / `stale harness` / `fixture gap`. The launch gate is: full battery green
or fully dispositioned at HEAD, with the run output committed in the same commit.
Failing loudly is not enough; something must be forced to consume the failure.

### G3 — regression-harness contract

Every verify suite asserts `stage >= milestone` (never an exact version pin) and
self-seeds against persistent, non-reaped fixtures, so the full-history battery
stays runnable against a moving dev stage. A suite that can never pass again is a
harness defect, not a product signal.

### G4 — status artifact + staleness watchdog

The pack schedules a status artifact the operator can check without asking, and
ships an external staleness watchdog — a dumb scheduled script
(`pack-templates/staleness_watchdog.sh`), not an agent — that alerts when the
heartbeat / session-registry timestamp exceeds its cadence. Orchestrator death is
detected by something the orchestrator does not have to be alive to run.

## Binding rules (what packs write into the constitution)

Each is one brief rule; packs copy the rule, not an essay about it.

- B1 — CURRENT updates land in the same commit as every integration merge; a
  merge without one is an unfinished merge.
- B2 — Context economy: findings-only reports; gate tails, never logs; pixel and
  screenshot judgment delegated to the UX auditor/builder — the orchestrator
  consumes verdicts and reads at most one composite image per milestone.
- B3 — Report contract: summary + SHAs + gate tails (~5 lines); never diffs or logs.
- B4 — Release-once: acknowledge a final report once; never re-issue work whose
  deliverable exists at HEAD (check git first); deconflict unassigned work before
  anyone commits.
- B5 — Every gate names its required environment explicitly; skip-as-pass is a
  red gate. Evidence older than the last code change touching its area is stale:
  re-run it. Nothing is marked complete from memory.
- B6 — Collect all audit verdicts before dispatching fixes; then consolidated fix
  waves, one redeploy per wave, not per fix.
- B7 — One driver per branch/worktree; the session registry in CURRENT is the
  ledger; a stand-down handshake precedes any relaunch of a presumed-dead session.
- B8 — Crash posture: commit from the first work block; any task over ~30 minutes
  is resumable from its commits; a redispatch resumes from HEAD, never rebuilds.
- B9 — Guardrails from session one: environment pin, destructive-command deny
  list, secrets placement, operator items never silently attempted.
- B10 — Memory is not policy: a binding lesson is promoted into the constitution
  or an agent definition (or declined with a reason) before the next milestone
  closes; until promoted, it steers nothing.
- B11 — New goals mid-run go to chartered child sessions with their own charter
  document and progress ledger, plus one pointer line in the parent CURRENT.
- B12 — Checkpoint asks are numbered so answers map to decisions. Quiet hours and
  the severity that may break them are declared; notification uses the host's
  available channel, else a flagged BLOCKED line atop the status artifact. A
  pending ask parks its thread; non-blocked work continues; the wait is recorded
  in CURRENT.
- B13 — The operator sees the product early: a per-milestone operator-consumable
  artifact appropriate to the project type (preview URL, installable build, or
  runnable demo script), plus scheduled operator experience passes the loop
  cannot skip — the first one early, on the core user journey.
- B14 — Every agent definition ships a `tools:` allowlist; no MCP tool enters one
  without proven need; implementation and audits go to the named agents, never a
  general-purpose spawn.

## Reflection clause (the pack's slot)

Every pack carries a reflection clause: on a cadence — **default: milestone close
or 24 hours, whichever comes first** — an independent fresh-context session reads
bounded inputs and produces two artifacts with different disposal semantics: a
**curated lesson store** (adopt-or-discard; adoption is an explicit recorded swap,
never a default) and an **orchestration-drift audit** filed append-only under
`audits/` with severities, never discardable. The staleness watchdog (G4) is the
third leg of external checking: deterministic gates catch bookkeeping decay,
scheduled fresh-context reflection catches judgment drift, and the dumb scheduled
watchdog catches orchestrator death. External checking is a cadence, not a
resident: no standing co-operator agent is added. The full reflection contract
ships as its own reference protocol in this `references/` directory; packs point
at it once it exists.

## Traceability

Every audit finding (P0-1..P3-9) and every template rule (T1..T15) maps to the
pack clause or gate that encodes it. `scripts/test_orchestration_reference.py`
parses this table; no row may be missing or empty.

| ID | Pack clause / gate |
|---|---|
| P0-1 | G1 C1 + C2 (evidence committed, audit reports filed) under G2 red-gate disposition; launch gate = green-or-dispositioned at HEAD |
| P0-2 | G3 regression-harness contract: `stage >= milestone` assertions, self-seeded persistent fixtures |
| P0-3 | G1 C3 (CURRENT SHA = git HEAD) + B1 (CURRENT updated in the merge commit) |
| P1-3 | G1 C4 (MILESTONES table must agree with git tags) |
| P1-4 | State-file contract d7 (continuity buffer newest-first, rotated daily, ~8KB hard cap) |
| P1-5 | G1 C2 (a milestone tag blocks without a filed per-auditor audit report) |
| P1-6 | G1 C5 (closed milestone requires a LOG entry) + C6 (CURRENT line cap) |
| P2-7 | G1 C1 (uncommitted verification/ or audits/ files fail the gate) |
| P2-8 | G1 C7 (state-file line-length cap ~500 chars) |
| P3-9 | G1 W1 + W2 (warn on unpushed main/tags and undeleted merged milestone branches) |
| T1 | Pack component (c) + B14 (tools allowlist on every agent definition from day one) |
| T2 | Pre-flight checklist (f): host MCP/plugin disable list + injected-catalog size audit |
| T3 | B2 context economy (findings-only reports, gate tails not logs, delegated reads) |
| T4 | B3 report contract (summary + SHAs + gate tails, never diffs or logs) |
| T5 | B7 one-writer serialization per branch/worktree |
| T6 | B4 release-once |
| T7 | B5 named gate environment, skip-as-pass-is-red, evidence freshness rule |
| T8 | Pack component (b): the milestone loop with RECORD explicit, one line per step |
| T9 | B6 collect-all-verdicts-before-fix-waves |
| T10 | Pack components (e) + (f) + B9 (guardrails digest, numbered checkpoints, operator items never silently attempted) |
| T11 | B10 memory-is-not-policy promotion rule |
| T12 | State-file contract d1 (CURRENT ≤25 lines, updated at every loop-step boundary), enforced by G1 C6 |
| T13 | B2 delegated pixel judgment (orchestrator consumes verdicts, ≤1 composite image per milestone) |
| T14 | B8 crash posture: commit from the first work block; tasks over ~30 minutes resumable from commits |
| T15 | B8 redispatch resumes from HEAD, never rebuilds |

## Decoupling

This file and every pack Mode C emits are project-agnostic: no client, company,
campaign, or product names; the field evidence is referred to only generically.
Everything project-specific (names, stack, gate commands, deploy targets,
checkpoint owners, quiet hours) enters a pack only from the user's brief or
`omnitune.config.yaml` — never from this file.
