---
model: claude-sonnet-4-6
family: sonnet
status: ga
source_status: synced-from-docs
lastSynced: 2026-07-03
lastReviewed: 2026-07-03
sources:
  - https://platform.claude.com/docs/en/about-claude/models/overview
  - https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
  - https://platform.claude.com/docs/en/about-claude/models/migration-guide
  - https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5
extends: _core.md
verify_remaining: []
---

# Rubric — Claude Sonnet 4.6

Read `_core.md` first; this file adds the Sonnet-4.6 calibration. Specs below are **sourced from the live models overview (re-synced 2026-07-03)**.

**Tier role:** the prior balanced workhorse, now on the overview's **Legacy models** tier (observed 2026-07-03) — still available at $3 / $15 per MTok, but **Claude Sonnet 5 is the drop-in successor** ("the best combination of speed and intelligence"). When tuning a skill pinned to Sonnet 4.6, note the migration caveats: Sonnet 5 rejects non-default sampling params and manual extended thinking, and its new tokenizer produces ~30% more tokens for the same text.

## Sourced platform facts (overview, 2026-06-14)
Re-synced against the live overview 2026-07-03; corrections are dated inline.
- **Context window: 1M tokens** — equal to Opus 4.8, *not* smaller. Long-context prompts that work on Opus work here.
- **Max output: 128k tokens** — equal to Opus 4.8 (corrected 2026-07-03; the live overview lists 128k, superseding the 64k previously recorded here). On the Batches API, Sonnet 4.6 supports up to 300k output via the `output-300k-2026-03-24` beta header.
- **Extended thinking: Yes** AND **Adaptive thinking: Yes** — Sonnet 4.6 supports *both* (Opus 4.8 is adaptive-only, no extended thinking). Budget-based extended thinking works here but is **deprecated** (removed in Sonnet 5) — prefer adaptive thinking for anything meant to outlive this model.
- **Latency: Fast**; **Pricing: $3 / $15 per MTok** (input/output) — ~40% of Opus cost.
- **Reliable knowledge cutoff: Aug 2025** (Opus 4.8 is Jan 2026). **Provide recent facts in-context** — Sonnet 4.6 knows less about late-2025/2026 events than Opus 4.8.

## Model-specific calibration (augments _core)
- **Instruction-following is strong;** apply Core §1 with full weight.
- **Thinking:** unlike Opus 4.8, Sonnet 4.6 supports extended (budget-based) thinking — accepted but **deprecated** on this model. A prompt that hard-codes `budget_tokens` may be valid here — do not flag it as universally rejected; flag it when the skill targets Opus 4.8, Fable 5, or **Sonnet 5** (all return a 400 for budget-based thinking). It is accepted only on Sonnet 4.6 and earlier Sonnet-class models and sits on a removal path — note it as a migration blocker for any skill expected to move to Sonnet 5.
- **Effort default: `high`** — resolved 2026-07-03: the Sonnet 5 prompting guide states effort "defaults to `high`, the same as on Claude Sonnet 4.6." Do not extend this to older Sonnets (4.5 and earlier) — confirm per model; skills that must run across Sonnet versions should still set effort explicitly.
- **Recency:** flag prompts that assume the model knows post-Aug-2025 facts without supplying them.
- **Default tuning target** for cost-sensitive, high-volume skills.

## Severity emphasis for Mode A on this model
Core §1.1/§1.2 (scope, framing) and §3.5 (suggest-vs-act). **Recency-assumption** and **Opus-only assumptions** (adaptive-only thinking — Sonnet 4.6 also supports budget-based extended thinking) are the model-specific findings to flag when a skill runs on Sonnet. (128k output and the `high` effort default are shared with Opus 4.8, not Opus-only — corrected 2026-07-03.)
