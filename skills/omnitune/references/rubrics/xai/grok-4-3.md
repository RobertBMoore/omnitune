---
model: grok-4.3
provider: xai
family: grok-4
status: ga
source_status: derived-tier
citation_gate: strict
extends: _core.md
lastSynced: 2026-07-03
lastReviewed: 2026-07-03
sources:
  - https://docs.x.ai/developers/models
  - https://docs.x.ai/developers/models/grok-4.3
  - https://docs.x.ai/developers/rest-api-reference/inference/models
---

# Rubric — Grok 4.3 (xAI flagship)

Read `_core.md` (the xAI provider core) first; this file adds the Grok 4.3 calibration. Source legend: `[XM]` docs.x.ai model pages · `[XR]` docs.x.ai REST inference reference · `[omnitune]` omnitune-internal invariant. xAI publishes **no prompting guide** as of 2026-07-03 (models + model-detail pages checked) — platform facts below are sourced; prompting guidance is derived-tier and tagged `[omnitune]` or `(verify)`. Confirm on the next sync.

**Controlling fact:** Grok 4.3 is xAI's current flagship — "leading the industry in non-hallucination rate, agentic tool calling, and instruction following capabilities" — recommended by xAI for both Chat and Coding. Strong instruction following rewards an explicit prompt contract: state Goal/Context/Constraints/Done-when and it will track them precisely. `[XM]`

## Sourced platform facts `[XM]`
- **Context window: 1M tokens;** modalities: text + image input → text output. Max output tokens: not stated on the model page `(verify)`.
- **Capabilities: function calling, structured outputs, reasoning** — all supported. `[XM]`
- **Pricing per MTok: $1.25 input / $0.20 cached input / $2.50 output.** The 6× cached-input discount rewards a stable prompt prefix — keep durable content (system prompt, standards, reference docs) byte-identical across calls and put volatile content last. `[XM]` (placement advice `[omnitune]`)
- **Rate limits as listed on the model page: 37 requests/s, 10M tokens/min** (account tier may vary yours); regions: us-east-1, eu-west-1, us-west-2. `[XM]`
- **Aliases: `grok-4.3-latest`, `grok-latest`** — both are moving targets; pin the exact id in automation and confirm against the live `/v1/models` listing. `[XM][XR]`

## Model-specific calibration (augments the xAI core)
- **Route by tier:** Grok 4.3 is xAI's recommended model for both Chat and Coding `[XM]`. `grok-build-0.1` is positioned as the dedicated agentic-coding line `(verify)` — inside Grok Build CLI / multi-step file-editing workflows prefer it; otherwise default to Grok 4.3, including for coding. (routing judgment `[omnitune]`)
- **Reasoning is supported; use the effort control per Core §2** — set it to the task rather than adding "think harder" prose; the model page does not document per-level behavior, so calibrate empirically. `(verify)` `[XM]`
- **Lean on the non-hallucination positioning, don't rely on it:** still require citations/verification steps in prompts where facts are load-bearing (Core §4) — a low hallucination *rate* is not a zero rate. `[omnitune]`
- **1M-token window:** long-context placement rules apply — durable/static content early, the ask at the end; recount token budgets rather than reusing numbers tuned for 256k-class models. `[omnitune]`
- **Image input is available** — prefer sending the actual screenshot/diagram over describing it in prose when the task is visual. `[XM]` (usage advice `[omnitune]`)
