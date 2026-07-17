---
model: grok-build-0.1
provider: xai
family: grok-build
status: ga
source_status: derived-tier
citation_gate: strict
extends: _core.md
lastSynced: 2026-07-03
lastReviewed: 2026-07-03
sources:
  - https://docs.x.ai/developers/models
  - https://docs.x.ai/developers/rest-api-reference/inference/models
---

# Rubric — Grok Build 0.1 (xAI coding agent)

Read `_core.md` (the xAI provider core) first; this file adds the Grok Build 0.1 calibration. Source legend: `[XM]` docs.x.ai models · `[XR]` docs.x.ai REST inference reference · `[omnitune]` omnitune-internal invariant. A `(verify)` tag marks a claim the live docs should confirm on the next sync — Grok Build is a recent public-beta id, so version-specific numbers are tagged rather than asserted.

**Controlling fact:** Grok Build 0.1 is xAI's dedicated agentic-coding model — built to plan, execute step by step, debug failures, and integrate with developer tools — and is the model xAI routes retired `grok-code-fast-1` coding traffic to. Tune it as a coding agent, not a chat model. `(verify)` `[XM]`

## Model-specific calibration (augments the xAI core)

- Prefer `grok-build-0.1` for agentic file-editing and multi-step coding work; it is the successor line to `grok-code-fast-1` for coding workloads. `(verify)` `[XM]`
- Treat the context window as ~256K tokens with higher pricing past the ~200K mark; keep durable, static content early and let long sessions compact rather than restating it. `(verify)` `[XM]`
- It runs as the engine behind the Grok Build CLI, which supports AGENTS.md, hooks, skills, and MCP out of the box — put repo standards and build/test/lint commands in AGENTS.md so they load automatically. `[XM]`
- Give it verifiable done-criteria and let it run the loop (reproduce, edit, test, re-check); a coding agent rewards a checkable "Done when" over prose description. `[omnitune]`
- For fast, well-scoped subtasks prefer a lower reasoning effort; reserve higher effort for debugging and cross-file changes. `[omnitune]`
- Confirm the exact id and any `-latest` alias against the live `/v1/models` listing before pinning it in automation. `[XR]`

## Delegation defaults (Mode C teams)

When Grok Build 0.1 runs a role in a Mode C team, this is its fan-out posture (the tier layer in `references/delegation-tiers.md` sets who runs what):
- **Tier position:** workhorse — the dedicated agentic-coding builder tier inside Grok Build CLI; route file-editing and multi-step build roles here and keep Grok 4.3 as the orchestrator/lead. `(verify)` `[XM]`
- **Give it a checkable Done-when and let it run the loop** (reproduce, edit, test, re-check); a coding-agent role rewards a verifiable completion criterion over prose. `[omnitune]`
- **Effort by subtask:** lower reasoning effort for fast, well-scoped subtasks; reserve higher effort for debugging and cross-file changes. `[omnitune]`
- **~256K window:** keep a role's durable standards in AGENTS.md and let long sessions compact rather than restating context in every dispatch. `(verify)` `[XM]`
