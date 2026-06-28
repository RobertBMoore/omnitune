---
name: skill-md-template
description: Reference skeleton for a well-formed SKILL.md, used by omnitune Mode A to score structure and completeness.
lastReviewed: 2026-06-14
---

# SKILL.md template

A strong `SKILL.md` has these parts. Mode A scores a target against this shape.

```markdown
---
name: <matches the directory name>
description: >-
  <40+ words. What the skill does + when to use it. End with explicit triggers:
  "Triggers on prompts like '<phrase>', '<phrase>', '/<command>'.">
---

# <name> — Agent Skill

## When to Use This Skill
<One short paragraph: the situations this fires on, and the situations it does NOT.>

## First Action
<Read these files, in order — a short numbered list. Load context before acting.>

## <Core workflow>
<Numbered steps when order matters. Imperative verbs. State scope explicitly.>

## Documentation Router  (only if the skill spans multiple reference files)
| Task | Read |
|------|------|
| <task> | <file(s)> |
Keep it ≤12 rows; rows must not thematically overlap.

## Definition of Done
<An explicit, checkable "done" statement.>
```

**Scoring notes for Mode A:**
- Frontmatter present + `description` ≥ ~40 words with trigger phrases → D2/D5.
- First Action loads context before acting → D1.
- Router ≤12 non-overlapping rows → D2/D6.
- Definition of Done present → D1 (anti-pattern #10).
- Main file focused (heavy reference factored into `references/`) → D3.
