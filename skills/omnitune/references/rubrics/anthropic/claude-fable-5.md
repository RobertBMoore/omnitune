---
model: claude-fable-5
family: fable
status: ga
ga_date: "2026-06-09"
source_status: synced-from-docs
lastSynced: 2026-07-13
lastReviewed: 2026-07-13
sources:
  - https://platform.claude.com/docs/en/about-claude/models/introducing-claude-fable-5-and-claude-mythos-5
  - https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5
  - https://platform.claude.com/docs/en/about-claude/models/overview
  - https://platform.claude.com/docs/en/about-claude/models/migration-guide
  - https://platform.claude.com/docs/en/managed-agents/memory
  - https://platform.claude.com/docs/en/managed-agents/dreams
extends: _core.md
---

# Rubric — Claude Fable 5

Read `_core.md` first; this file adds the Fable-5 calibration. Sourced from the live docs (synced 2026-07-13). Source legend: `[FN]` introducing-fable-5 · `[PF]` prompting-claude-fable-5 · `[OV]` models overview · `[MEM]` managed-agents/memory · `[DR]` managed-agents/dreams.

**Controlling fact:** Fable 5 is Anthropic's most capable widely-released model — built for long-horizon, ambiguous, multi-day agentic work. The big shift for *tuning*: prompts and skills written for prior models are **often too prescriptive for Fable 5 and can degrade output** — the tuner's job here leans toward *removing* over-specification, not adding it. `[PF]`

## ⚠️ Reversals vs Opus 4.8 (the structural deltas — read first)
These flip rules that hold on Opus 4.8. The per-model rubric overrides `_core` here:

1. **Subagents: MORE, not fewer.** Opus 4.8 spawns fewer subagents by default; Fable 5 "dispatches parallel subagents more readily" and is "significantly more dependable" at it, reliably sustaining parallel subagents and ongoing communication with long-running subagents and peer agents. Steer toward frequent delegation + async orchestration, not restraint. (Reverses `_core §5.4` / the Opus "fewer subagents" note.) `[PF]`
2. **Over-prescription degrades output.** "Skills developed for prior models are often too prescriptive for Claude Fable 5 and can degrade output quality. Review and consider removing older instructions." A *brief* instruction steers most behaviors; enumerating each case is counterproductive. (Reverses the Opus 4.8 "enumerate scope explicitly per item" emphasis — for Fable 5, **enumeration is a finding**.) `[PF]`
3. **Brevity over completeness in steering.** Un-steered, Fable 5 over-elaborates (surveys options, narrates, over-structures). A short brevity instruction is as effective as listing each pattern. `[PF]`

## 🚫 Fable-5-only hard rule (refusal trigger)
**Do not instruct the model to reproduce, echo, transcribe, or "show its reasoning" in the response.** Such instructions can trigger the `reasoning_extraction` refusal category and cause elevated fallbacks to Opus 4.8. When auditing/rewriting for Fable 5, **flag any "show your thinking / explain your reasoning / narrate your steps" instruction as a HIGH-severity finding.** If reasoning visibility is needed, read structured `thinking` blocks (summarized) instead. `[PF]`

## Sourced platform facts `[FN][OV]`
- **Context: 1M tokens; max output: 128k; pricing: $10 / $50 per MTok.**
- **Adaptive thinking is the only mode and is always on** — `thinking:{type:"disabled"}` is NOT supported. Control depth via **effort**, not thinking config. Raw chain-of-thought is never returned (`thinking.display`: summarized | omitted, default omitted).
- **Safety classifiers can decline requests** → `stop_reason:"refusal"` (HTTP 200). Targets offensive-cyber, bio/life-sciences, and reasoning-extraction; benign work may also trip them. Configure server/client fallback to Opus 4.8. `[FN][PF]`
- Supports effort, task budgets (beta), memory tool, code execution, programmatic tool calling, context editing, compaction, vision.

## Model-specific calibration (augments _core)
- **Effort:** `high` default; `xhigh` for the most capability-sensitive work; `medium`/`low` for routine (lower effort still strong, often beats prior models' `xhigh`). Reduce effort if a task completes but runs long. `[PF]`
- **Longer turns by default** — requests can run many minutes; autonomous runs for hours. Flag harnesses that block synchronously; prefer async checks. Add an anti-overplanning instruction ("when you have enough information to act, act"). `[PF]`
- **Overengineering at higher effort** — pronounced; needs an explicit "don't add features/refactor/abstractions beyond the task; only validate at system boundaries" instruction. `[PF]`
- **Ground progress claims** — instruct it to audit each progress claim against a tool result (nearly eliminates fabricated status). `[PF]`
- **State boundaries** — can take unrequested actions; define explicit do/don't constraints; "report findings and stop until asked." `[PF]`
- **Give the reason, not just the request** — intent/context improves results (consistent with `_core §1.4`). `[PF]`
- **Self-verification:** fresh-context verifier subagents outperform self-critique on long runs. `[PF]`
- **Final-response register** — after long agentic runs Fable 5 addresses the user in working-shorthand (arrow-chains, references to thinking the user never saw, overly technical phrasing). Steer the final message as a *re-grounding*: outcome first, complete sentences, each file/flag/identifier its own plain clause. A brief addendum suffices; flag its absence in user-facing long-run skills. `[PF]`
- **Memory system + session-close reflection** — Fable 5 does well when it writes lessons from past runs to a simple file and references them (one lesson/file, one-line summary, record *why*, update-don't-duplicate, delete-when-wrong), bootstrapped by reflecting over past sessions via subagents. Flag a long-horizon agent skill with no memory/lesson-file practice. `[PF]`
- **Delegation handoff** — beyond "more subagents": give explicit guidance on *when* delegation is appropriate, prefer async orchestrator↔subagent communication over blocking, and keep long-lived subagents that hold context across subtasks (cache-read savings; no bottleneck on the slowest). `[PF]`
- **Vision / UI self-verification** — Fable 5 reads dense technical images, web apps, and detailed screenshots with much higher accuracy (often fewer tokens) and uses bash/crop tools on flipped/blurry/noisy images. For UI work, route visual checks to a fresh-context verifier subagent rather than self-critique. `[PF]`
- **Lesson-store curation is periodic, not per-turn** — the accumulated store is cleaned by a separate synthesis pass that merges duplicates and replaces stale/contradicted entries with the latest, never modifying its inputs; the curated store is adopt-or-discard (the local-Dream pattern; see `references/reflection-protocol.md`, modeled on managed-agent Dreams). Do not steer per-turn memory rewriting. `[DR][MEM]`

## Severity emphasis for Mode A on this model
**Highest-yield findings (Fable-5-specific):** (1) any "show/echo your reasoning" instruction → HIGH (refusal trigger); (2) over-prescriptive, enumerate-every-case skills → MEDIUM/HIGH (degrades output — recommend trimming); (3) synchronous/blocking harness assumptions for long runs, incl. "spawn fewer subagents" guidance carried over from Opus; (4) a user-facing long-run skill with no final-response register addendum, or a long-horizon agent with no memory/lesson-file practice → MEDIUM; (5) UI work relying on self-critique instead of a fresh-context vision verifier → MEDIUM. Findings (4)–(5) are missing *structural affordances* (a lesson file, a brief register addendum, a verifier subagent) — orthogonal to (2)'s per-case over-enumeration, so both can apply to one skill without conflict. Note: `_core` rules still apply, but where this file reverses one, **this file wins.**
