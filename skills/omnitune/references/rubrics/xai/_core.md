---
provider: xai
applies_to: current xAI Grok family (Grok 4.x, Grok Build)
source_status: derived-tier
citation_gate: strict
lastSynced: 2026-07-03
lastReviewed: 2026-07-03
sources:
  - https://docs.x.ai/developers/models
  - https://docs.x.ai/developers/rest-api-reference/inference/models
---

# Rubric Core — xAI (Grok family)

The provider-invariant prompt-engineering rules for xAI's Grok-class models. Each per-model rubric (`<model>.md`) reads this core first, then layers model-specific calibration. Source legend: `[XM]` docs.x.ai models · `[XR]` docs.x.ai REST inference reference · `[omnitune]` omnitune-internal invariant. A `(verify)` tag marks a claim a published page cannot state verbatim for a newly-released id; confirm against the live docs on the next sync.

**Controlling fact:** the Grok API is OpenAI- and Anthropic-SDK-compatible — migrating a prompt is a URL/key swap, not a rewrite — but the prompt *contract* still needs to be stated explicitly; a scoped Goal/Context/Constraints/Done-when prompt travels across providers unchanged. `[XM]`

## 1. Prompt contract

- State the task as Goal, Context, Constraints, and Done-when so the model stays scoped and produces reviewable work. `[omnitune]`
- Make "Done when" a checkable completion criterion (compiles, tests pass, a named artifact exists), not a vibe. `[omnitune]`
- Name the Context explicitly: the files, docs, examples, or errors that matter for this task. `[omnitune]`

## 2. Reasoning effort (the primary lever)

- Grok 4.3 and newer reasoning models expose a reasoning-effort control; set it to the task and reach for it before adding "think harder" prose. `[XM]`
- `reasoning.effort: none` disables reasoning entirely on models that support it — use it only for latency-sensitive, well-scoped calls, never for agentic or multi-step work. `(verify)` `[XM]`
- Raise effort when a result shows it is warranted rather than pre-emptively; efficient reasoning makes a lower setting sufficient more often. `[omnitune]`

## 3. Outcome-first, minimal scaffolding

- Write the smallest prompt that still pins the contract; over-specification and enumerate-every-case instructions carry across from prior models and should be trimmed. `[omnitune]`
- Give explicit output budgets (word/section/JSON-only) rather than describing format in prose. `[omnitune]`

## 4. Tools, verification & agents

- Include verification steps in the prompt — reproduce, validate, run lint/tests — because a model that can check its own work returns higher-quality output. `[omnitune]`
- Grok Build supports AGENTS.md, plugins, hooks, skills, and MCP servers; put durable team standards in AGENTS.md, not the prompt, so they load automatically. `[XM]`
- Confirm the exact model id against the live `/v1/models` listing before wiring it into automation; aliases like `grok-latest` resolve to a moving target. `[XR]`

## Audit floor-rule (model-invariant)

A dimension scoring Critical caps the overall verdict at "Critical — do not pass," regardless of other dimensions. Dimensions that do not apply are recorded N/A and excluded. The verdict is a floor rule, never an arithmetic mean. `[omnitune]`

## Fail-closed safety clause (model-invariant)

Never soften a safety-critical or fail-closed directive (destructive actions, PII, an allowlist/domain fence). When in doubt, fail closed and surface the question rather than proceeding. `[omnitune]`

## Delegation defaults (Mode C teams)

When Mode C composes a team on Grok models, this rubric supplies the fan-out posture; `references/delegation-tiers.md` supplies who runs what.
- Same orchestrator–worker lever as every provider: a capable lead with cheaper specialist workers; reserve the flagship for the orchestrator and hard reviews, and route scoped/high-volume work to a lower-effort or lighter model. `[omnitune]`
- The Grok API is OpenAI-/Anthropic-SDK-compatible, so a Grok role composes into a mixed-provider team under a model-agnostic layer (per-agent model / LiteLLM) — omnitune's provider-neutral pack is that substrate; a native single-vendor orchestrator cannot host it. `[XM]`
- Grok Build supports AGENTS.md, hooks, skills, and MCP: put a role's durable standards in AGENTS.md, and keep the four-part dispatch brief explicit because it travels across providers unchanged — Goal · Context · Constraints · Done-when map to the shared Mode C fields: Goal ↦ objective, Context ↦ tools/sources, Constraints ↦ boundaries, Done-when ↦ output format. `[XM]`
- Effort is the fan-out/depth dial: set it to the role (higher for debugging and cross-file changes, lower for scoped subtasks) rather than adding "think harder" prose. `[omnitune]`

## Note on mixed-provider parity

When a team spans providers, confirm each role's model supports the capability its dispatch assumes (structured outputs, image input, reasoning) against the live docs before pinning it in automation. `[XR]`
