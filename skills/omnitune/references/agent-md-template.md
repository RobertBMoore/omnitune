---
name: agent-md-template
description: Reference skeleton for a well-formed agent (.md) file, used by omnitune Mode A to score subagent system prompts and by Mode C to shape each pack agent definition.
lastReviewed: 2026-07-17
---

# Agent .md template

An agent file is a **subagent system prompt** loaded into isolated context with no memory of the caller. It must restate everything the subagent needs.

```markdown
---
name: <agent-name>
description: <when the parent should dispatch this agent; include example trigger situations>
tools: [<the minimum tools this agent actually uses>]
model: <the model this agent RUNS on, keyed to its tier — see references/delegation-tiers.md; use `inherit` only with a stated reason>
effort: <low | medium | high | xhigh — matched to the role's judgment load>
---

# <Agent name>

## Role
<One paragraph: what this agent is for, and what it is NOT for.>

## Context you do not inherit
<Restate working directory, branch/SHA, relevant paths, and any project conventions
BY NAME — the subagent cannot see the caller's state.>

## Task
<Numbered, imperative steps. State scope explicitly.>

## Before you begin
<One clarifying-question gate if the task is ambiguous — guessing is costly.>

## Success criteria
<Checkable list. "Done when: …">

## Return format
<Status (DONE / DONE_WITH_CONCERNS / BLOCKED / NEEDS_CONTEXT), what was done,
key findings, absolute file paths. Concise — no preamble.>
```

**Scoring notes for Mode A (agents):**
- `tools:` matches instructed behavior exactly → D4.
- `model:` + `effort:` present and matched to the role's tier — not silently inheriting the caller's model — → delegation tiering (`delegation-tiers.md`). Every-role-on-one-tier without a stated reason is a finding.
- Inherited-context restated by name (no "follow the project conventions" without saying what they are) → D1/D6.
- Clarifying-question gate present → Core §6.7.
- Success criteria + concise return format → anti-pattern #10, Core §6.9.

**For Mode C (orchestration packs):** `model:` and `effort:` are required, not optional — they are the channel a pack uses to express tiering (orchestrator on the frontier tier, builders on the workhorse tier, explorers/auditors on the cheap tier). Resolve each from `references/delegation-tiers.md`, keyed to the model that role RUNS on (which may differ from, or be a different provider than, the generating session's model). The four-part dispatch brief (objective · output format · tools/sources · boundaries) belongs in the Task section for any dynamically-dispatched delegation, because the subagent inherits nothing.
