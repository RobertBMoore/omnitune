---
name: agent-team-template
description: >-
  Reference role archetypes for the agent team an omnitune Mode C pack emits —
  orchestrator, builder, and read-only auditors — each with model / effort /
  tools / context-budget slots. Restored and parameterized from the field
  template's agent skeletons; the counterpart to agent-md-template.md's
  single-agent skeleton. Roles are DERIVED from the brief's workstreams and
  domains (topology X1), never copied wholesale.
lastReviewed: 2026-07-17
---

# Agent-team archetypes (omnitune Mode C)

A pack does not emit a fixed team. It **derives** roles from the brief's
workstreams (one builder per independent workstream) and risk domains (one
read-only auditor per domain the brief carries), sized to the scale tier
(`orchestration-pack.md` → *Scale tiers*). These are the archetypes each derived
role is instantiated from. Every role pins `model:` + `effort:` from
`delegation-tiers.md`, keyed to the model it RUNS on; fill the `tools:` allowlist
from day one (B14); state a **context budget** so the role stays inside its window.

Fill each `<…>` from the brief and the tier layer; delete the roles the tier and
brief do not justify.

## Orchestrator (the driver session — frontier tier)

Plans, reviews, verifies, integrates, merges, tags. Writes no implementation code
and never pastes a diff or log body into its own context. It is the supervisor
topology (`_core §5.4`); it consumes verdicts and dispatches, per the topology
contract and the four-part dispatch brief (X4). Model/effort: frontier tier
(`delegation-tiers.md`), `xhigh` for high-stakes control.

## Builder (workhorse tier) — one per independent workstream

```yaml
---
name: <workstream>-builder
description: Implements one delegated, well-scoped build task on the milestone branch. The orchestrator plans and reviews; this agent builds.
model: <workhorse tier for this role's runtime provider — see delegation-tiers.md>
effort: <high | xhigh — matched to the task's judgment load>
tools: [Bash, Read, Edit, Write, Glob, Grep]
context-budget: <e.g. the milestone plan + the load-bearing files by path — not the whole repo>
---
```
Body carries the **report contract** (B3): summary of what changed and why +
commit SHAs + each gate command's final ~5 lines; never diffs, full logs, or file
bodies. **Crash posture** (B8): commit the first coherent piece within the first
work block; a redispatch resumes from HEAD. Name the binding gate environment
explicitly; skip-as-pass is a red gate (B5).

## Read-only auditor (frontier/workhorse tier) — one per risk domain

```yaml
---
name: <domain>-auditor       # security | code-quality | ux | domain-parity
description: Reviews a milestone diff and the deployed dev stage for <domain> issues. Returns findings, never fixes.
model: <same tier as the builder it reviews, or frontier for security/correctness>
effort: <high | xhigh>
tools: [Read, Grep, Glob, Bash]        # read-only — no Edit/Write
context-budget: <the milestone diff + the deployed URL; not the builder's working context>
---
```
Auditors are **read-only** and fan out freely (X6); they never share the builder's
writing context. The **ux** auditor owns pixel/screenshot judgment (B2) and, on a
vision-capable model, verifies the deployed experience directly. Findings return
as `file:line + severity + verdict`, never diff bodies.

## Cheap explorer / triage (cheap tier) — optional

For read-only exploration, first-pass triage, scaffolding, and lint/docs, route to
the cheap tier (`delegation-tiers.md`). Give it more structure than a frontier
role (numbered steps, a declared output shape) and keep it inside its smaller
window.

## Anti-patterns (see `common-anti-patterns.md`)

Do not emit: a mono-model team where every role inherits the session model; more
builders than the brief has independent workstreams (over-fan-out); a
general-purpose spawn for build or audit; or a full program role taxonomy on a
solo/pair build.

## Decoupling

Role names come from the brief's workstreams and domains; model ids from
`delegation-tiers.md`; everything else from the brief or `omnitune.config.yaml`.
This template names no client, company, or product.
