---
name: description-authoring-guide
description: How to write a SKILL.md / agent description that triggers reliably, used by omnitune Mode A for Dimension 5 findings.
lastReviewed: 2026-06-14
---

# Description authoring guide

The `description:` field is the trigger contract. The Skill tool fires on lexical match against user intent, so the description must carry the words users actually type.

## A strong description has three parts
1. **What it does** — one specific clause. Not "handles workflows"; say what it produces.
2. **When to use it** — the situations it fires on (and, if useful, what it does NOT cover).
3. **Explicit triggers** — end with: `Triggers on prompts like "<phrase>", "<phrase>", "/<command>".`

## Rules
- **≥ ~40 words.** Shorter descriptions under-trigger.
- **Active voice, second person where natural.** Avoid third-person-passive ("This skill is used to…").
- **Use the user's words, not your internal names.** If users say "rewrite this prompt," the description must contain "rewrite this prompt," even if the skill is named `tune-prompt`.
- **List real invocation variants.** Cover the common phrasings, including slash commands.

## Before / after
**Before:** `description: Handles prompt improvement.`
**After:**
```yaml
description: >-
  Rewrites an ad-hoc prompt into optimized form for the current model, self-scored
  in a QA loop before presenting. Use when a prompt is vague, under-specified, or
  about to run against a real task. Triggers on prompts like "improve this prompt",
  "rewrite this for the model", "what's wrong with this prompt", "/omnitune:tune-prompt".
```

## Scoring (Mode A, Dimension 5)
- Triggers cover the real phrasings users type (from `--sample-prompts`, the existing examples, or heuristic) → 5.
- Misses a common variant → 3. Doesn't match real usage → 1.
