---
model: claude-sonnet-4-6
family: sonnet
status: ga
source_status: synced-from-docs
lastSynced: 2026-06-14
lastReviewed: 2026-06-14
sources:
  - https://platform.claude.com/docs/en/about-claude/models/overview
  - https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
  - https://platform.claude.com/docs/en/about-claude/models/migration-guide
extends: _core.md
verify_remaining: ["effort default level (not stated on the overview; confirm via the effort docs)"]
---

# Rubric — Claude Sonnet 4.6

Read `_core.md` first; this file adds the Sonnet-4.6 calibration. Specs below are **sourced from the live models overview (synced 2026-06-14)**; one prompt-engineering item (effort default) is still flagged `(verify)`.

**Tier role:** "the best combination of speed and intelligence" — the balanced workhorse for the bulk of production work, at lower cost/latency than Opus.

## Sourced platform facts (overview, 2026-06-14)
- **Context window: 1M tokens** — equal to Opus 4.8, *not* smaller. Long-context prompts that work on Opus work here.
- **Max output: 64k tokens** (Opus 4.8 is 128k) — cap large-generation prompts accordingly; on the Batches API, Sonnet 4.6 supports up to 300k output via the `output-300k-2026-03-24` beta header.
- **Extended thinking: Yes** AND **Adaptive thinking: Yes** — Sonnet 4.6 supports *both* (Opus 4.8 is adaptive-only, no extended thinking). You may use classic budget-based extended thinking here.
- **Latency: Fast**; **Pricing: $3 / $15 per MTok** (input/output) — ~40% of Opus cost.
- **Reliable knowledge cutoff: Aug 2025** (Opus 4.8 is Jan 2026). **Provide recent facts in-context** — Sonnet 4.6 knows less about late-2025/2026 events than Opus 4.8.

## Model-specific calibration (augments _core)
- **Instruction-following is strong;** apply Core §1 with full weight.
- **Thinking:** unlike Opus 4.8, Sonnet 4.6 supports extended (budget-based) thinking. A prompt that hard-codes `budget_tokens` (rejected on Opus 4.8) may be valid here — do not flag it as universally rejected; flag it only when the skill targets Opus.
- **Effort default: (verify)** — not stated on the overview. Until confirmed, do not assume Opus 4.8's `high` default; set effort explicitly in skills that run on Sonnet.
- **Recency:** flag prompts that assume the model knows post-Aug-2025 facts without supplying them.
- **Default tuning target** for cost-sensitive, high-volume skills.

## Severity emphasis for Mode A on this model
Core §1.1/§1.2 (scope, framing) and §3.5 (suggest-vs-act). **Recency-assumption** and **Opus-only assumptions** (128k output, adaptive-only thinking, `high` effort default) are the model-specific findings to flag when a skill runs on Sonnet.
