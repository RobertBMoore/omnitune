---
name: tune-goal-protocol
description: omnitune Mode C — turn a project brief into a launch-ready orchestration pack for the session model, gated by a brief-intake question step and a fabrication ledger, self-checked against the pack contract's traceability list before presenting. Repo-agnostic; the pack contract comes from references/orchestration-pack.md, output paths from omnitune.config.
lastReviewed: 2026-07-17
---

# Tune-Goal Protocol — omnitune Mode C

Emit a launch-ready orchestration pack from a project brief. The pack contract —
components, the topology contract, mechanized gates, binding rules, reflection
clause — is `references/orchestration-pack.md`; it is provider-shared and
model-agnostic. Team composition comes from two model-shaped sources: the
**delegation-tier layer** (`references/delegation-tiers.md`) supplies who runs
what (per-role model + effort), keyed to the model each role runs on; each
runtime role's **rubric** supplies that model's fan-out posture and register.
The pack is not presented until it passes the self-check pass (step 3).

## Step 0 — Brief intake gate (run FIRST)

The input is a project brief. A pack needs, at minimum — **recording / operations facts:**

1. **Deploy target** — stage names, deploy command, and the dev URL verification runs against.
2. **Gate commands** — lint / test / e2e commands, and the required environment each must name (the skip-as-pass rule needs the names).
3. **Checkpoint owners** — who answers each numbered checkpoint, and on what channel.
4. **Quiet hours** — the operator's quiet window and which severity may break it.
5. **Milestone shape** — the phases/milestones, or enough scope to propose them.
6. **Target directory** — where the pack files land (see step 2 defaults).

And **team-design facts** (garbage-in for topology without them — a perfect emitter still cannot tier a team it was never told can run cheaply, split workstreams it was never told are independent, or right-size apparatus for a scale it never asked about):

7. **Scale** — max concurrent writers/agents **and** horizon in days. These pick the **tier**: **Solo/Pair** (≤1 concurrent writer or ≤~3 days), **Squad** (2–4 writers or ~1–3 weeks, the default), **Program** (5+ agents or 3+ weeks). The tier gates which components, state files, gates, and roles emit (see `orchestration-pack.md` → *Scale tiers*).
8. **Workstream independence** — which workstreams have independent context (can run in parallel on isolated worktrees) vs must serialize. Drives role count and decomposition (topology X1/X5/X6).
9. **Required specializations** — which audit/domain roles the brief needs (security, code-quality, ux, domain-parity). Absent roles are not emitted; a named risk domain with no owner is a gap to surface.
10. **Runtime model set** — which model(s)/provider(s) each role will **run** on (accept a multi-provider set: Claude + GPT + Grok). This is independent of the generating session's model and selects each role's `model:`/`effort:` from `delegation-tiers.md` and its fan-out posture from that model's rubric (topology X2/X3/X7). Default to the session model only where a role is unpinned.
11. **Audit rigor** — how much milestone auditing the operator wants; sets record_check's `tier` and (at Squad) which milestones are user-facing/risky (C2 proportionality).

If the brief lacks any of these, ask **numbered questions** so answers map to
items — do not proceed on invented values. When scale is unstated, **propose a
tier from what the brief implies (default Squad) and ladder it** ("I assumed:
Squad tier — 2–4 writers, ~2 weeks — confirm or correct"); never silently apply
Program apparatus to a pair build. **Fabrication-ledger discipline (as in
Mode B) is non-negotiable:** every specific in the emitted pack (name, command,
URL, cadence, cap, owner) is either **(a) cited** to the brief or
`omnitune.config`, or **(b) laddered** in an Assumptions block ("I assumed: <X> —
confirm or correct"). Contract defaults from `orchestration-pack.md` (line caps,
the reflection cadence of milestone close or 24h, the ~8KB buffer cap) are cited
to that file, not laddered. A specific that is neither cited nor laddered is a
fabrication and fails the self-check.

## Step 1 — Load the knowledge sources, the tier layer, and the team's rubrics

Read, in order:

1. `references/orchestration-pack.md` — end to end: the pack contract (components
   a-g), the **topology contract** (points X1-X11), the **Scale tiers** section,
   gates G1-G4, binding rules B1-B14, the reflection clause, the traceability
   tables.
2. `references/reflection-protocol.md` — the local-Dream contract (points R1-R7)
   the pack's reflection clause inherits; read when emitting component (b)/(g)
   so the clause is complete, not a stub.
3. `references/delegation-tiers.md` — the delegation-tier layer: role →
   recommended model + effort per provider. This is where per-agent `model:` /
   `effort:` come from (topology point X3), keyed to the model each role RUNS on.
4. The **runtime team's** rubrics — for **each distinct model** in the Step-0
   runtime model set (which may span anthropic / openai / xai), load
   `references/rubrics/<provider>/<model>.md` + that provider's `_core.md`,
   resolving each id with `scripts/resolve_model.py`. The generating session's
   rubric is loaded too, but it is only one of the set: a team generated on Opus
   that runs builders on Fable and an auditor on Grok needs all three rubrics.

The delegation-tier layer (3) supplies **who runs what** — the per-role model and
effort. Each role's rubric (4) supplies that model's **fan-out posture** — the
degree of fan-out (more vs fewer subagents), blocking vs async dispatch,
long-lived vs disposable workers — plus its effort/verbosity, register, and
structure guidance. The rubric never names which model runs a role; the tier layer
never sets fan-out posture. Where the tier layer or a rubric is silent — or a
role's runtime model is unpinned — ladder the choice as an assumption in the
fabrication ledger.

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

1. **Traceability walk.** Walk every row of `orchestration-pack.md`'s recording
   traceability table (P0-1..P3-9, T1..T15): the clause or gate it names must be
   present in the emitted pack as a gate script check or a binding constitution
   rule. An invariant present only as prose-only policy is a failure. (The
   topology table X1..X11 is walked in Step 3.5.)
2. **Gate scripts runnable.** Run `python3 -m py_compile` on the emitted
   `record_check.py` and `bash -n` on the emitted `staleness_watchdog.sh`; both
   must pass. Quote the command tails as evidence.
3. **Fabrication ledger clean.** Every added specific is cited or laddered; the
   Assumptions block is complete.
4. **Completeness.** All seven components (a–g) exist; the constitution is under
   ~90 lines; the CURRENT schema caps at 25 lines.

If a check still fails after fixing, present the pack with verdict
**CONDITIONAL**, naming each failing check in one line — never silently ship.

## Step 3.5 — Topology self-check (the design-fitness supervisor)

The recording self-check (Step 3) validates *mechanics*; this validates the
*team*. It is the orchestration-fitness review at emit time — the t0 supervisor
the operator asked for. Walk the topology table X1..X11; a pack that fails any of
these is not READY:

1. **Model + effort on every agent.** Every agent definition carries `tools:`
   **and** an explicit, justified `model:` + `effort:` (X2). A team on one tier for
   every role fails unless the pack states why (X2/X3).
2. **Roles map 1:1 to the brief.** Every emitted role owns a workstream or a risk
   domain (no unmapped role); every risk domain the brief names has an owner (no
   unowned domain) (X1). No general-purpose spawn for build or audit (B14).
3. **Fan-out matches the runtime rubric.** Each role's fan-out posture, async/blocking
   dispatch, and disposable/long-lived stance match *that role's model's* rubric
   Delegation-defaults — not the generating model's (X7). A Fable-5-run role
   carrying Opus's "fewer subagents / blocking barriers" is a failure.
4. **Fable-5 emission scan.** For any role that runs on Fable 5: scan the emitted
   agent/goal prose for reasoning-extraction triggers ("show / echo / narrate your
   reasoning") → a HIGH failure (refusal trigger); and require the long-async
   affordances (send-to-user, don't-end-on-a-promise, final-response re-grounding).
5. **Cross-provider portability.** When roles span providers, flag any assumed-portable
   capability — a structured-output gate, a vision-based UX audit, or
   reasoning-extraction-sensitive prose — that one role's model may not support.
6. **Serialization split intact.** Correctness serialization (X5, one writer per
   file/branch) is present and unconditional; any relaxed throughput serialization
   (X9/B6) is justified by the runtime rubric's async posture, not improvised.

A topology failure yields the same **CONDITIONAL** verdict as a recording failure,
naming each failing check in one line — never silently ship a mis-designed team.

Present, in this order:

1. The **numbered operator pre-flight checklist** (component f) — host MCP/plugin
   disable list, injected-catalog size audit, checkpoints and what each blocks,
   device-pass calendar, quiet hours and break-glass severity.
2. The pack's **reserved decisions** — anything the brief left open that the pack
   parked rather than guessed (e.g. unconfirmed checkpoint owners, the watchdog's
   scheduling mechanism and alert channel, notification wiring), each as a
   numbered ask. **Always include the supervision fork** when scale is near/at
   program (10+ agents): the layered oversight cadence (default) vs a standing
   "Co-Operator"/hierarchical supervisor — present it, do not decide it silently.
3. The **Assumptions block** from the fabrication ledger — including the scale
   tier if it was laddered and each role's runtime model where it was assumed.
4. The file list (or the offer to save, in standalone mode).

## Definition of Done

- Brief gaps were asked as numbered questions (or the brief supplied everything).
- The pack contains all seven contract components, written per the meta-rules.
- The self-check passed: recording traceability clean, gate scripts compile/lint,
  no unlisted fabrications, **and the Step 3.5 topology self-check passed** (every
  agent tiered and justified, roles map 1:1 to the brief, fan-out matches each
  runtime rubric) — or the verdict says CONDITIONAL and names the failures.
- The pre-flight checklist, reserved decisions, and assumptions were presented.
- Files were written to the target directory when one was named or configured;
  otherwise the pack was presented in chat with an offer to save.
