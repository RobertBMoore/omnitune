---
name: agent-md-template
description: Reference skeleton for a well-formed agent (.md) file, used by omnitune Mode A to score subagent system prompts.
lastReviewed: 2026-06-14
---

# Agent .md template

An agent file is a **subagent system prompt** loaded into isolated context with no memory of the caller. It must restate everything the subagent needs.

```markdown
---
name: <agent-name>
description: <when the parent should dispatch this agent; include example trigger situations>
tools: [<the minimum tools this agent actually uses>]
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
- Inherited-context restated by name (no "follow the project conventions" without saying what they are) → D1/D6.
- Clarifying-question gate present → Core §6.7.
- Success criteria + concise return format → anti-pattern #10, Core §6.9.
