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

## Delegation defaults (Mode C teams)

When GPT-5.5 runs a role in a Mode C team, this is its fan-out posture (the tier layer in `references/delegation-tiers.md` sets who runs what):
- **Tier position:** frontier + workhorse — the recommended Codex flagship, the right model for the orchestrator/lead and hard reviews, and a strong builder at a lower effort. `[MD]`
- **Route the cheap leg down:** send subagent / high-volume / latency-sensitive steps to `gpt-5.4-mini`, which OpenAI positions for responsive coding and subagents. `(verify)`
- **Effort is the fan-out dial as much as the depth dial:** start build roles at low/medium effort and raise for cross-file or debugging work; a scoped dispatch brief (goal · context · constraints · done-when) keeps a worker on-task. `[LM]`
- **Not a drop-in for 5.4:** migrate a legacy team's role prompts to 5.5's contract rather than porting them verbatim. `[LM]`
