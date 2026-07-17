---
model: claude-sonnet-5
family: sonnet
status: ga
source_status: synced-from-docs
lastSynced: 2026-07-03
lastReviewed: 2026-07-03
sources:
  - https://platform.claude.com/docs/en/about-claude/models/overview
  - https://platform.claude.com/docs/en/about-claude/models/whats-new-sonnet-5
  - https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5
  - https://platform.claude.com/docs/en/about-claude/models/migration-guide
  - https://platform.claude.com/docs/en/build-with-claude/adaptive-thinking
extends: _core.md
verify_remaining: ["GA launch date (not stated on the overview or the What's-new page; intro pricing runs through 2026-08-31)"]
---

# Rubric — Claude Sonnet 5

Read `_core.md` first; this file adds the Sonnet-5 calibration. Sourced from the live docs (synced 2026-07-03). Source legend: `[WN]` whats-new-sonnet-5 · `[PS]` prompting-claude-sonnet-5 · `[OV]` models overview · `[AT]` adaptive-thinking guide · `[MG]` migration guide.

**Controlling fact:** Sonnet 5 is the drop-in successor to Sonnet 4.6 `[WN][MG]` — "the best combination of speed and intelligence," strongest in coding and agentic tasks — and it follows instructions **more literally and more strictly** than 4.6. Prompts that leaned on the model to generalize, pad, or self-report progress need review: the tuner's job here is to make scope and bars explicit, and to *remove* scaffolding the model now handles natively. `[PS]`

## ⚠️ Reversals vs Sonnet 4.6 (the structural deltas — read first)

1. **Adaptive thinking is ON by default.** Requests without a `thinking` field run *with* adaptive thinking (on 4.6 they ran without). Turn it off only via `thinking: {type: "disabled"}` — a Sonnet-5 switch; on Fable 5 adaptive thinking is always-on and the disable switch is NOT supported `[AT]`. Budget `max_tokens` for thinking + response together. (A 4.6-era prompt tuned for thinking-off behavior may now over-think; steer triggering in the prompt rather than disabling.) `[WN][PS]`
2. **Manual extended thinking is REMOVED.** `thinking: {type: "enabled", budget_tokens: N}` returns a 400 (it was merely deprecated on 4.6). Flag any hard-coded `budget_tokens` as a breaking finding when the skill targets Sonnet 5. `[WN]`
3. **Sampling parameters are REJECTED.** Non-default `temperature`, `top_p`, or `top_k` returns a 400 — new for Sonnet-class models. Steer tone/variety via prompt instructions instead (for design variety, use a propose-options-first pattern, not temperature). `[WN][PS]`
4. **New tokenizer: ~30% more tokens for the same text.** Token counts, `max_tokens` limits, and context-capacity assumptions tuned on 4.6 are wrong here — recount, and leave headroom at `high`+ effort or risk `stop_reason: "max_tokens"` truncation after long thinking. `[WN][PS]`
5. **Interim-progress scaffolding is now counterproductive.** Sonnet 5 provides regular, higher-quality user-facing updates on long agentic traces by default — "if you've added scaffolding to force interim status messages ('After every 3 tool calls, summarize progress'), try removing it." Flag such scaffolding as a finding. `[PS]`

## Sourced platform facts `[OV][WN]`
- **Context: 1M tokens** (the default AND the maximum — no smaller variant); **max output: 128k** (up to 300k on the Batches API via the `output-300k-2026-03-24` beta header).
- **Pricing: $3 / $15 per MTok** (intro $2 / $10 through 2026-08-31); latency: Fast; reliable knowledge cutoff: Jan 2026.
- **Effort defaults to `high`** on the Claude API and Claude Code.
- **Assistant-message prefilling returns 400** (carried over from 4.6) — use structured outputs or system-prompt instructions.
- **Priority Tier is not available** on Sonnet 5.
- **First Sonnet-tier model with real-time cybersecurity safeguards:** prohibited/high-risk cyber requests may be refused as HTTP 200 with `stop_reason: "refusal"` — handle that stop reason, don't treat it as an error. `[WN]`
- **Computer use:** supports `computer_20251124`, resolutions up to 2576px / 3.75MP; 1080p balances performance and cost. `[PS]`

## Model-specific calibration (augments _core)
- **Effort ladder: `max` → `xhigh` → `high` (default) → `medium` → `low`.** Use `xhigh` for the hardest coding/agentic work; `low` only for short, scoped, latency-sensitive calls. Cross-model mapping when migrating: Sonnet 5 at `medium` ≈ Sonnet 4.6 at `high`; Sonnet 5 at `high` ≈ Sonnet 4.6 at `max` — benchmark by observed thinking length, not effort name. `[PS]`
- **Effort compliance is strict, especially at the low end** — at `low`/`medium` the model scopes work to exactly what was asked. If reasoning is shallow on complex tasks, *raise effort* rather than prompting around it. `[PS]`
- **More literal instruction following:** it "does not silently generalize an instruction from one item to another, and it does not infer requests you didn't make." State scope explicitly — Core §1.1 is HIGH severity here. `[PS]`
- **More agentic by default:** reaches for tools and runs self-verification loops more readily; `high`/`xhigh` effort substantially increases tool usage. With thinking disabled it under-reaches for tools — add an explicit nudge if tool calls matter with thinking off. `[PS]`
- **Verbosity calibrates to task complexity,** not a fixed default. Declare the length target (Core §1.8); positive examples of the desired concision beat "don't over-explain" instructions. `[PS]`
- **Code-review harnesses: recall drops are usually a harness effect.** Sonnet 5 follows "only report high-severity" bars faithfully — it finds the bugs and then withholds sub-bar findings. Make the finding stage coverage-oriented ("report every issue, include confidence + severity; a downstream step filters") or state a concrete bar ("anything causing incorrect behavior, a test failure, or a misleading result"), never a qualitative one ("important"). `[PS]`
- **Design/frontend briefs settle into a house style.** Generic "make it clean" nudges swap one fixed palette for another. Either specify a concrete visual direction, or have the model propose distinct options before building (the recommended variety mechanism now that temperature is unavailable). `[PS]`
- **Interactive coding products:** use `xhigh`/`high` effort and put task, intent, and constraints in the *first* turn — progressive disclosure across turns reduces token efficiency and sometimes performance. `[PS]`
- **Recency:** knowledge is reliable through Jan 2026 — supply anything newer in-context.

## Delegation defaults (Mode C teams)
When Sonnet 5 runs a role in a Mode C team, this is its fan-out posture (the tier layer in `references/delegation-tiers.md` sets who runs what):
- **Tier position:** workhorse — the default builder/implementer tier ("best combination of speed and intelligence," strongest Sonnet at coding and agentic tasks). Also a capable code-quality auditor. `[WN][PS]`
- **More agentic by default:** reaches for tools and runs self-verification loops readily; `high`/`xhigh` effort substantially increases tool use. As a builder it needs less delegation scaffolding than prior Sonnets — don't over-prescribe its loop. `[PS]`
- **Literal:** state each role's scope and Done-when explicitly; it "does not silently generalize an instruction from one item to another." A vague dispatch brief yields narrow output. `[PS]`
- **Effort:** `xhigh`/`high` for the hardest build/audit work; `medium`/`low` for scoped subtasks. Put task, intent, and constraints in the first dispatch turn — progressive disclosure across turns costs efficiency. `[PS]`

## Severity emphasis for Mode A on this model
Core §1.1 (explicit scope — literalism), §1.8 (declared verbosity target). Model-specific findings to flag: hard-coded `budget_tokens` or non-default sampling params (400s), forced interim-progress scaffolding, token budgets tuned to the 4.6 tokenizer, qualitative severity bars in review harnesses, and unhandled `stop_reason: "refusal"`.
