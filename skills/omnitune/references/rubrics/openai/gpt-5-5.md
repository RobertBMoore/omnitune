---
model: gpt-5.5
provider: openai
family: gpt-5
status: ga
source_status: synced-from-docs
citation_gate: strict
extends: _core.md
lastSynced: 2026-06-28
lastReviewed: 2026-06-28
sources:
  - https://developers.openai.com/codex/models
  - https://developers.openai.com/codex/prompting
  - https://developers.openai.com/api/docs/guides/latest-model
---

# Rubric — GPT-5.5 (Codex default)

Read `_core.md` (the OpenAI provider core) first; this file adds the GPT-5.5 calibration. Source legend matches the core: `[CP]` codex/prompting · `[BP]` codex/learn/best-practices · `[MD]` codex/models · `[CG]` cookbook codex prompting guide.

**Controlling fact:** GPT-5.5 is OpenAI's recommended Codex default — "for most tasks in Codex, start with `gpt-5.5`." Tune for it first; it is a new family, not a faster 5.4. `[MD][CG]`

## Model-specific calibration (augments the OpenAI core)

- Default to `gpt-5.5` for Codex work; it is the frontier model in the picker and shipped for Codex on 2026-04-23. `[MD]`
- Start `reasoning.effort` at low or medium and `text.verbosity` at low; raise either only when the result shows it is warranted, not pre-emptively. `[CG]`
- Migrate legacy `gpt-5.2`/`gpt-5.4` prompts toward the outcome-first contract rather than porting them verbatim — 5.5 punishes over-specification with mechanical output. `[CG]`
- Route subagent / high-volume / latency-sensitive steps to `gpt-5.4-mini`, which OpenAI positions for responsive coding tasks and subagents. `[MD]`
- `gpt-5.3-codex-spark` is a text-only research preview for near-instant iteration — not a drop-in for file-editing agentic work. `[MD]`
- Lean on 5.5's metaprompting: when a task is underspecified, have it tighten the prompt/plan before implementing. `[CG]`
