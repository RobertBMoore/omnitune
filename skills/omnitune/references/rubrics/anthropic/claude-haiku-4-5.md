---
model: claude-haiku-4-5
model_id_full: claude-haiku-4-5-20251001
family: haiku
status: ga
source_status: derived-tier
lastSynced: 2026-06-14
lastReviewed: 2026-06-14
sources:
  - https://platform.claude.com/docs/en/about-claude/models/overview
  - https://platform.claude.com/docs/en/about-claude/models/whats-new-claude-4-5
  - https://www.anthropic.com/news/claude-haiku-4-5
  - https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
extends: _core.md
verify_remaining: ["effort default level (Haiku is adaptive-thinking: No; confirm effort behavior via the effort docs)"]
---

# Rubric — Claude Haiku 4.5

Read `_core.md` first; this file adds the Haiku-4.5 calibration. Specs below are **sourced from the live models overview (synced 2026-06-14)**.

**Tier role:** "the fastest model with near-frontier intelligence" — high-volume, latency-sensitive, well-scoped tasks (classification, extraction, routing, short generation, the cheap leg of a multi-model workflow). Drop-in replacement for Haiku 3.5 and Sonnet 4 at the lowest price point.

## Sourced platform facts (overview, 2026-06-14)
- **Context window: 200k tokens** — materially smaller than Opus/Sonnet's 1M. Do **not** design 1M-token long-context prompts for Haiku.
- **Max output: 64k tokens.**
- **Extended thinking: Yes** (the first Haiku to support it) — but **Adaptive thinking: No.** Haiku uses classic budget-based extended thinking, not Opus 4.8's adaptive thinking.
- **Latency: Fastest**; **Pricing: $1 / $5 per MTok** — the most economical current model.
- **Reliable knowledge cutoff: Feb 2025** (the earliest of the current models). **Supply recent facts in-context** aggressively.

## Model-specific calibration (augments _core)
- **Be more explicit and structured than with Opus/Sonnet.** Core §2 (structure) is **HIGH severity**: numbered steps, declared output shape, concrete few-shot examples.
- **Examples carry more weight** than abstract instructions — flag example-free prompts that rely on pattern inference.
- **Reasoning:** Core §4 "prefer effort over prescriptive CoT" is **reversed** here — be more prescriptive; make the steps explicit rather than expecting the model to derive them. Extended thinking is available, but don't rely on deep autonomous multi-step inference.
- **Context: 200k, not 1M.** Flag any long-context prompt that assumes an Opus/Sonnet window. Apply Core §2 (long-data-at-top + `<quotes>`) aggressively when inputs are large.
- **Recency: Feb 2025 cutoff** — the strongest recency-assumption risk of the current models; supply recent facts.

## Severity emphasis for Mode A on this model
Structure (Core §2) and example sufficiency are highest-yield; an under-specified, example-free prompt that passes on Opus can fail on Haiku. Flag Opus/Sonnet-window assumptions (1M context) and post-Feb-2025 recency assumptions.
