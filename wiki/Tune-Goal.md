# Tune Goal — from brief to operating system

`/omnitune:tune-goal` is Mode C: it turns a project brief into a launch-ready orchestration pack for the model your session is running.

The result is not another giant prompt. It is an operating system for the work: a statute for the goal, a short constitution for every session, bounded builder/auditor roles, resumable state, human checkpoints, guardrails, and runnable record/liveness gates.

> **Launch-ready means ready for operator pre-flight.** Mode C does not deploy, approve production, or replace the project's own tests, security review, or release judgment.

## When it earns its weight

| Use `tune-goal` when… | Use something lighter when… |
|---|---|
| Work spans multiple milestones, sessions, agents, or worktrees | One focused task can finish in the current session — use `tune-prompt` |
| A deploy, migration, launch, or human approval can block progress | You want to improve an existing reusable instruction file — use `tune-skill` |
| State must survive context compaction or an interrupted orchestrator | There is no durable state, checkpoint, or handoff to manage |
| Parallel work needs ownership, evidence, and integration discipline | A normal issue checklist already contains everything the work needs |
| The operator needs quiet hours, status visibility, and early product passes | The task has no operational lifecycle after the answer is returned |

Mode C is especially useful for Git-backed product builds, large migrations, multi-agent refactors, and launch programs where “done” must be demonstrated at milestones rather than remembered in chat.

## How the flow works

1. **Intake gate.** Mode C maps the brief and asks numbered questions for any required launch fact it cannot find. It does not silently invent commands, URLs, owners, cadence, or scope.
2. **Model shaping.** The provider-shared pack contract is combined with the active session model's rubric. Delegation, effort, verbosity, and instruction shape are model-specific; project facts are not.
3. **Seven-part emission.** It creates every required component and instantiates the two dependency-free gate scripts.
4. **Self-check.** It walks contract traceability, checks the fabrication ledger and component/line caps, then runs `python3 -m py_compile` and `bash -n` on the emitted gates.
5. **Operator handoff.** It presents the pre-flight checklist first, followed by reserved decisions, assumptions, and the file list. An unresolved self-check failure is named and is never treated as ready.

With `output.packs` configured, packs save under a dated subdirectory; an existing configured destination is preserved by appending `-v2`, and so on. A target directory named in the brief wins. Without config, Mode C presents the pack in chat and offers to save it.

## The seven-part pack

| Component | What it makes durable |
|---|---|
| Goal prompt | Mission, milestones, per-milestone reading map, state schema, numbered checkpoints, and definition of done |
| Constitution | A short auto-loaded operating contract: resume rules, loop, precedence, evidence, context economy, delegation, and guardrails |
| Agent definitions | Scoped builders and read-only auditors with explicit tool allowlists, crash posture, and a compact report contract |
| State-file contracts | CURRENT, MILESTONES, LOG, DECISIONS, BACKLOG, live-session registry, and a capped continuity buffer |
| Guardrails digest | Environment pin, destructive-command controls, secret placement, and operator-only actions from session one |
| Operator pre-flight | Plugins/MCPs to disable, catalog-size audit, blocking checkpoints, experience-pass calendar, and quiet hours |
| Gate scripts | `record_check.py` for record discipline and `staleness_watchdog.sh` for an externally detectable stale heartbeat |

The pack also carries a fresh-context reflection clause. By default, at milestone close or 24 hours, it curates bounded session lessons into an adopt-or-discard store and always files an append-only orchestration-drift audit. Memory becomes policy only after explicit promotion; the reflection is a cadence, not a resident co-orchestrator.

## Give it these six things

A rough brief is acceptable — Mode C will ask for gaps — but the strongest first pass names:

1. **Deploy target:** stages, deploy commands, and the dev URL used for verification.
2. **Gate commands:** lint, test, and end-to-end commands plus the environment each requires.
3. **Checkpoint ownership:** who answers each numbered decision and where.
4. **Quiet hours:** the no-interrupt window and the severity allowed to break it.
5. **Milestones:** phases or enough bounded scope for Mode C to propose them.
6. **Target directory:** where the pack should be saved.

Name environment variables, never secret values. Put credentials in the project's secret store and describe only the contract the agents must follow.

## Worked example — complete intake

This example is intentionally fictional and uses the reserved `.example` domain. It demonstrates the level of operational specificity that produces the best first pass without including any private project, person, account, or filesystem path.

```text
/omnitune:tune-goal "
Project: FieldNotes (fictional), a members-only gardening-club web app for plot
observations and photos.

Outcome: ship a small, maintainable v1 with authentication, observation CRUD,
photo uploads, and a verified release.
Stack: SvelteKit + SQLite.
Out of scope: billing, public profiles, and social feeds.
Secrets: GitHub Actions environment secrets; never put values in code, logs,
commits, chat, or the pack.

Deploy targets:
- dev VPS: ./scripts/deploy-dev.sh; verify at https://dev.fieldnotes.example
- production: ./scripts/deploy-production.sh, blocked until CP3

Required gates (run from the repo root):
- npm run lint (no environment variables)
- DATABASE_FILE=.data/test.sqlite npm test
- BASE_URL=https://dev.fieldnotes.example npm run e2e

Milestones: M0 scaffold; M1 auth; M2 observations CRUD; M3 photo uploads;
M4 launch.

Operator checkpoints, all owned by the project operator in this task chat:
- CP1 approve environment/config before the first dev deploy
- CP2 approve DNS before M4 end-to-end verification
- CP3 approve launch before any production deploy

Status/liveness:
- update status/CURRENT.md every 30 minutes while work is active
- run the external watchdog every 10 minutes and alert this task chat after
  45 minutes without a heartbeat

Milestone auditors: one read-only code auditor and one read-only UX auditor.
Quiet hours: 22:00–07:00 UTC; only a P0 may interrupt.
Operator experience pass: desktop + mobile after M2.
Save the pack under docs/orchestration/fieldnotes/.
"
```

## What that brief becomes

| Brief fact | Required pack behavior |
|---|---|
| Production deploy is blocked until CP3 | The goal and pre-flight checklist record production as blocked pending CP3 and forbid silent approval |
| `npm test` needs `DATABASE_FILE` | The gate contract names the environment explicitly; skip-as-pass is red, and stale evidence must be rerun |
| M0 through M4 are named | The mission and MILESTONES table use the same progression; the record gate cross-checks tags, closed rows, LOG entries, clean evidence directories, and filed auditor reports |
| The operator owns CP1–CP3 in chat | Pending asks park only the blocked thread, are recorded in CURRENT, and leave unrelated work moving |
| Quiet hours permit only P0 interruptions | Notification behavior and break-glass severity become binding operating rules |
| Desktop + mobile pass follows M2 | The operator sees the product early through a scheduled experience checkpoint rather than only at launch |
| A dev URL is supplied | End-to-end evidence is tied to a named target instead of an agent-chosen environment |

That is the power shift: prose such as “keep me updated,” “run the tests,” or “do not launch without me” becomes explicit state, ownership, evidence, and gates that survive a fresh session.

## What quality is mechanically checked

Mode C performs a structural self-check before handoff: seven components, traceability, the fabrication ledger, line caps, and gate-script syntax. The repository's CI separately fails if any of 25 traceability mappings or seven reflection-contract rows is missing or empty, or if either shipped gate template fails Python/Bash syntax checks.

Those checks are meaningful but bounded. They detect missing/empty mappings and syntax regressions; they do not generate a golden pack, validate template semantics or your deploy commands, or guarantee the resulting product. Project lint/tests/e2e, security review, operator pre-flight, and launch approval remain authoritative.

A shorter FieldNotes brief also appears in the Mode C regression corpus. That fixture protects coverage classification, not a golden generated output. To run the structural contract check directly:

```text
cd scripts
python3 -m unittest test_orchestration_reference
```

## Best-use checklist

1. Start Mode C before implementation, not after orchestration has already drifted.
2. State outcome and non-goals so the pack can prevent scope creep.
3. Supply exact gate commands and environment names; never paste credentials.
4. Use role names instead of personal details unless the project truly requires named owners.
5. Make checkpoints block a specific action rather than saying “ask me when needed.”
6. Review reserved decisions and assumptions before launching any agent.
7. Wire the watchdog to a scheduler and alert channel; the script cannot schedule itself.
8. Use a Git repository; `record_check.py` fails closed without one.
9. Keep the project's own CI, security controls, and release approval in force.

For a minimal first run, point the command at an existing brief and name a safe output directory:

```text
/omnitune:tune-goal "Use docs/project-brief.md as reference data. Ask numbered
questions for missing launch facts, then save the pack under docs/orchestration/."
```
