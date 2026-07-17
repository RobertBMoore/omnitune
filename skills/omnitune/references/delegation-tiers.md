---
name: delegation-tiers
description: >-
  Knowledge source for omnitune Mode C (tune-goal) — the delegation-tier layer:
  role → recommended model + effort, per provider (anthropic / openai / xai).
  Restores the concrete tiering defaults the template→contract refactor deleted.
  Composed with orchestration-pack.md (the topology contract) and each runtime
  role's own rubric; keyed to the model a role RUNS on, not the generating
  session's model. The session rubric supplies the fan-out posture; this file
  supplies who runs what.
lastReviewed: 2026-07-17
---

# Delegation-tier layer — who runs what (omnitune Mode C)

The pack contract (`orchestration-pack.md`) says every agent definition carries an
explicit, justified `model:` + `effort:` (topology point X2). This file is where
those defaults come from. It is the counterpart the rubric cannot be: a per-model
rubric describes how to prompt *that one model*, so it is the wrong shape to
answer a cross-model, cross-provider *team-composition* question. That question is
answered here.

## The one load-bearing result

> "a multi-agent system with Claude Opus 4 as the lead agent and Claude Sonnet 4
> subagents outperformed single-agent Claude Opus 4 by **90.2%**." — Anthropic,
> *How we built our multi-agent research system*

The lever is **model tiering**: the orchestrator runs on the more capable tier;
workers run on cheaper, faster tiers. A team that defaults every role to the one
session model is the exact single-tier configuration that result beats. Product
defaults already bake this in — Claude Code subagents *"control costs by routing
tasks to faster, cheaper models like Haiku"*, and the built-in Explore agent is
*capped* so read-only work never runs on a more expensive model than needed.

## The three tier roles (provider-general)

| Tier role | What runs here | Why |
|---|---|---|
| **Frontier — orchestrate / hard-audit** | the orchestrator; security/correctness audits on risky milestones | plan, delegate, synthesize, judge — the decisions the whole run rests on |
| **Workhorse — build** | builders/implementers on a scoped milestone task | most tokens, most turns; a strong workhorse is the cost/quality sweet spot |
| **Cheap — explore / triage** | read-only exploration, classification, scaffolding, lint/docs, first-pass triage | high-volume, low-judgment work; the "cheap leg of a multi-model workflow" |

Team size scales with the tier roles, not against them: 1 agent for simple
fact-finding, 2–4 for comparison/parallel workstreams, 10+ only for genuine
program scale. Over-provisioning ("50 subagents for a simple query") is the
#1 named failure — see `common-anti-patterns.md`.

## Per-provider seed defaults

These are **seeds**, not hardcodes: a pack pins each role's model+effort from the
row for the provider that role RUNS on, then the pack's fabrication ledger ladders
any value the brief did not confirm. Effort names are each provider's own ladder.

### anthropic

| Role | Model | Effort | Notes |
|---|---|---|---|
| Orchestrate / hard-audit | `claude-opus-4-8` or `claude-fable-5` | `xhigh` | Fable 5 for long-horizon/async programs; Opus 4.8 for the most literal high-stakes control. Fan-out posture differs — see each rubric's Delegation-defaults block. |
| Build | `claude-sonnet-5` | `high`/`xhigh` | "best combination of speed and intelligence"; the workhorse builder tier. |
| Explore / triage / scaffold | `claude-haiku-4-5` | `medium` | "the cheap leg of a multi-model workflow"; 200k context (not 1M) and a Feb-2025 cutoff — do not hand it 1M-token long-context or post-cutoff-fact tasks. |

### openai

| Role | Model | Effort | Notes |
|---|---|---|---|
| Orchestrate / hard-audit | `gpt-5.5` | `high`/`xhigh` | the recommended Codex flagship; "start with gpt-5.5 for most tasks". |
| Build | `gpt-5.5` | `medium`/`high` | same flagship at a lower effort for scoped build work; raise effort for cross-file/debug. |
| Explore / triage / subagents | `gpt-5.4-mini` | `low`/`medium` | OpenAI positions the mini for responsive coding and subagents `(verify)`. |

### xai

| Role | Model | Effort | Notes |
|---|---|---|---|
| Orchestrate / hard-audit | `grok-4.3` | high | xAI's flagship for Chat and Coding; strong instruction-following rewards an explicit contract. |
| Build | `grok-build-0.1` | medium/high | the dedicated agentic-coding line (successor to grok-code-fast-1) inside Grok Build CLI. |
| Explore / triage | `grok-build-0.1` (low effort) or `grok-4.3` (`reasoning.effort: none`) | low/none | reserve higher effort for debugging and cross-file changes. |

## Scale tier and model tier are independent dials

The scale tier (Solo/Pair · Squad · Program — see `orchestration-pack.md` and the
Step-0 intake) sets *how much apparatus* emits. The model tier sets *what each
role runs on*. They do not move together: a lean Solo/Pair team may still run its
one builder on Haiku or Grok to save cost, and a Program team may still put a
cheap explorer tier under a frontier orchestrator. Pin both, per role.

## Multi-provider teams: the pack IS the substrate

Teams are often *generated* on one model but *run* on others, sometimes across
providers (Claude + GPT + Grok). Two facts govern this:

1. **Native single-vendor orchestration cannot host a mixed team.** Claude Code
   subagents/agent teams accept only Claude ids in `model:`; a Claude-orchestrator
   / GPT-builder / Grok-auditor team needs a model-agnostic layer (the OpenAI
   Agents SDK's per-agent model / a `ModelProvider` / LiteLLM) or manual multi-CLI
   operation. omnitune's **provider-neutral pack** — prose goal-prompt +
   constitution + file-based state + deterministic gate scripts — is *more*
   portable than any native primitive and is therefore the right abstraction for a
   mixed-provider team. (When the whole team is Claude, prefer native primitives —
   see the coordination-substrate section of `orchestration-pack.md`.)
2. **Cross-provider feature parity is not guaranteed.** Structured outputs, vision,
   and reasoning-extraction sensitivity differ across providers. When roles span
   providers, do not assume a capability is portable: a structured-output gate, a
   vision-based UX audit, or reasoning-extraction-sensitive prose may work on one
   role's model and error on another's. The topology self-check flags this.

## How a pack consumes this file

For each role in the emitted team:
1. Read the role's **runtime model** from the Step-0 intake (multi-provider set;
   default to the session model only if the brief pins nothing).
2. Pin `model:` + `effort:` from that provider's row above, keyed to the role's
   tier (orchestrate / build / explore).
3. Draw the *fan-out posture* (more-vs-fewer subagents, async-vs-blocking,
   long-lived-vs-disposable workers) from that model's rubric Delegation-defaults
   block — never from this file. This file sets who runs what; the rubric sets how
   hard they fan out.
4. Ladder any value the brief did not confirm in the pack's Assumptions block.

## A note on the field default

The field template did **not** cost-tier: its builder and auditor skeletons both
ran at the strongest tier (`model: <strongest available builder model>`, auditor
`<same tier as builder>`, both `effort: xhigh`) — a defensible correctness-over-cost
choice for one high-stakes program build, and the wrong default for a cost- or
latency-sensitive team. Tiering is a deliberate per-role cost/correctness decision;
that is exactly why it must be *expressible* in the agent definition and *chosen*
at emit time, not frozen to one tier by omission.

## Decoupling

This file names model ids and providers (the delegation inventory it exists to
carry) but no client, company, campaign, or product names. Everything
project-specific — which model each role runs on, the scale, the effort overrides
— enters a pack from the user's brief or `omnitune.config.yaml`, never from here.
