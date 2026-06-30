---
model: gpt-5.5
provider: openai
family: gpt-5
status: ga
source_status: derived-tier
citation_gate: strict
extends: _core.md
lastSynced: 2026-06-28
lastReviewed: 2026-06-30
sources:
  - https://developers.openai.com/codex/models
  - https://developers.openai.com/codex/prompting
  - https://developers.openai.com/api/docs/guides/latest-model
---

# Rubric — GPT-5.5 (Codex default)

Read `_core.md` (the OpenAI provider core) first; this file adds the GPT-5.5 calibration. Source legend: `[CP]` codex/prompting · `[MD]` codex/models · `[CG]` cookbook codex prompting guide · `[LM]` api/docs/guides/latest-model (Using GPT-5.5). A `(verify)` tag marks a claim a published page cannot state verbatim for a forward-dated id — a real tag is used only for GPT-5.5-subject guidance the cited pages are about, or the general best-practices ladder.

**Controlling fact:** GPT-5.5 is OpenAI's recommended Codex default — "for most tasks in Codex, start with `gpt-5.5`." Tune for it first; it is a new family, not a faster 5.4. `[MD][LM]`

## Model-specific calibration (augments the OpenAI core)

- Default to `gpt-5.5` for Codex work; it is the frontier model in the picker. `[MD]`
- Start `reasoning.effort` at low or medium and `text.verbosity` at low (the API default is medium); raise either only when the result shows it is warranted, not pre-emptively. `[LM]`
- Migrate legacy `gpt-5.2`/`gpt-5.4` prompts to 5.5's contract rather than porting them verbatim — it is a new family, not a faster 5.4. `[LM]`
- Route subagent / high-volume / latency-sensitive steps to `gpt-5.4-mini`, which OpenAI positions for responsive coding tasks and subagents. `(verify)`
- `gpt-5.3-codex-spark` is a text-only research preview for near-instant iteration — not a drop-in for file-editing agentic work. `(verify)`
- Lean on 5.5's metaprompting: when a task is underspecified, have it tighten the prompt/plan before implementing. `[CG]`
