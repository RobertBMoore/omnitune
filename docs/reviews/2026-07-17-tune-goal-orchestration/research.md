# tune-goal Orchestration Review — Researcher Report

**Author:** Researcher (Opus 4.8, x-high) · one of three reviewers (auditor / researcher / consultant)
**Date:** 2026-07-17
**Scope:** Establish current (July 2026) best practice for multi-agent orchestration from primary sources, then produce a cited gap analysis against what omnitune's Mode C (`/omnitune:tune-goal`) prescribes.
**Disposition:** PROPOSE-ONLY. This report is my only write. No pipeline files were modified; nothing was committed.

**omnitune files read:** `skills/omnitune/references/orchestration-pack.md`, `.../reflection-protocol.md`, `.../rubrics/anthropic/_core.md`, `.../rubrics/anthropic/claude-fable-5.md`, `.../rubrics/anthropic/claude-opus-4-8.md`, `.../agent-md-template.md`, `.../pack-templates/*`, `tune-goal-protocol.md`, `SKILL.md`.

**Method:** Every claim below was checked against a live primary source in July 2026 (fetched, not recalled). Model guidance has changed fast in 2026; where a source is a doc I fetched in full it is cited inline, and the full URL list is in the Appendix. Secondary/search-only sources are flagged as such.

**Rev 2 (mid-run):** Folded in two operator-added questions — mixed-provider / cross-provider team tiering (§1.11, gap G11) and orchestrator oversight vs a standing "Co-Operator" (§1.12, gap G12) — plus the upstream field evidence the contract was distilled from (`miracle-academy-community-hub/audits/ORCHESTRATION-AUDIT.md` and `.../docs/ORCHESTRATION-TEMPLATE.md`; §2.4) and the consultant's report (`consult.md`), cited where I concur rather than re-argued.

---

## 1. Current best practice for multi-agent orchestration (July 2026)

### 1.1 Topology: orchestrator–worker with **heterogeneous model tiering**

The reference architecture is a **lead (orchestrator) agent that plans and delegates to specialized worker subagents running in parallel**, each in an isolated context, returning a condensed result the lead synthesizes. The single most-cited quantitative result:

> "a multi-agent system with Claude Opus 4 as the lead agent and Claude Sonnet 4 subagents outperformed single-agent Claude Opus 4 by 90.2%." — Anthropic, *How we built our multi-agent research system* [MA]

The load-bearing detail is **model tiering**: the orchestrator runs on the more capable/expensive model; workers run on a cheaper, faster tier. This is not a research curiosity — it is baked into the current product defaults:

- Claude Code subagents: *"Control costs by routing tasks to faster, cheaper models like Haiku."* The `model` frontmatter field accepts `sonnet | opus | haiku | fable | <full-id> | inherit`. [SA]
- The built-in **Explore** agent is **capped at Opus even when the main session is on a higher tier**, so exploration "never runs on a more expensive model than the one you already chose." Cheap read-only work is deliberately down-tiered. [SA]
- Agent SDK `AgentDefinition` carries a per-agent `model` field; the docs' canonical example uses *"a more capable model for high-stakes reviews"* (`opus`) and `sonnet` otherwise, chosen dynamically at query time. [SDK]
- Agent teams: teammates **do not inherit the lead's model by default**; you set a default teammate model or specify per-spawn (e.g. *"Use Sonnet for each teammate"*). [AT]

**Durable principle (provider-general):** orchestrator = frontier tier; builders/implementers = workhorse tier; read-only explorers/auditors = cheap tier. On Anthropic today that maps to Opus 4.8 / Fable 5 (lead) → Sonnet 5 (build) → Haiku 4.5 (explore/classify); omnitune's own model library already tags these roles ("Haiku… the cheap leg of a multi-model workflow"; "Sonnet 5… best combination of speed and intelligence"). The equivalent on OpenAI is a capable orchestrator with cheaper specialist tools. [MA][SA][SDK]

### 1.2 The subagent task/handoff contract (four required elements)

Because a subagent starts with **no parent history**, the delegation prompt is the entire contract. Anthropic states every subagent brief needs four things:

> objective · output format · guidance on tools/sources · clear task boundaries. "Without detailed task descriptions, agents duplicate work, leave gaps, or fail to find necessary information." [MA]

The SDK reinforces the fresh-context constraint: *"The only content you pass from parent to subagent is the Agent tool's prompt string, so include any file paths, error messages, or decisions the subagent needs directly in that prompt."* [SDK] This is the dispatch-side mirror of a report contract, and it is separate from (and as important as) the return format.

### 1.3 Context engineering: smallest high-signal token set, external state, isolation

Anthropic frames the whole discipline as finding *"the smallest possible set of high-signal tokens that maximize the likelihood of some desired outcome."* [CE] Concrete techniques, and when each wins:

- **Compaction** — summarize near the limit, preserving "architectural decisions, unresolved bugs, and implementation details while discarding redundant tool outputs." Best for conversational flow. [CE]
- **Structured note-taking / external memory** — write state to files (e.g. `NOTES.md`) outside the context window and re-read; a public-beta **memory tool** now supports this. Best for "iterative development with clear milestones." [CE]
- **Sub-agent isolation** — each subagent "explores extensively, using tens of thousands of tokens or more, but returns only a condensed, distilled summary of its work (often 1,000–2,000 tokens)," keeping detail out of the lead's window. Best for research/analysis with parallel exploration. [CE]
- **Context rot** is real: "as the number of tokens in the context window increases, the model's ability to accurately recall information from that context decreases." Long context ≠ free. [CE]

### 1.4 Parallelism, async orchestration, and the disposable-vs-long-lived question

For the newest model family (Fable 5 / Mythos 5) the defaults **reverse** relative to Opus 4.8:

> "Claude Fable 5 dispatches parallel subagents more readily than prior models. Use subagents frequently … and prefer **asynchronous communication** between orchestrator and subagents over blocking until each subagent returns. **Long-lived subagents that keep their context across subtasks** save time and cost through cache reads and avoid bottlenecking on the slowest subagent." [PF]

Two shifts matter for orchestration design:
1. **More delegation, async, not fewer/blocking.** (Opus 4.8 is the opposite: "Fewer subagents by default … steer explicitly for fan-out." [BP]) The correct default is now *model-conditioned*.
2. **Long-lived subagents are a first-class pattern.** Subagents are resumable (return an `agentId`; continue via `SendMessage`) and retain full history across turns. [SA][SDK] "Disposable" describes context isolation, not a mandate to discard the worker.

Independent-work topology is also explicit in agent teams: teammates "each own a separate piece without stepping on each other," and file-conflict avoidance is achieved by **ownership** ("Break the work so each teammate owns a different set of files"), not by global serialization. [AT]

### 1.5 Team size scales to task complexity — over-provisioning is a named failure

- Anthropic embeds explicit scaling rules in the lead's prompt: **1 agent** for simple fact-finding, **2–4** for comparisons, **10+** for complex research. [MA]
- The #1 early failure mode was **over-spawning**: "spawning 50 subagents for simple queries." [MA]
- Agent teams guidance: "Start with 3–5 teammates … Three focused teammates often outperform five scattered ones," with "5–6 tasks per teammate." [AT]

A fixed, heavy team regardless of project size is an anti-pattern in both sources.

### 1.6 Native coordination primitives now exist (subagents / agent teams / Workflow)

The platform has grown three distinct primitives; choosing among them is itself a best-practice decision [SA][AT][SDK]:

| Primitive | Coordination | Communication | Best for | Cost |
|---|---|---|---|---|
| **Subagents** | Lead manages all work | Report result to lead only | Focused tasks where only the result matters | Lower (summarized back) |
| **Agent teams** (experimental, `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`) | **Shared task list**, self-claim, **file-locked** claims, **mailbox**, idle notifications, plan-approval gate | Teammates message each other directly | Work needing discussion/challenge across independent owners | Higher (each is a full session) |
| **Workflow tool** (SDK) | Orchestration script run **outside conversation context** | n/a | "Runs that coordinate dozens to hundreds of agents" | Scales past a single conversation |

Salient details omnitune should know:
- Agent teams provide, **natively**, exactly what omnitune hand-rolls: a shared task list with **file locking to prevent race conditions**, a mailbox, per-agent idle/failure notification, and a lead↔teammate plan-approval handshake. [AT]
- **Prompt-injection defense is built in**: Claude Code "scans each subagent's final report before Claude reads it," because "text from those sources can carry instructions aimed at the main conversation" — and this "isn't a substitute for restricting what a subagent can reach." Tool allowlists are a security boundary, not just a tidiness rule. [SA]
- `isolation: worktree` gives a subagent an isolated repo copy branched from the default branch — the native answer to "one driver per branch." [SA]

### 1.7 Verification and adversarial review

- **Fresh-context verifier subagents beat self-critique** on long runs: "Separate, fresh-context verifier subagents tend to outperform self-critique." [PF]
- Anthropic evaluates with an **LLM judge against a rubric** (factual/citation accuracy, completeness, source quality, tool efficiency) **plus human testing** for edge cases, starting from ~20 representative queries. [MA]
- Agent teams make adversarial review a topology: assign each teammate a distinct lens, or have them "talk to each other to try to disprove each other's theories, like a scientific debate," which beats sequential investigation's anchoring. [AT]

### 1.8 Memory & reflection: the "Dreams" pattern (omnitune's reflection protocol is a faithful copy)

Anthropic's managed-agent **Dreams** is a real, documented feature. A dream is an **asynchronous, fresh-context job** that takes a pre-existing memory store **plus 1–100 past sessions** and produces a **new, separate** store: "duplicates merged, stale or contradicted entries replaced with the latest value, and new insights surfaced." Critically: **"The input store is never modified, so you can review the output and discard it"**; it is steered by an `instructions` field (synthesis guidance, not line edits); and the pipeline model is selectable (`claude-fable-5`, `claude-opus-4-8`, `claude-sonnet-5`, …). [DR]

omnitune's `reflection-protocol.md` (R1–R7: bounded input, steering-not-editing, read-only inputs, two artifacts, adopt-is-explicit, pushed-not-parked, promotion queue) is a **high-fidelity reimplementation of this pattern** for a file-based, provider-agnostic setting. This is a design strength and should be preserved, not "fixed." (The one enhancement: Dreams is model-selectable, so the local Dream is itself a tiering opportunity — run it on a cheaper model — and could cite the 1–100 session cap explicitly as its R1 bound.)

### 1.9 Model-family steering that packs must honor (Fable 5 hazards)

- **Reasoning-extraction refusal.** "Prompts, skills, or harness instructions that tell the model to echo, transcribe, or explain its internal reasoning as response text can trigger the `reasoning_extraction` refusal category on Claude Fable 5, causing elevated fallbacks to Claude Opus 4.8." Any "show your thinking / narrate your steps" language in an emitted pack is a live hazard for a Fable-5 team. [PF]
- **Over-prescription degrades output.** "Skills developed for prior models are often too prescriptive for Claude Fable 5 and can degrade output quality. Review and consider removing older instructions." Enumerated case-lists are a *finding*, not a virtue, for Fable 5. [PF]
- **Long-async affordances** are recommended scaffolding: a verbatim `send_to_user` tool (paired with elicitation language or it is rarely called), a "don't end on a promise" end-of-turn check, and a final-response re-grounding register. [PF]

### 1.10 Multi-provider equivalents (omnitune is anthropic/openai/xai)

The orchestrator–worker pattern generalizes. The **OpenAI Agents SDK** frames two named patterns [OAI-O]:
- **Manager / agents-as-tools** — a central orchestrator invokes specialist sub-agents as tools and keeps the user-facing conversation (analogous to Claude subagents).
- **Handoffs** — peer agents transfer control to a specialist that owns the next turn (decentralized, analogous to agent teams).

Tiering is the same lever (capable orchestrator, cheaper specialists). Codex/OpenAI agent definitions live in `AGENTS.md`-style files; the abstraction (role + tools + when-to-delegate) matches the Claude agent `.md`. The tiering and four-part-brief recommendations below are therefore provider-general and belong in the provider-shared contract, with each rubric filling in its own tier names.

### 1.11 Multi-provider / mixed-model teams (Claude + GPT + Grok)

Two structural facts govern packs whose team runs on models other than — or a mix beyond — the generating session's model:

**(a) A mixed-provider team cannot run under a native single-vendor orchestrator.** Claude Code subagents and agent teams accept only Claude models in the `model` field (`sonnet | opus | haiku | fable | <full Claude id> | inherit`) [SA]. A team whose orchestrator is Claude, builder is GPT, and auditor is Grok needs either a **model-agnostic orchestration layer** — the OpenAI Agents SDK explicitly supports non-OpenAI providers via per-agent `Agent.model`, a custom `ModelProvider`, or LiteLLM (beta), and documents mixed tiers directly: *"a smaller, faster model for triage, while using a larger, more capable model for complex tasks"* [OAI-M]; LangGraph / CrewAI / AutoGen are model-agnostic by design [industry] — or **manual multi-CLI operation** (Claude Code + Codex + a Grok CLI run as separate driver sessions). The key implication: omnitune's **provider-neutral pack (prose goal-prompt + constitution + file-based state + deterministic gate scripts) is the *right* abstraction for a mixed-provider team** — more portable than native primitives, which are single-vendor. That advantage is realized only if each role pins its own model+effort and draws steering from that model's rubric.

**(b) Cross-provider feature parity is not guaranteed.** *"You need to be aware of feature differences between model providers, or you may run into errors"* — structured outputs, multimodal input, and hosted search differ across providers [OAI-M]. A pack that spans providers must not assume a capability is portable (a structured-output gate, a vision-based UX audit, or reasoning-extraction-sensitive prose).

**Tiering is per-vendor-ladder but the same lever:** cheap explore/triage tier (Haiku 4.5 / GPT-5.x-mini / grok-code-fast) · workhorse build tier (Sonnet 5 / GPT-5.5 / grok-4.3) · frontier orchestrate/hard-audit tier (Opus 4.8 or Fable 5 / GPT-5.5 / grok-4.3). omnitune already ships all three providers' rubrics plus `resolve_model.py` routing, so the ingredients exist; what is missing is *per-role* selection (G11). Note the field evidence did **not** cost-tier — its builder and auditor skeletons run at the **same** high tier (`model: <strongest available builder model>`, auditor `<same tier as builder>`, both `effort: xhigh`) [FT] — a defensible correctness-over-cost choice for one high-stakes build, and the wrong default for a cost- or latency-sensitive team. Tiering is a deliberate per-role cost/correctness decision, which is exactly why it must be *expressible* in the agent definition and *chosen* at emit time.

### 1.12 Orchestrator oversight: supervisor vs reflection vs gates vs human checkpoints

Disambiguate two things "supervisor" conflates. A **supervisor topology** — the orchestrator plans, dispatches workers, and aggregates — is the 2026 production default (orchestrator-worker/supervisor is the bulk of deployments; "supervisor pattern with 3–5 specialists" is the standard first build) [industry]; omnitune already implements it (the orchestrator *is* the supervisor). A **standing "Co-Operator" above the orchestrator** — a resident agent watching the orchestrator — is what the originating operator asked for (session `3d08a743`) and what the design replaced with scheduled reflection (consult.md §2.11).

Current guidance does not endorse a resident meta-supervisor at small scale: multi-agent systems already cost ~15× a chat's tokens and each resident agent multiplies that [MA], and a co-operator "doubles cost and drifts alongside" what it watches (omnitune's own reflection-protocol argument — sound). The recommended shape is a **layered oversight stack**, each layer catching a different failure at a different cadence and cost:

| Oversight layer | Catches | Cadence | Cost | Earns its cost when |
|---|---|---|---|---|
| Deterministic gates (lint/test/e2e + record_check) | bookkeeping decay, broken builds, skipped evidence | every merge/tag (inline) | ~0 (scripts) | always |
| Human checkpoints (plan approval, irreversible actions) | wrong direction, scope creep, destructive/irreversible steps | at decision points | operator attention | always — esp. irreversible/scope [AT] |
| Fresh-context verifier subagent | orchestrator *judgment* errors (bad synthesis, missed regressions) | per risky milestone | 1 cheap subagent | "fresh-context verifier subagents outperform self-critique" on long runs [PF] |
| Scheduled reflection (local Dream) | cross-run judgment drift, stale lessons | milestone-close / 24h | 1 offline session | multi-day autonomous horizon [DR] |
| Standing / hierarchical supervisor | coordination overload | continuous | +1 full agent (2–3×) | only at 10+ agents where one orchestrator can't hold coordination [MA][industry] |

The evidence says the design's substitution was **directionally correct**: the field build ran with *no* co-operator and the independent audit still judged its architecture *"better than almost any long-running autonomous build this auditor has seen,"* with every one of its ten findings being RECORD (bookkeeping) decay, not judgment drift [FA]. A resident co-operator would not have caught the P0s (stale CURRENT, red-but-uncommitted battery, unfiled audits); **deterministic gates** — which omnitune mechanizes as record_check — would.

The real gap is the **middle layer**: omnitune catches bookkeeping decay (gates) and cross-run drift (reflection, coarse cadence) but has **no inline check on the orchestrator's own per-milestone judgment** — its read-only auditors review the *product*, not the orchestrator's synthesis/decisions. The "better way" the operator wants is therefore not a standing co-operator but a **per-milestone fresh-context verifier of the orchestrator's decisions** (cheap, scoped, disposable), plus surfacing the co-operator-vs-cadence fork as an explicit, tier-gated operator choice (consult.md Rec 9) — with a hierarchical supervisor reserved for true program scale (10+ agents).

---

## 2. Gap analysis

### 2.1 Summary table

Severity: **CRITICAL** (produces a materially wrong/expensive orchestration on common cases) · **HIGH** (wrong on common cases or contradicts the target model's own rubric) · **MEDIUM** (reliability/cost drift) · **LOW** (polish). Ranked by blast radius, per `_core` floor-rule convention.

| # | Best practice says | omnitune's contract/rubrics say | Severity | File(s) to change |
|---|---|---|---|---|
| G1 | Orchestrator = frontier tier; workers = cheaper tier (Opus-lead + Sonnet-workers beat solo-Opus by 90.2%); route cheap work to Haiku; per-agent `model` is standard. [MA][SA][SDK][AT] | Protocol **promises the rubric supplies** "which model orchestrates, what builders/auditors run on" (`tune-goal-protocol.md:50-54`, `SKILL.md:72`), but **no anthropic rubric contains model-tiering guidance**, and `agent-md-template.md:12-16` has **no `model:`/`effort:` slot**. Packs default the whole team to the single session model. | **CRITICAL** | rubrics (`anthropic/*`, `_core.md`); `orchestration-pack.md` (c); `agent-md-template.md`; `tune-goal-protocol.md` |
| G2 | Native subagents / agent teams / Workflow provide context isolation, a **file-locked shared task list**, mailbox, idle+failure notification, plan-approval, `isolation: worktree`, and subagent-output injection scanning. [SA][AT][SDK] | Pack **hand-rolls** the same coordination: session registry (`orchestration-pack.md:69-70`), one-driver-per-branch + stand-down handshake (B7, `:154`), external `staleness_watchdog.sh` (G4). No mapping to, or delegation to, native primitives even when the session model is Claude. | **HIGH** | `orchestration-pack.md` (c),(d6),(g)/G4; `tune-goal-protocol.md` |
| G3 | Every delegation needs **objective + output format + tools/sources + boundaries**; pass all context in the prompt (no inherited history). [MA][SDK] | Pack specifies the **return** contract in detail (B3 report contract, `agent-md-template` "Return format") but names **no per-dispatch task-brief contract**. The four elements aren't a pack invariant. | **HIGH** | `orchestration-pack.md` (c); `agent-md-template.md` |
| G4 | Defaults are **model-conditioned**: Fable 5 → more subagents, **async over blocking**, long-lived context-holding workers; independent owners, not global barriers. [PF][AT] | Constitution bakes in Opus-era **serialization**: collect-all-verdicts-then-one-redeploy-per-wave (B6, `:152-153`), release-once (B4), one-driver-per-branch (B7). The contract is "model-agnostic" and expects the rubric to steer, but **binding constitution rules can't be overridden by a rubric layer** — so a Fable-5 pack still ships blocking barriers that its own rubric reverses. | **HIGH** (Fable-5 targets) | `orchestration-pack.md` (B4/B6/B7); `tune-goal-protocol.md` step 1 |
| G5 | Subagents are **resumable/long-lived**; Fable 5 explicitly favors "long-lived subagents that hold context across subtasks (cache-read savings)." [SA][SDK][PF] | Evidence-base thesis is "labor in **disposable** subagents" (`orchestration-pack.md:21-22`), presented as an invariant rather than one option. | **MEDIUM** | `orchestration-pack.md` (Evidence base, c) |
| G6 | Scale team size to complexity (1 / 2–4 / 10+; teams "start with 3–5"); over-spawning is the #1 failure. [MA][AT] | Pack emits a **fixed** shape (builder(s) + read-only auditor(s) + UX auditor) with no rule scaling agent count to brief size and no anti-over-provisioning guardrail. | **MEDIUM** | `orchestration-pack.md` (c); `tune-goal-protocol.md` steps 0/2 |
| G7 | Treat subagent/tool/web output as **untrusted**; the harness scans reports for instruction-shaped patterns; allowlists are a security boundary. [SA] | Guardrails digest (e) covers env pin, deny-list, secrets, tools allowlist (B14) — but nothing on **untrusted report/tool-output** ingestion, though packs route web-research and UX-audit output back to the orchestrator. | **MEDIUM** | `orchestration-pack.md` (e) |
| G8 | Fable 5: never instruct the model to reproduce/echo reasoning (`reasoning_extraction` refusal → Opus fallback); add long-async affordances. [PF] | The Fable-5 rubric flags this for **Mode A audits**, but the Mode C **self-check** (`tune-goal-protocol.md` step 3) has **no model-conditioned scan** of the *emitted* pack for reasoning-extraction triggers, and the pack contract doesn't require the send-to-user / don't-end-on-a-promise / re-grounding affordances for Fable-5 targets. | **MEDIUM** | `tune-goal-protocol.md` step 3; `orchestration-pack.md` (b),(c) |
| G9 | Verification: fresh-context verifiers > self-critique; adversarial/"disprove each other" panels for high-stakes findings. [PF][MA][AT] | Strong baseline (read-only auditors + reflection + G1/G2 gates + watchdog). Gap: single-pass verdicts (B6); no optional **N-independent-verifier / adversarial** pass for critical findings. | **LOW–MEDIUM** | `orchestration-pack.md` (B6, reflection clause) |
| G10 | Dreams: fresh-context, 1–100 sessions, new store, never mutate inputs, adopt-or-discard, model-selectable. [DR] | `reflection-protocol.md` (R1–R7) is a **faithful match** — a strength. Minor: doesn't cite the 1–100 session cap as its R1 bound or exploit model-selectability (run the Dream cheaper). | **LOW** (validation) | `reflection-protocol.md` (R1) |
| G11 | Mixed-provider teams run under a model-agnostic layer (OpenAI Agents SDK: per-agent `Agent.model` / custom `ModelProvider` / LiteLLM; "smaller, faster model for triage … larger, more capable for complex tasks") or manual multi-CLI; native Claude teams are Claude-only; cross-provider feature parity isn't guaranteed. [OAI-M][SA][industry] | Pack keys **all** steering off the **generating session's** one rubric (`tune-goal-protocol.md:37-54`, `SKILL.md:72`; `resolve_model.py` selects a single rubric). No per-role `model:` field, and no intake for which model(s)/provider(s) the team will actually **run** on. Generating model ≠ running model(s); mixed-provider isn't modeled. | **HIGH** | rubrics; `agent-md-template.md`; `tune-goal-protocol.md` (Step 0/1); `SKILL.md` |
| G12 | Oversight is layered by cost/cadence (gates always; human checkpoints at irreversible/scope; **fresh-context verifier per risky milestone**; reflection at autonomous horizon; standing supervisor only at 10+ agents). A resident co-operator over one orchestrator is overhead. [PF][AT][MA][DR][industry] | Design silently swapped the operator's requested standing Co-Operator for scheduled reflection (`reflection-protocol.md:33-46`) — directionally right, but the fork was never surfaced, and there is **no inline verifier of the orchestrator's own per-milestone judgment** (auditors review the product, not the orchestrator). | **MEDIUM** | `reflection-protocol.md`; `orchestration-pack.md` (reflection clause, c); `tune-goal-protocol.md` Step 4 |

### 2.2 Root cause of "a bad orchestration of agents"

The operator's complaint traces primarily to **G1 + G4**, compounded by G2/G6:

**G1 is the smoking gun.** `tune-goal-protocol.md:50-54` states plainly: *"The rubric, never this protocol, supplies the model-shaped values: the delegation default (which model orchestrates, what builders/auditors run on)…"* and `SKILL.md:72` repeats it. But the anthropic rubrics contain only effort/subagent-count/async steering — **no assignment of models to roles**. And `agent-md-template.md` (the skeleton every pack agent inherits) exposes `name`, `description`, `tools:` but **not `model:` or `effort:`** — the exact two fields the live subagent spec [SA] and SDK `AgentDefinition` [SDK] use to express tiering. So a pack literally has no channel to encode "orchestrator on Opus, builders on Sonnet, explorers on Haiku." The emitting model then either (a) puts the entire team on the one session model (an all-Opus-4.8 or all-Fable-5 team — expensive, and the exact single-tier configuration that Anthropic's own data shows a tiered team beats by 90.2%), or (b) ladders it as an unprincipled assumption. Both read as "bad orchestration."

**G4 makes it worse on the newest model.** The pack contract is declared "provider-shared and model-agnostic," delegating model steering to the rubric — but the steering it needs to apply (Fable 5's reversals: more subagents, async, long-lived) lands as **binding constitution rules** (B4/B6/B7) that a rubric layer cannot rewrite. A Fable-5-targeted pack therefore ships Opus-era blocking barriers and "disposable subagents" that directly contradict `claude-fable-5.md`'s own documented reversals (rubric lines 26-30, 51). The pack fights the model it is built for.

**G2 explains the "reinvented, fragile" feel.** The pack's session-registry + one-driver-per-branch + external watchdog is a manual reconstruction of what agent teams now provide natively with file-locked task claims and a mailbox [AT]. Where the target is a Claude model, the pack neither maps onto these primitives nor lets the operator delegate coordination to them.

**Independent corroboration.** The consultant, walking the protocol by hand on a two-person brief, reaches G1 independently: the rubric lacks the delegation topology the protocol claims to read, so "the entire agent-team design is laddered as an assumption" and the pack still ships marked READY (consult.md §1.3, §2.6). Two dimensions the operator raised mid-run compound it: the pack keys off the *generating* session's model when teams often run on *other* — or mixed-provider — models (G11), and it silently replaced the operator's requested standing supervisor with scheduled reflection (G12).

### 2.3 What is already right (preserve during any fix)

The audit's own verdict — "state in files, judgment in the orchestrator, evidence over memory" — is **well-aligned** with current context-engineering guidance [CE], and several pieces are genuinely current best practice: findings-only reports + gate tails (B2/B3) match the "distilled 1–2k-token summary" isolation pattern [CE]; bounded reflection input (R1) matches Dreams' bounded window [DR]; the tools-allowlist discipline (B14) matches the security-boundary framing [SA]; the three-legged external check (deterministic gates + fresh-context reflection + dumb watchdog) is a sound "external checking is a cadence, not a resident" design; and `reflection-protocol.md` faithfully mirrors Dreams [DR]. Fixes should target model/topology defaults, **not** the state-file discipline or the reflection design.

### 2.4 The field evidence: what the contract fixed, and what the distillation dropped

The contract was reverse-engineered from one build — the Miracle Academy community platform (M0–M12, one orchestrator, 152 agent spawns, 1,144 commits over ~6 days) and its independent audit [FA][FT]. Reading that source directly (the operator's ask) shows both what the contract got right and where it over-reached.

**What it correctly encodes.** The audit's ten findings (P0-1..P3-9) are *all* RECORD (bookkeeping) failures — a red regression battery left uncommitted while state says "clean," a stale CURRENT pointer, a MILESTONES table disagreeing with git, an unrotated continuity buffer, audit reports that stopped after M5 [FA]. Its verdict: *"The architecture is sound. The bookkeeping that the architecture depends on has visibly decayed."* omnitune's response — mechanize RECORD as blocking gates (G1/G2 of the pack), cap+rotate the buffer (d7), require audit files at tags (C2) — fixes the right problem and should be preserved.

**What the distillation dropped or over-generalized.**
1. **Per-role model+effort.** The field template's agent skeletons carry `model:` and `effort:` (`ORCHESTRATION-TEMPLATE.md:21-41`); omnitune's `agent-md-template.md` dropped both. The contract lost tiering information *its own source contained* — the concrete root of G1/G11.
2. **Nuanced serialization.** The source already separated correctness- from throughput-serialization — *"One writer at a time per working copy … Read-only work fans out freely: auditors, reviewers, research … may overlap"* (`ORCHESTRATION-TEMPLATE.md:77-84`). The distillation hardened this toward blunt barriers (B6 collect-all-then-batch), which stalls a small team (consult.md §2.7). The source was more parallel than the contract.
3. **Scale.** The source is explicitly *one large build*; the contract applies the full apparatus to any brief that trips a low bar. The consultant treats this scale-mismatch as the single largest source of "bad orchestration" (consult.md §2.1); I concur, and the best-practice grounding is the team-size scaling both Anthropic sources give (1 / 2–4 / 10+; "start with 3–5"; over-spawning is the #1 failure) [MA][AT].

Net: the contract fixed the *recording* problem faithfully and over-generalized the *topology* (model tier, parallelism, scale) from a single high-stakes build. It has also never been output-validated — no pack has been generated, run as a real team, and audited (consult.md §2.11); the operator's complaint is the first output-side signal.

---

## 3. Prioritized recommendations

**P0 — Wire model tiering into the contract and the rubrics (fixes G1).**
1. Add a **model-tiering block to each rubric** (or to `_core.md` as a provider-general default the per-model files refine): name the role→tier mapping the protocol already promises — orchestrator = session/frontier tier; builder/implementer = workhorse tier (Sonnet 5); read-only explorer/auditor = cheap tier (Haiku 4.5). omnitune's `models.json` already carries the tier roles; make the pack consume them.
2. Add `model:` and `effort:` slots to `agent-md-template.md` frontmatter (they mirror the live `.md` subagent spec and SDK `AgentDefinition`), so every emitted agent definition *can* express its tier and effort.
3. Make `orchestration-pack.md` component (c) require a per-agent model+effort, defaulted from the rubric's tiering block, and add a self-check row (Step 3) that fails a pack whose agents are all on one tier without a stated reason.

**P0 — Make serialization and delegation defaults model-conditioned (fixes G4).**
4. Split the binding rules into **correctness-serialization** (keep always: one writer per file/branch — this is also how agent teams avoid conflicts [AT]) vs **throughput-serialization** (B6's collect-all-then-one-wave, blocking dispatch), and mark the latter as an Opus-4.8 default the rubric may relax. For Fable-5 targets, the emitted constitution should prefer async dispatch, more parallel subagents, and long-lived context-holding workers, per `claude-fable-5.md`.
5. In `tune-goal-protocol.md` step 1, make the rubric's delegation reversals actually flow into the *emitted constitution*, not just into audit scoring — i.e. the pack the model emits must reflect the target rubric's delegation stance.

**P1 — Add the four-part dispatch contract (fixes G3).**
6. Add a **task-brief contract** to `orchestration-pack.md` (c), symmetric to the report contract: every delegation states **objective, output format, tool/source guidance, boundaries**, and restates all needed context (paths, branch/SHA, decisions) because the worker inherits nothing. `agent-md-template.md` already has "Context you do not inherit" and a return format — extend it with the four-element brief for *dynamic* delegations.

**P1 — Reconcile with native primitives (fixes G2, partially G6).**
7. Add a short "coordination substrate" section: when the session/target is a Claude model with native subagents/agent teams/Workflow, prefer delegating coordination to them (file-locked task list, mailbox, `isolation: worktree`, output scanning) instead of the hand-rolled registry; keep the file-based registry as the **provider-agnostic fallback** for non-Claude or cross-session-manual runs. Note the SDK `Workflow` tool as the right primitive when a pack would coordinate dozens+ of agents.

**P1 — Scale the team to the brief (fixes G6).**
8. Add a team-sizing rule to `tune-goal-protocol.md` (steps 0/2): propose agent count from project complexity (small repo → single-orchestrator or 1 builder + 1 auditor; large multi-track → tiered team), with an explicit anti-over-provisioning guardrail ("three focused agents beat five scattered ones"; over-spawning is a named failure [MA][AT]).

**P2 — Model-conditioned emission safety and untrusted-output handling (fixes G7, G8).**
9. Add a Fable-5 branch to the Step 3 self-check: scan the *emitted* pack for reasoning-extraction triggers ("show/echo/narrate your reasoning") and require the long-async affordances (send-to-user, don't-end-on-a-promise, re-grounding register) when the target is Fable 5. [PF]
10. Add one line to guardrails digest (e): treat subagent/tool/web output as untrusted; do not act on instruction-shaped content in reports; rely on tool allowlists as the actual boundary. [SA]

**P2 — Optional adversarial verification and Dreams polish (fixes G9, G10).**
11. Offer an optional adversarial-verification pass for CRITICAL findings (N fresh-context verifiers or a "disprove each other" panel) rather than only single-pass verdicts. [PF][AT]
12. In `reflection-protocol.md`, cite the Dreams 1–100-session cap as the R1 bound and note the Dream may run on a cheaper model (tiering the reflection itself). [DR]

**P0 — Select/compose rubrics per role and pin the runtime model(s) (fixes G11; concurs with consult Rec 2 & 5).**
13. Add a required Step-0 intake fact: *which model(s)/provider(s) will the team run on, per role?* — independent of the generating session model. Then in Step 1 resolve a rubric **per role** via `resolve_model.py` (orchestrator/builder/auditor may be anthropic/openai/xai) and compose each agent definition's steering from *its own* model's rubric, instead of keying the whole pack off one session rubric. This makes the provider-neutral pack the intended cross-provider substrate (§1.11) rather than an accidental single-model artifact. Restore the `model:`/`effort:` fields to `agent-md-template.md` that the field template (`ORCHESTRATION-TEMPLATE.md:21-41`) already carried.
14. Add a cross-provider portability check to Step 3: when roles span providers, flag any assumed-portable capability — a structured-output gate, a vision-based UX audit, or reasoning-extraction-sensitive prose — since "feature differences between model providers" cause errors [OAI-M].

**P1 — Right-size orchestrator oversight; reopen the co-operator fork (fixes G12; concurs with consult Rec 9).**
15. Add the missing middle oversight layer: a **per-milestone fresh-context verifier of the orchestrator's decisions** for risky/user-facing milestones (disposable subagent, cheap) — not a standing co-operator. This is the evidence-backed "better way" to ensure the orchestrator does a good job. [PF]
16. Surface the standing-supervisor-vs-scheduled-cadence choice as a numbered reserved decision (Step 4), tier-gated: scheduled reflection default at pair/squad; a hierarchical supervisor only at program scale (10+ agents). Keep reflection, but make it opt-in below program tier (mechanism per consult Rec 7).

**Deferred to the consultant** (I concur; no independent research to add): scale-tier the whole emit (consult Rec 1), make milestone audits proportional (Rec 4), run Mode A on the pack's own governance footprint (Rec 8), and add a generate-then-audit regression fixture that scores the *emitted team* (Rec 10).

**Bottom line:** the architecture omnitune bets on (state in files, orchestrator judgment, isolated workers, external cadence checks) is sound and matches current guidance — the field audit and the consultant both say so. The "bad orchestration" is a **defaults problem, not an architecture problem**: packs can't express model tiering (G1) — a field they *dropped from their own source*, §2.4 — ship Opus-era blocking serialization onto a Fable-5 model that documents the opposite (G4), re-implement coordination the platform now provides natively (G2), key off the *generating* model when teams run on other/mixed providers (G11), and silently swapped the operator's requested supervisor for a coarse-cadence reflection with no inline judgment check (G12). P0 items 1–5 and 13–14 address the operator's complaint most directly; the oversight "better way" is item 15 (a per-milestone fresh-context verifier), not a resident co-operator.

---

## Appendix — Sources (primary unless noted)

Anthropic engineering & docs (fetched in full, July 2026):
- [MA] *How we built our multi-agent research system* — https://www.anthropic.com/engineering/multi-agent-research-system
- [CE] *Effective context engineering for AI agents* — https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- [SA] *Create custom subagents* (Claude Code docs) — https://code.claude.com/docs/en/sub-agents
- [AT] *Orchestrate teams of Claude Code sessions* (agent teams) — https://code.claude.com/docs/en/agent-teams
- [SDK] *Subagents in the SDK* (Claude Agent SDK) — https://code.claude.com/docs/en/agent-sdk/subagents (references the `Workflow` tool / *dynamic workflows*: https://code.claude.com/docs/en/workflows)
- [PF] *Prompting Claude Fable 5* — https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5
- [DR] *Dreams* (managed agents) — https://platform.claude.com/docs/en/managed-agents/dreams
- [BP] *Claude prompting best practices* / Opus 4.8 calibration — https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices (Opus 4.8 "fewer subagents by default" corroborated by omnitune `claude-opus-4-8.md` rubric, docs-synced 2026-06-04)

Related (referenced; verify on next sync):
- *Introducing Claude Fable 5 and Claude Mythos 5* — https://platform.claude.com/docs/en/about-claude/models/introducing-claude-fable-5-and-claude-mythos-5
- *Memory* (managed agents) — https://platform.claude.com/docs/en/managed-agents/memory

Multi-provider (OpenAI Agents SDK docs, fetched July 2026):
- [OAI-M] OpenAI Agents SDK — *Models* (non-OpenAI providers via per-agent `Agent.model` / `ModelProvider` / LiteLLM; mixed-tier triage-vs-complex example; feature-parity caveat) — https://openai.github.io/openai-agents-python/models/
- [OAI-O] OpenAI Agents SDK — *Orchestrating multiple agents* (LLM-vs-code orchestration; manager/agents-as-tools vs handoffs) — https://openai.github.io/openai-agents-python/multi_agent/ ; *Orchestration and handoffs* — https://developers.openai.com/api/docs/guides/agents/orchestration
- *Building agents with the Claude Agent SDK* (blog, search-sourced) — https://claude.com/blog/building-agents-with-the-claude-agent-sdk

[industry] Secondary 2026 orchestration surveys (directional; corroborate the supervisor-default and cost-tiering consensus, not load-bearing on their own): TrueFoundry, Beam.ai, DigitalApplied, and Gurusup multi-agent-orchestration write-ups (2026).

Field evidence the contract was distilled from (repo `miracle-academy-community-hub`, read 2026-07-17):
- [FA] `audits/ORCHESTRATION-AUDIT.md` — independent 2026-07-12 orchestration audit (architecture sound; RECORD decay; findings P0-1..P3-9).
- [FT] `docs/ORCHESTRATION-TEMPLATE.md` — the 15-rule template (per-role `model:`/`effort:` skeletons; nuanced serialization rule).

Teammate report cited (this directory): `consult.md` — consultant's end-user critique (scale mismatch; laddered topology; the co-operator fork).

omnitune files audited (repo, 2026-07-17): `skills/omnitune/references/orchestration-pack.md`; `.../reflection-protocol.md`; `.../rubrics/anthropic/{_core,claude-fable-5,claude-opus-4-8}.md`; `.../agent-md-template.md`; `.../pack-templates/{record_check.py,staleness_watchdog.sh}`; `skills/omnitune/tune-goal-protocol.md`; `skills/omnitune/SKILL.md`.
