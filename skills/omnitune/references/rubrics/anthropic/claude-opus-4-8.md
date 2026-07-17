---
model: claude-opus-4-8
family: opus
status: ga
source_status: synced-from-docs
lastSynced: 2026-06-04
lastReviewed: 2026-06-14
sources:
  - https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
  - https://platform.claude.com/docs/en/about-claude/models/whats-new-claude-4-8
  - https://platform.claude.com/docs/en/about-claude/models/migration-guide
  - https://www.anthropic.com/news/claude-opus-4-8
  - https://platform.claude.com/docs/en/build-with-claude/effort
  - https://platform.claude.com/docs/en/build-with-claude/adaptive-thinking
  - https://platform.claude.com/docs/en/about-claude/models/overview
extends: _core.md
---

# Rubric — Claude Opus 4.8

Read `_core.md` first; this file adds the Opus-4.8-specific calibration. Source legend: `[BP]` best practices · `[WN]` what's new in 4.8 · `[MG]` migration guide · `[News]` anthropic.com/news/claude-opus-4-8 · `[EF]` effort guide · `[OV]` models overview.

**Controlling fact:** Opus 4.8 performs well on existing 4.7 prompts but is **more literal**, **calibrates length to judged complexity**, **favors reasoning over tool calls** (with better tool-trigger reliability than 4.7), and **respects effort strictly** — effort matters more than on any prior Opus. Most audit findings trace to one of these. `[BP]`

## What changed 4.7 → 4.8
1. **Effort default is `high`** on every surface (API + Claude Code). Set `xhigh` explicitly for coding/high-autonomy work. `[WN][MG]`
2. **Effort levels recalibrated:** `medium` allows somewhat more thinking, `high` somewhat less, `xhigh` substantially more. Re-baseline any level tuned against 4.7. `[MG]`
3. **More literal instruction following, especially at lower effort** — does not generalize an instruction across items and does not infer unrequested work. State scope explicitly. `[BP]`
4. **Better tool triggering** — less likely to skip a required tool call than 4.7, while still favoring reasoning. Raise effort to increase tool use. `[WN][BP]`
5. **Fewer subagents by default** than 4.7 — steer explicitly for fan-out. `[BP]`
6. **Higher-quality progress updates** — remove forced interim-summary scaffolding. `[BP]`
7. **Better bug-finding + more self-correcting** — "around four times less likely than its predecessor to allow flaws in code it has written to pass unremarked." `[News]`
8. **Platform:** model id `claude-opus-4-8`; 1M-token context default (200k on Microsoft Foundry); mid-conversation `role:"system"` accepted; 1,024-token prompt-cache minimum; fast mode (`speed:"fast"`, ~2.5x output tok/s, premium, research preview). `[WN][MG]`

## Model-specific calibration (overrides/augments _core)

- **Literalness is high, especially at low effort.** Core §1 (scope, positive framing, no hedges) is **HIGH severity** on this model — ambiguity yields narrow compliant output, not helpful inference. `[BP]`
- **Effort is the primary quality lever.** `xhigh` for coding/agentic; minimum `high` for intelligence-sensitive work; `medium` for cost-sensitive; `low` only for scoped latency-sensitive work. `max` can overthink — test first. At `max`/`xhigh`, start max output tokens at 64k `[EF]` (a starting headroom, not the ceiling — the hard max is 128k `[OV]`). If reasoning feels shallow, raise effort rather than prompting "think carefully." `[BP]`
- **Adaptive thinking** (`thinking:{type:"adaptive"}`, off unless set); manual `budget_tokens` is **rejected (400)** — migrate to adaptive thinking + effort. `[WN][MG]`
- **Tool-triggering is reliable;** raise effort (not aggressive prose) to increase tool use. `[BP]`
- **Subagents: fewer by default** — steer explicitly when you want parallel fan-out; rein in single-file delegation. `[BP]`
- **Request "above and beyond" explicitly** — 4.8 scopes to the ask at `low`/`medium`. `[BP]`
- **Self-correction is strong** (~4x less likely to pass its own flaws) — lighter self-review scaffolding is needed than on prior models; don't over-stack "double-check everything." `[News]`
- **Frontend house style** defaults to cream/off-white (~`#F4F1EA`), serif display, terracotta/amber — wrong for dashboards/fintech/healthcare and persistent. Specify a concrete palette/type system or instruct "propose 4 distinct directions before building." `[BP]`
- **Prefilled assistant responses rejected (400) since 4.6** — use Structured Outputs, system-prompt instructions, XML output tags, or tool calling. `[BP]`

## Delegation defaults (Mode C teams)
When Opus 4.8 runs a role in a Mode C team, this is its fan-out posture (the tier layer in `references/delegation-tiers.md` sets who runs what):
- **Tier position:** frontier — orchestrate and hard-audit. Opus 4.8's literalness and strong self-correction (~4x fewer of its own flaws pass) make it the right lead for high-stakes control and correctness review. `[BP][News]`
- **Fan-out: fewer by default.** Opus 4.8 "spawns fewer subagents by default — steer explicitly when you want parallel fan-out; rein in single-file delegation." Do not stack async-peer scaffolding it does not want; when you need parallelism, ask for it by name. `[BP]`
- **Dispatch: blocking-then-integrate is fine.** Collect-verdicts-then-fix-wave (throughput serialization) is an acceptable Opus-era default here; it is not a hard invariant — a pack targeting a more-async model may relax it. The correctness invariant (one writer per file/branch) always holds.
- **Workers: disposable is fine.** Opus 4.8 does not need long-lived context-holding subagents to perform; the disposable-worker default is well-matched. Raise builder/auditor effort to `xhigh` for coding and high-autonomy roles.

## Severity emphasis for Mode A on this model
Core §1.1/§1.2/§1.3 (scope, framing, aggression) and §3.5 (suggest-vs-act) are the highest-yield findings; effort-default/level drift (§4) is the most common MEDIUM. `[BP]`
