---
model: gpt-5.4
provider: openai
family: gpt-5
status: limited
source_status: synced-from-docs
citation_gate: strict
extends: _core.md
lastSynced: 2026-06-29
lastReviewed: 2026-06-29
sources:
  - https://developers.openai.com/codex/models
  - https://developers.openai.com/codex/learn/best-practices
  - https://developers.openai.com/api/docs/guides/latest-model
---

# Rubric — GPT-5.4 (prior Codex flagship)

Read `_core.md` (the OpenAI provider core) first; this file adds only the GPT-5.4 calibration. Source legend (the full tag legend lives in `_core.md`): `[MD]` codex/models · `[BP]` codex/learn/best-practices · `[LM]` api/docs/guides/latest-model (Using GPT-5.5). A `(verify)` tag marks a claim **not** stated verbatim in the cited docs — surfaced for human review, never a real source tag. Because the `gpt-5.4`-family ids (`gpt-5.4`, `gpt-5.4-mini`, `gpt-5.3-codex-spark`) are prior/forward-dated, any claim naming one of them that a published page cannot state verbatim carries `(verify)`; a real tag is used only where the cited page genuinely covers the claim — the GPT-5.5 guidance it is about, or the general Codex best-practices ladder.

**Controlling fact:** OpenAI recommends starting from `gpt-5.5` for most Codex work and migrating legacy prompts to its contract rather than porting verbatim `[LM]`; `gpt-5.4` is a prior Codex flagship, so tune it only for workflows still pinned to it `(verify)`.

## Model-specific calibration (augments the OpenAI core)

- Default new Codex work to `gpt-5.5` `[MD]`; reach for `gpt-5.4` only when a workflow is explicitly pinned to it `(verify)`.
- `gpt-5.4` is superseded by `gpt-5.5` as the recommended default — treat any 5.4-specific tuning as legacy maintenance, not the forward target. `(verify)`
- Migrate `gpt-5.4` prompts to 5.5's contract rather than porting them verbatim; 5.5 is a new family, not a faster 5.4. `[LM]`
- Apply the OpenAI core's two separate levers — follow the `reasoning.effort` / `text.verbosity` ladder and re-evaluate before escalating rather than assuming a fixed default `[BP]`; this rubric assumes `gpt-5.4` exposes the same controls as the documented Codex family `(verify)`.
- Route subagent / latency-sensitive steps to `gpt-5.4-mini`, which OpenAI positions for responsive coding tasks and subagents. `(verify)`
- `gpt-5.3-codex-spark` is a text-only research preview for near-instant iteration — not a drop-in for file-editing agentic work. `(verify)`
