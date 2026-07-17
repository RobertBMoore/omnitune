---
provider: openai
applies_to: current OpenAI GPT-5 / Codex family
source_status: synced-from-docs
citation_gate: strict
lastSynced: 2026-07-03
lastReviewed: 2026-07-03
sources:
  - https://developers.openai.com/codex/prompting
  - https://developers.openai.com/codex/learn/best-practices
  - https://developers.openai.com/codex/models
  - https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide
  - https://developers.openai.com/codex/guides/agents-md
  - https://developers.openai.com/api/docs/guides/latest-model
---

# Rubric Core — OpenAI (GPT-5 / Codex family)

The provider-invariant prompt-engineering rules for OpenAI's GPT-5-class / Codex models. Each per-model rubric (`<model>.md`) reads this core first, then layers model-specific calibration. Source legend: `[CP]` codex/prompting · `[BP]` codex/learn/best-practices · `[MD]` codex/models · `[CG]` cookbook codex prompting guide · `[AG]` codex/guides/agents-md · `[LM]` api/docs/guides/latest-model (Using GPT-5.5) · `[omnitune]` omnitune-internal invariant.

**Controlling fact:** GPT-5.5 is a new model family — start from a minimal, scoped prompt and migrate legacy prompts rather than porting them verbatim. `[LM]`

## 1. Prompt contract

- State the task as four elements — Goal, Context, Constraints, Done-when — so the model stays scoped, makes fewer assumptions, and produces reviewable work. `[BP]`
- Make "Done when" a checkable completion criterion (compiles, tests pass, no `any`), not a vibe. `[BP]`
- Name the Context explicitly: the files, folders, docs, examples, or errors that matter for this task. `[BP]`
- Decompose complex work into smaller, focused steps — easier for the model to test and for you to review. `[CP]`

## 2. Effort & verbosity (the two separate levers)

- Set `reasoning.effort` to the task: low for fast, well-scoped work; medium/high for complex changes or debugging; xhigh for long, agentic, reasoning-heavy tasks. `[BP]`
- The effort ladder runs none → low → medium (default) → high → xhigh — there is no `minimal` level; reserve `none` for calls where low latency matters more than intelligence. Re-evaluate before escalating, since efficient reasoning makes low/medium sufficient more often. `[LM]`
- Treat `text.verbosity` as a separate lever from effort; the documented levels are low and medium (medium is the default) — prefer low, and raise back to medium only when you need more exposition. `[LM]`

## 3. Outcome-first, minimal scaffolding

- Write the smallest prompt that still pins the contract; GPT-5.5 rewards a scoped, minimal prompt. `[LM]`
- Treat GPT-5.5 as a new model family, not a drop-in for 5.2/5.4 — migrate legacy prompts rather than porting them verbatim. `[LM]`
- Lean on the model's metaprompting strength: ask it to critique and tighten your prompt or plan when a task is underspecified. `[CG]`

## 4. Structure & output

- Prefer Structured Outputs (a response schema) over describing the schema in prose, and give explicit budgets (word/section/JSON-only). `[LM]`

## 5. Tools, planning & verification

- Codex produces higher-quality output when it can verify its work: include steps to reproduce, validate a feature, and run lint/pre-commit checks. `[CP]`
- Ask the model to write/update tests, run the suite, check lint/format/types, and review its work before you accept it. `[BP]`
- For ambiguous or large work, use Plan mode (`/plan`) so the model gathers context and proposes an approach before implementing. `[BP]`
- Use Goal mode (`/goal`) for persistent multi-step objectives — the goal text is both the starting prompt and the completion criteria. `[CP]`
- Select the model deliberately with `/model`; long agentic sessions auto-compact context, so put durable, static content first. `[CP]`

## 6. AGENTS.md is the durable-rules home

- Put team standards in `AGENTS.md`, not the prompt — it loads into context automatically and covers repo layout, build/test/lint commands, and engineering conventions. `[AG]`
- Respect precedence by proximity: an `AGENTS.md` closer to the working directory overrides a broader one higher in the tree. `[AG]`

## Audit floor-rule (model-invariant)

A dimension scoring Critical caps the overall verdict at "Critical — do not pass," regardless of other dimensions. Dimensions that do not apply are recorded N/A and excluded. The verdict is a floor rule, never an arithmetic mean. `[omnitune]`

## Fail-closed safety clause (model-invariant)

Never soften a safety-critical or fail-closed directive (destructive actions, PII, an allowlist/domain fence). When in doubt, fail closed and surface the question rather than proceeding. `[omnitune]`

## Delegation defaults (Mode C teams)

When Mode C composes a team on OpenAI models, this rubric supplies the fan-out posture; `references/delegation-tiers.md` supplies who runs what.
- The orchestrator–worker pattern generalizes here as **manager / agents-as-tools** (a central orchestrator invokes specialists as tools) or **handoffs** (a peer transfers control to a specialist). Pick the manager pattern when only the result matters; handoffs when a specialist owns the next turn. `[omnitune]`
- Tiering is the same lever: a capable orchestrator with cheaper specialist workers; route subagent / high-volume / latency-sensitive steps to a smaller model and reserve the flagship for the lead and hard reviews. `[BP]`
- Codex agent definitions live in `AGENTS.md`-style files; the abstraction (role + tools + when-to-delegate + model) matches a Claude agent `.md`, so the four-part dispatch brief travels unchanged — Codex's Goal · Context · Constraints · Done-when map to the shared Mode C fields: Goal ↦ objective, Context ↦ tools/sources, Constraints ↦ boundaries, Done-when ↦ output format. `[AG]`
- Mixed-provider teams (OpenAI + Claude + Grok) run under a model-agnostic layer — per-agent model / a custom provider / LiteLLM — not a native single-vendor orchestrator; omnitune's provider-neutral pack is that substrate. `[omnitune]`
- Cross-provider feature parity is not guaranteed (structured outputs, multimodal input, hosted search differ): do not assume a capability is portable across a mixed team's roles. `[LM]`
