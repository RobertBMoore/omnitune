---
name: tune-goal-protocol
description: omnitune Mode C — turn a project brief into a launch-ready orchestration pack for the session model, gated by a brief-intake question step and a fabrication ledger, self-checked against the pack contract's traceability list before presenting. Repo-agnostic; the pack contract comes from references/orchestration-pack.md, output paths from omnitune.config.
lastReviewed: 2026-07-13
---

# Tune-Goal Protocol — omnitune Mode C

Emit a launch-ready orchestration pack from a project brief. The pack contract —
components, mechanized gates, binding rules, reflection clause — is
`references/orchestration-pack.md`; it is provider-shared and model-agnostic.
Model-specific steering comes from the **session model's** rubric
(`references/rubrics/<provider>/<model>.md` + `_core.md`, selected upstream).
The pack is not presented until it passes the self-check pass (step 3).

## Step 0 — Brief intake gate (run FIRST)

The input is a project brief. A pack needs, at minimum:

1. **Deploy target** — stage names, deploy command, and the dev URL verification runs against.
2. **Gate commands** — lint / test / e2e commands, and the required environment each must name (the skip-as-pass rule needs the names).
3. **Checkpoint owners** — who answers each numbered checkpoint, and on what channel.
4. **Quiet hours** — the operator's quiet window and which severity may break it.
5. **Milestone shape** — the phases/milestones, or enough scope to propose them.
6. **Target directory** — where the pack files land (see step 2 defaults).

If the brief lacks any of these, ask **numbered questions** so answers map to
items — do not proceed on invented values. **Fabrication-ledger discipline (as in
Mode B) is non-negotiable:** every specific in the emitted pack (name, command,
URL, cadence, cap, owner) is either **(a) cited** to the brief or
`omnitune.config`, or **(b) laddered** in an Assumptions block ("I assumed: <X> —
confirm or correct"). Contract defaults from `orchestration-pack.md` (line caps,
the reflection cadence of milestone close or 24h, the ~8KB buffer cap) are cited
to that file, not laddered. A specific that is neither cited nor laddered is a
fabrication and fails the self-check.

## Step 1 — Load the knowledge source and the session rubric

Read, in order:

1. `references/orchestration-pack.md` — end to end: the pack contract (components
   a-g), gates G1-G4, binding rules B1-B14, the reflection clause, the
   traceability table.
2. `references/reflection-protocol.md` — the local-Dream contract (points R1-R7)
   the pack's reflection clause inherits; read when emitting component (b)/(g)
   so the clause is complete, not a stub.
3. `references/rubrics/<provider>/<session-model>.md` + `_core.md` — the rubric
   selected upstream by `SKILL.md` step 2.

The rubric, never this protocol, supplies the model-shaped values: the delegation
default (which model orchestrates, what builders/auditors run on), effort and
verbosity defaults for the agent definitions, register and structure guidance for
the goal prompt and constitution. Where the rubric is silent, ladder the choice
as an assumption.

## Step 2 — Emit the pack

Produce every component of the pack contract (a–g): goal prompt, constitution,
agent definitions, state-file contracts, guardrails digest, operator pre-flight
checklist, gate scripts. Instantiate the gate scripts from
`references/pack-templates/` (`record_check.py`, `staleness_watchdog.sh`), fill
each CONFIG from the brief (file names, line caps, tag prefix, auditor list,
status cadence), and keep them dependency-free.

Writing rules (from the contract's meta-rules): every scriptable invariant lands
as a blocking gate, never policy prose; judgment invariants land as one brief
binding rule each, never enumerated case lists. Everything project-specific comes
from the brief; the pack contains no other proper nouns.

**Where the files go:**
- The user named a target directory → write there.
- Else `omnitune.config.output.packs` is configured → write to
  `<output.packs>/<YYYY-MM-DD>-<slug>/`. Create the directory if missing; never
  overwrite an existing pack — append `-v2` etc.
- Else (**standalone**) → present the pack structure and file bodies in chat and
  offer to save to a directory the user names.

## Step 3 — Self-check pass (before presenting)

Do not present a pack that fails any of these; fix and re-check first.

1. **Traceability walk.** Walk every row of `orchestration-pack.md`'s
   traceability table (P0-1..P3-9, T1..T15): the clause or gate it names must be
   present in the emitted pack as a gate script check or a binding constitution
   rule. An invariant present only as prose-only policy is a failure.
2. **Gate scripts runnable.** Run `python3 -m py_compile` on the emitted
   `record_check.py` and `bash -n` on the emitted `staleness_watchdog.sh`; both
   must pass. Quote the command tails as evidence.
3. **Fabrication ledger clean.** Every added specific is cited or laddered; the
   Assumptions block is complete.
4. **Completeness.** All seven components (a–g) exist; the constitution is under
   ~90 lines; the CURRENT schema caps at 25 lines.

If a check still fails after fixing, present the pack with verdict
**CONDITIONAL**, naming each failing check in one line — never silently ship.

## Step 4 — Present: pre-flight checklist and reserved decisions

Present, in this order:

1. The **numbered operator pre-flight checklist** (component f) — host MCP/plugin
   disable list, injected-catalog size audit, checkpoints and what each blocks,
   device-pass calendar, quiet hours and break-glass severity.
2. The pack's **reserved decisions** — anything the brief left open that the pack
   parked rather than guessed (e.g. unconfirmed checkpoint owners, the watchdog's
   scheduling mechanism and alert channel, notification wiring), each as a
   numbered ask.
3. The **Assumptions block** from the fabrication ledger.
4. The file list (or the offer to save, in standalone mode).

## Definition of Done

- Brief gaps were asked as numbered questions (or the brief supplied everything).
- The pack contains all seven contract components, written per the meta-rules.
- The self-check passed: traceability walk clean, gate scripts compile/lint, no
  unlisted fabrications — or the verdict says CONDITIONAL and names the failures.
- The pre-flight checklist, reserved decisions, and assumptions were presented.
- Files were written to the target directory when one was named or configured;
  otherwise the pack was presented in chat with an offer to save.
