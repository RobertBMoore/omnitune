# Audit — `/omnitune:tune-goal` orchestration-pack generation

**Auditor:** auditor agent (3-agent review panel: auditor / researcher / consultant)
**Date:** 2026-07-17 · **Branch:** `hotfix/duplicate-hooks-load` (clean) · **Effort:** Opus 4.8 x-high
**Complaint under audit:** newly generated Mode C packs specify a *bad orchestration of agents* — the agent-team designs the packs emit are poor.
**Verdict:** Confirmed and root-caused. The pipeline was reverse-engineered from a field audit that only ever examined **recording discipline**, and the "model-agnostic" refactor from template → contract **deleted the concrete team-design defaults** the template carried, redirecting them to rubrics that never received them. The result has **no contract, no grounding source, and no gate for agent-team design** — it neither steers toward good topology nor detects bad topology, and it cannot express the multi-provider, multi-model runtime teams the operator actually runs. **Propose-only — no pipeline files were modified. This report is the sole write.**

---

## 1. Scope, method, evidence base

**Pipeline files read end-to-end:** `commands/tune-goal.md`; `skills/omnitune/SKILL.md`; `skills/omnitune/tune-goal-protocol.md`; `references/orchestration-pack.md`; `references/reflection-protocol.md`; `references/pack-templates/{record_check.py,staleness_watchdog.sh}`; `references/rubrics/anthropic/{_core.md,claude-fable-5.md,claude-opus-4-8.md,claude-sonnet-5.md,claude-sonnet-4-6.md,claude-haiku-4-5.md}` + `references/rubrics/{openai,xai}/*`; `references/models.json`; `scripts/resolve_model.py`; `scripts/test_orchestration_reference.py`; `references/agent-md-template.md`; `references/common-anti-patterns.md`; the three `omnitune.config` files; `tuner/regression/goal-pack-brief.md`.

**Ground-truth field evidence read (the source the contract was distilled from):** `miracle-academy-community-hub/audits/ORCHESTRATION-AUDIT.md` (the original 2026-07-12 field audit) and `docs/ORCHESTRATION-TEMPLATE.md` (the template predecessor of `orchestration-pack.md`). Field orchestrator session `9455aeb3` resolved to a sub-session ("M12 round-2 visual re-QA", no prompts) — not useful; the field audit document is the authoritative upstream evidence and it is excellent.

**Sessions inspected:** `c4c4537d` (this task's parent), `3d08a743` / `f6c6ad3d` (the two July-13/14 sessions that **built** the pipeline on `claude-code:fable-1m` — the second hit its session limit mid-run). Neither consumed a pack.

**Was a concrete bad pack found?** No — confirmed. The July sessions built the *generator* (commit `61d56d6`); no `PROGRESS.md`/constitution/goal-prompt artifact exists in the tree, there is no `reports/` dir, and `omnitune.config.yaml` omits `output.packs` so every pack emits chat-only (F7). I therefore ground the audit two ways: (a) the **distillation-fidelity analysis** in F0, comparing the field audit and template against the shipped contract; and (b) a **dry-run trace** of the protocol on the in-repo fixture `tuner/regression/goal-pack-brief.md` (§3).

**Relationship to `consult.md`:** the consultant reached the same three headline conclusions (rubrics lack the topology the protocol claims; no scale tiering; self-check validates mechanics only) from the *user's seat* using a simulated brief. **I verify those independently below and cite `consult.md` rather than re-argue where we agree.** My differentiated contribution is the upstream provenance: the consultant explicitly *could not* read the Miracle Academy evidence (`consult.md:194`) and worked from the distilled rows; I read the raw field audit and template, which is what makes F0 provable.

**One structural fact that colours everything:** the contract's own evidence base is a single **program-scale** build — "M0 to M8, one orchestrator, **152 agent spawns over four days**" (`ORCHESTRATION-TEMPLATE.md:3`), "1,144 commits Jul 6-12 … one effectively-continuous session" (`ORCHESTRATION-AUDIT.md:3`). Everything the contract mandates is calibrated to that one scale (see F0, F6).

---

## 2. Findings

Severity: **P0** blocks good output at the source · **P1** lets bad output ship undetected · **P2** degrades quality · **P3** polish.

---

### F0 — The distillation deleted the team-design content. **[P0 · root of F1 & F2]**

This is the finding the ground-truth evidence unlocks. Trace the chain **field audit → template → contract** and the team-design defaults are progressively stripped until nothing is left.

**Step 1 — the field audit never evaluated team *design*.** Its scope was explicitly narrow and its subject was a team a human had *already built well*:
> "Scope: the orchestration approach (constitution, state files, memory, delegation, loop fidelity, evidence discipline, context survival), **NOT the product code.**" — `ORCHESTRATION-AUDIT.md:3`
> "**The architecture is sound.** The bookkeeping that the architecture depends on has visibly decayed… Grade: B- overall (**architecture A-, recording discipline … C-**)." — `ORCHESTRATION-AUDIT.md:7`

Every one of its P0/P1/P2 findings is a *recording* failure (red battery, stale CURRENT, dead MILESTONES table, silent LOG, unfiled audits, uncommitted evidence, unrotated buffer). Its "What is working" section certifies the *team design itself was already good* — "The delegation surface matches the policy… builder.md and frontend-builder.md carry tools allowlists, the binding report contract… Auditors are read-only" (`ORCHESTRATION-AUDIT.md:61-68`). **So the P0-1..P3-9 taxonomy the contract is built on is 100% recording lessons — because recording is all the audit looked at, on a team whose design was a given.** The contract inherited an evidence base that had, by construction, *nothing to say about how to design a team from a brief* — which is exactly what Mode C is asked to do.

**Step 2 — the template still carried concrete topology defaults. The contract abstracted them to nothing.** The template predecessor had real, usable team-design content that `orchestration-pack.md` **removed**:

| Team-design element | `ORCHESTRATION-TEMPLATE.md` (predecessor) | `orchestration-pack.md` (shipped contract) |
|---|---|---|
| **Role taxonomy** | Named: "Orchestrator… Builders… Auditors (security, code quality, ux, domain parity)" — `:9-15` | Collapsed to "builder(s) and read-only auditor(s)" — `:52` |
| **Builder model/effort** | `model: <strongest available builder model>` · `effort: xhigh` — `:26-27` | Deleted: "Model, effort, and verbosity defaults come from the session model's rubric… **never hardcoded here**" — `:57-58` (and the rubric doesn't have them — F2) |
| **Auditor model/effort** | `model: <same tier as builder>` · `effort: xhigh` — `:38-39` | Deleted (same redirect) |
| **Serialization / parallelism** | A full section: "One writer at a time per working copy. Parallel writers require isolated worktrees… Read-only work fans out freely: auditors, reviewers, research… may overlap" — `:77-84` | One line: B7 "One driver per branch/worktree" — `:153` |
| **Operator MCP-disable default** | Specific evidence-based list ("chrome-devtools, playwright, posthog, slack… did zero useful work… keep context7") — `:126-133` | Abstracted to "the host MCP/plugin disable list" — component (f), `:82` |

The refactor's stated goal was decoupling — "no client, company, campaign, or product names… project-agnostic" (`orchestration-pack.md:227-232`). But in genericizing, it did not *parameterize* the topology defaults, it **erased** them: the template's working default `model: <strongest available builder model>, effort: xhigh` became "comes from the rubric," and the rubric is silent (F2). **Decoupling deleted the answer instead of moving it.**

**Step 3 — the scale was frozen, not adapted.** The template titled itself "**starting rules** for the next app build" and said "copy this file… **adapt** names and gate commands" (`ORCHESTRATION-TEMPLATE.md:1,5-7`) — i.e. an adaptable starting point derived from one 152-spawn program. The contract reframed those starting rules as *the invariant every pack must satisfy*, with no scale dial (F6; `consult.md:§2.1`).

**Root-cause hypothesis:** The pipeline was built to productize the *recording* lessons of one expertly-hand-designed program build. In making the recording machinery model-agnostic and mechanized, the refactor discarded the template's concrete (single-model, single-scale) topology defaults without replacing them — leaving Mode C to generate the one thing the evidence chain never covered and the contract no longer specifies.

**Fix proposal:** Treat F0 as the reason F1/F2 exist. Restore the deleted content in parameterized form: a topology contract (F1) that re-instates the role taxonomy and serialization rules the template had, and a delegation-tier layer (F2) that re-instates `strongest-builder / same-tier-auditor / xhigh` as real defaults keyed by role and model — not a redirect to an empty rubric field.

---

### F1 — The pack contract constrains recording mechanics, not agent-team design. **[P0]**

F0 explains *why*; this is the *state* it produced. Of the seven components (a–g), four gates (G1–G4), fourteen binding rules (B1–B14), and 25 traceability rows in `orchestration-pack.md`, **~90% govern state files, commits, gate tails, line caps, context economy, and death-detection.** The meta-rules that bind the whole contract are both about recording — "Gates, not prose" / "Brief binding rules, not case lists" (`:26-32`). The only team surface, component (c), is thin — "builder(s) and read-only auditor(s)… Model, effort, and verbosity… from the rubric… never hardcoded" (`:52-58`) — and the constitution reduces the whole delegation strategy to "**the delegation policy in two lines**" (`:50`).

Nothing in the contract addresses the levers that determine team quality: **topology** (how many builders; parallel vs serial; when a workstream gets its own agent), **role specialization** (the brief's domains → a derived role set; note B2/B13 presuppose "the UX auditor" that component (c) never defines — `:145,172`), **model/effort tiering** (punted to the empty rubric — F2), **context budgets per agent** (absent), and **handoff protocol** (only the one-way report contract). `consult.md:§1.4` reaches the same crux from the user seat: *"a pack whose agent team is an unsteered guess passes every check the pipeline runs, and ships marked READY."*

**Fix proposal:** Add a **Topology contract** to `orchestration-pack.md` — the missing counterpart to the recording contract — as brief binding rules the pack instantiates: a role-derivation rule (roles from the brief's milestones/domains, not a fixed pair); a decomposition rule (parallel only for independent-context workstreams — re-instate the template's serialization section, `TEMPLATE:77-84`); a tiering rule (F2); a per-agent context-budget rule; and a first-class agent-team template (F8). Expand "delegation policy in two lines" into a real section.

---

### F2 — Team model/effort/verbosity tiering is delegated to a source that structurally cannot supply it — and cannot express multi-provider runtime teams at all. **[P0]**

**The promise** (`tune-goal-protocol.md:51-53`): *"The rubric… supplies the model-shaped values: the delegation default (**which model orchestrates, what builders/auditors run on**), effort and verbosity defaults… Where the rubric is silent, ladder the choice as an assumption"* (`:54`).

**The rubrics cannot deliver it.** A grep across the entire rubric library returns only *single-model, in-place* subagent-count guidance, never a team tiering spec: Opus 4.8 "Subagents: fewer by default…" (`claude-opus-4-8.md:41`); Fable 5 "Subagents: MORE, not fewer… frequent delegation + async" (`claude-fable-5.md:28`), "Delegation handoff… keep long-lived subagents" (`:51`). None names *which model a builder or auditor runs on*. By construction a per-model rubric describes how to prompt *that one model* — it is the wrong shape to answer a cross-model tiering question. So the promised value is **always** "rubric silent → laddered guess," verified independently by the consultant (`consult.md:§1.3`, Rec 2). This is the finding all three reviewers converge on.

**The information exists, unread.** The delegation-target knowledge is sitting in `models.json` and sibling rubrics that Mode C never loads: Haiku "the cheap leg of a multi-model workflow" (`claude-haiku-4-5.md:22`); `models.json:191` gpt-5.4-mini "OpenAI suggests it for subagents"; the template's own default "`<strongest available builder model>`" (deleted per F0). `tune-goal-protocol.md:37-48` loads only `orchestration-pack.md`, `reflection-protocol.md`, and **the session model's** rubric + `_core.md`; a grep confirms no Mode C file references `models.json`, a sibling rubric, or any delegation inventory.

**The multi-provider dimension (operator answer #2).** The operator confirms teams are *generated on one model but run on different models, often multi-provider (ChatGPT, Grok, …)*. The pipeline **cannot express this at all**: rubric selection keys solely off the generating session's model (`SKILL.md:34`, `resolve_model.py` resolves *one* id → *one* rubric). There is no concept of "resolve a team of models," no place for a per-role model that differs from the session model, and no loading of the openai/xai rubrics that *do exist* for the models the builders will actually run on. So an Opus-generated pack ships Opus's "fewer subagents" posture to a team that may run builders on Fable ("more subagents") and Grok — silently mis-tuned (`consult.md:§2.6`, Rec 5). The raw material for cross-provider per-role tiering is already in the repo (anthropic/openai/xai rubrics + `models.json`); it is unwired, not missing.

**Root-cause hypothesis:** A category error compounded by F0 — a *team-composition, cross-model* decision was assigned to a *single-model prompt-engineering* document, after the template's concrete defaults were deleted, with no plumbing to load more than one model's rubric.

**Fix proposal:**
1. Add a **delegation-tier layer** (new `references/delegation-tiers.md` or a `delegation:` block in `models.json`) mapping role → recommended model + effort per provider, seeded from the tier notes already present (Haiku cheap-leg, mini-for-subagents, `strongest-builder/xhigh`).
2. Add a required intake fact: **which model(s) the team will run on** (operator answer #2) — accept a multi-provider set; select each role's defaults from *that* model's rubric, loading the openai/xai/anthropic rubrics as needed.
3. Reframe the session rubric's role from "supplies the delegation default" to "supplies the *fan-out posture*"; the tier layer supplies *who runs what*. Fix the false promise at `tune-goal-protocol.md:51-53`.
4. Gate every agent definition on carrying an explicit, justified `model` + `effort` (F3).

---

### F3 — The self-check cannot detect a badly-orchestrated pack. **[P1]** *(concurs with `consult.md:§1.4`, Rec 3)*

Independently verified: Step 3 (`tune-goal-protocol.md:78-92`) validates the traceability walk (all **recording** rows P0-1..P3-9/T1..T15), `py_compile`/`bash -n` on the scripts, a clean fabrication ledger (a mis-tiered team passes because the mistier is *laddered*), and existence/line-caps ("all seven components exist; constitution < ~90 lines"). `test_orchestration_reference.py` asserts only 25 traceability rows + template compilation + reflection rows R1–R7. **Zero assertions about topology, tiering, role fit, or context budgets.** A pack with a mono-model, mis-tiered, wrong-count, or contradictory-fan-out team returns a clean self-check and a **READY** verdict. The one quality dimension the operator complains about is the one dimension nothing validates.

**Fix proposal:** Add a **topology self-check** (Step 3.5) + test: every agent carries `tools:` **and** explicit justified `model:`+`effort:`; roles map to brief workstreams/domains (no unmapped role, no unowned domain); no general-purpose spawn for build/audit (mechanize B14); fan-out matches the session rubric's posture (F5); emit a **CONDITIONAL** verdict naming topology failures exactly as it already does for recording failures (`:94-95`).

---

### F4 — The intake gate collects recording inputs and omits every input good topology needs, including scale. **[P1]**

The gate's six required facts (`tune-goal-protocol.md:18-26`) — deploy target, gate commands, checkpoint owners, quiet hours, milestone shape, target dir — **all feed recording/gates/scheduling.** It never asks: workstream **independence** (parallel-vs-serial input); required **specializations** (→ role set); **which models the team will run on** (F2, operator #2); **scale** — team size / agent concurrency / horizon (the tier selector, operator #1); or **audit rigor**. Garbage-in for topology: even a perfect emitter cannot tier a team it was never told can run Haiku, split workstreams it was never told are independent, or right-size apparatus for a scale it never asked about.

**Fix proposal:** Add a **Team-design intake block** to Step 0 with numbered questions for scale (drives the tier — see the recommendation in §4), workstream independence, specializations, runtime model set, and audit rigor; ladder each when unanswered (`consult.md` Rec 1).

---

### F10 — The co-operator the operator asked for was silently swapped for decay-detection cadences that cannot see a never-good team. **[P1]** *(operator answer #3)*

**The trace.** In session `3d08a743` turn 1 the operator asked, verbatim, for *"an AI 'Co-Operator' Agent that runs above the Orchestrator Agent to make sure the Orchestrator Agent is doing the best job possible."* The pipeline's answer, written into `reflection-protocol.md:33-46`, **explicitly rejects it**: *"the answer is not a standing co-operator agent that doubles cost and drifts alongside it. External checking is three scheduled legs… **no resident agent is added**"* (echoed at `orchestration-pack.md:186-188`). The fork was decided unilaterally and never surfaced to the operator as a choice (`consult.md:§2.11`, Rec 9).

**Why the substitution is implicated in the complaint.** The operator asked for a supervisor of *orchestration quality* ("doing the best job possible"). What the design substituted checks something different: the three legs catch **bookkeeping decay** (gates), **judgment drift** (reflection), and **orchestrator death** (watchdog) — `reflection-protocol.md:38-45`. Every one is a **change-from-prior-state** detector. The reflection audit is literally an "**orchestration-*drift* audit**" (`orchestration-pack.md:184`, `reflection-protocol.md:R4`) — it measures deviation over time, **not correctness at t0.** A pack that is *born* with a bad team has no drift from bad→bad, so the only "supervisor" in the system is blind to it **forever**. The operator's instinct was correct — they wanted a check on whether the orchestration is *good*; the design gave them checks on whether the recording is *decaying*. The substitution is the whole pipeline's defect in miniature: **asked about orchestration quality, answered with recording machinery.**

Note the substitution also *added* cost the small-build operator feels — three overlapping external-check legs plus two milestone auditors multiply triage load with no quality payoff below program scale (`consult.md:§2.4, §2.9`).

**Was the co-operator itself "what broke the setup"?** Assessed skeptically: not by commission. The reflection design is coherent *for its stated job* (decay detection on a long autonomous run). It broke the operator's use case by **omission** — it foreclosed the quality-supervisor their instinct reached for and replaced it with drift detection that cannot catch an initially-bad team. So the operator's suspicion is directionally right: the co-operator *decision* (to decline it) is upstream of the complaint.

**Fix proposal:** Reopen the fork as a **reserved decision** (`consult.md` Rec 9): offer (a) the scheduled-cadence answer (keep, for autonomous/program runs) *and* (b) a **design-quality gate** — not a standing resident, but a one-shot **orchestration-fitness review at pack-emit time and at milestone-0** that scores the team's initial design (the thing drift audits structurally cannot). That gives the operator the "is the orchestrator doing a good job" supervision they asked for, at t0 where it matters, without a doubled-cost resident. Wire it to F3's topology self-check.

---

### F5 — Fable 5's "more subagents / async" reverses the contract's single-orchestrator serialization, unreconciled. **[P2]** *(concurs with `consult.md:§2.6`)*

Mode C composes two sources that pull opposite ways on fan-out with no resolution rule. The contract is written for a serialized single-orchestrator build — B7 "One driver per branch/worktree… stand-down handshake" (`orchestration-pack.md:153`), B4 deconflict (`:150`), reflection "no standing co-operator… no resident agent is added" (`:186-188`). The Fable-5 rubric steers the opposite way — "Subagents: MORE… frequent delegation + async" (`claude-fable-5.md:28`) — and even discourages the explicit topology F1 wants ("Over-prescription degrades output… enumeration is a finding," `:29`). On the Fable-5 sessions these packs are generated for, the emitter is told both "spawn many async peers" and "one driver, deconflict, heavy per-merge bookkeeping" → an incoherent team either way. The template *had* the reconciliation the contract lost: read-only work fans out freely; writers serialize on isolated worktrees (`TEMPLATE:77-84`).

**Fix proposal:** Add a reconciliation rule — the one-writer-per-branch recording invariant holds; the *degree* of fan-out is the model-shaped variable the session rubric sets; async peers honor one-writer by living on separate worktrees (re-instate `TEMPLATE:77-84`). Resolve whether "no standing co-operator" survives Fable 5's sustained-peer-communication strength (ties to F10).

---

### F6 — Fixed two-role topology + no scale dial: one program-scale build hardcoded as universal. **[P2]** *(concurs with `consult.md:§2.1`)*

Component (c)'s "builder(s) and read-only auditor(s)" (`orchestration-pack.md:52`) is the only topology named, and the entire contract is calibrated to the single 152-spawn program build it was distilled from (`TEMPLATE:3`) — yet applied wholesale to any brief. The consultant documents the consequences from the user seat: mandatory milestone auditors gate-enforced on a two-person team (`consult.md:§2.2, §2.10`), concurrency machinery (registry/heartbeat/handshake) for concurrency a solo/pair team doesn't have (`§2.3`), a full reflection cadence where the operator *is* the drift check (`§2.4`). The field audit even shows the source build's own recording *decayed the moment it left clean single-orchestrator shape* for overlapping goals (`ORCHESTRATION-AUDIT.md:29-31,82`) — evidence the machinery is scale-fragile, not scale-free.

**Fix proposal:** Replace the fixed pair with the role-derivation rule (F1) and a **scale tier** (F4 + §4 recommendation) that gates which components/gates/roles emit; define the UX/security/domain auditor roles the binding rules already assume (restore `TEMPLATE:14`).

---

### F7 — The repo's own config omits `output.packs`; packs emit chat-only, so no corpus exists to review or regress. **[P2]**

`output.packs` is a documented *optional* key (`omnitune.config.example.yaml:36`, `schema.md:19`) but is absent from `omnitune.config.yaml`, so per `tune-goal-protocol.md:75-76` every pack is chat-only unless the user names a directory. Two harms: no persisted pack corpus to review/diff/regress (which is why this audit and the consultant's both had to reconstruct output rather than read it), and no feedback loop to surface F0–F6 in practice. The regression fixture tests that a pack *is emitted with 7 components*, not that it is *good*.

**Fix proposal:** Set `output.packs` in the repo config and in `/omnitune:install`'s default; add a **golden emitted pack** to the corpus with topology assertions (ties F3, and `consult.md` Rec 10).

---

### F8 — Mode C has no agent-team template or topology anti-pattern catalog — unlike Modes A and B. **[P2]** *(concurs with `consult.md` Rec 10)*

Mode A ships `agent-md-template.md` (a *single-agent* skeleton) + `common-anti-patterns.md`; Mode B ships a QA loop. Mode C ships only the gate-script templates (recording machinery) — **no team-design template, no orchestration anti-pattern list** (grep of `common-anti-patterns.md` for topology/team/delegation → nothing). The highest-judgment artifact in the plugin is emitted freehand. The template's role skeletons (`TEMPLATE:17-52`) are exactly the missing artifact, deleted in the F0 refactor.

**Fix proposal:** Add `pack-templates/agent-team.md` (role archetypes with model/effort/tools/context-budget slots, restored and parameterized from `TEMPLATE:17-52`) and a topology anti-pattern section (mono-model team; over-fan-out; general-purpose spawn for build/audit; auditor sharing builder context; no cheap-leg tiering; program apparatus on a pair build).

---

### F9 — Minor ambiguities / wording. **[P3]**

- False-promise wording at `tune-goal-protocol.md:51-53` (fixed by F2) misdirects the emitter to expect tiering the rubric never contains.
- "delegation policy in two lines" (`orchestration-pack.md:50`) hard-caps the most consequential design at two lines.
- `commands/tune-goal.md:11` / SKILL.md call `output.packs` "the default save location" without noting it is unset in the shipped config (F7).
- `claude-opus-4-8` manifest entry has `ga_date: null` (`models.json:81`); unrelated to orchestration, worth a sync pass.

---

## 3. Grounding dry-run — what the pipeline emits for the FieldNotes fixture

Tracing `tuner/regression/goal-pack-brief.md` (SvelteKit+SQLite CRUD, VPS dev stage, gates lint/test/e2e, M0–M4, CP1–3, quiet hours, device pass) on a **Fable 5** session — the model these packs target:

| Step | What happens | Failure |
|---|---|---|
| Step 0 intake (`:18-26`) | Collects the six recording facts — brief supplies all. | **No team-design or scale input gathered** (F4). Team designed from the milestone list alone. |
| Step 1 load (`:37-48`) | Loads `orchestration-pack.md` + `reflection-protocol.md` + **only** `claude-fable-5.md` + `_core`. | `models.json`, Haiku/Sonnet/GPT/Grok rubrics never seen (F2). Can't tier; can't target a multi-provider runtime team. |
| Step 2 emit (c) (`:56-58`) | "builder(s) + auditor(s)"; model/effort "from rubric" → silent → laddered. Fable rubric says "more subagents, async" + "don't over-prescribe." | **Mono-model team, all on Fable 5 at `high`**, count/roles improvised, tiering laddered; scaffold/lint/docs (Haiku's job per the library) run on the frontier model; fan-out steered high while B7/B4 pull serial (F5, F6). |
| Step 3 self-check (`:78-92`) | Traceability (recording) clean; scripts compile; ledger "clean" (mistier is laddered); 7 components exist; caps OK. | **READY.** Bad team never examined (F3). |
| Step 4 present | Pre-flight + reserved decisions + Assumptions block (now silently holding the entire team-tiering decision). | Operator sees a confident READY; the bad orchestration is buried in an assumptions ladder. |

The pipeline **deterministically produces an under-designed, mono-model team and certifies it green.**

---

## 4. Firm recommendation — the scale envelope (operator answer #1)

The operator asked us to recommend the scale envelope as an open design question. **Recommendation: a three-tier model, selected by two intake questions — (i) max concurrent writers/agents, (ii) horizon in days — with the tier gating what emits.** The framing that makes this defensible: **the field evidence validates exactly one tier (program); the other two are new and must ship *leaner*, not as the program contract with lines crossed out.**

| Tier | Selector | Team | State files | Reflection | Watchdog | record_check C2 (audit-per-tag) |
|---|---|---|---|---|---|---|
| **Solo/Pair (lean)** | ≤1 concurrent writer, or ≤~3 days | 1 orchestrator + 1 builder; **combined** code/UX auditor **only** on user-facing/risky milestones | CURRENT + MILESTONES + LOG + DECISIONS + BACKLOG **only** (drop registry/heartbeat/handshake) | **Off** — session-close append only; operator reviews at milestone close | Optional | **Satisfied by the gate battery** (lint/test/e2e green at HEAD) when no auditor role exists |
| **Squad (default)** | 2–4 concurrent writers, or ~1–3 weeks | + parallel domain builders on isolated worktrees; dedicated code + UX auditors | + session registry | Scheduled at **milestone-close** (not 24h) | On | Required for user-facing milestones |
| **Program (full)** | 5+ concurrent agents, or 3+ weeks | Full role taxonomy (security/CQ/UX/domain) | All seven, incl. registry/heartbeat/~8KB buffer | **Milestone-close or 24h** (current default) | Required | Required, all auditor roles |

**Program tier = the current contract, unchanged** — it is the one tier the Miracle Academy evidence actually supports. The defect today is that solo/pair and squad builds get the program contract. This aligns with `consult.md` Rec 1; I commit to the concrete tier definitions above and to the principle that **program is the only validated tier**, so the new tiers strip apparatus rather than the contract adding it. Pair this with F2's runtime-model question (a lean pair team may still run builders on Haiku/Grok) — scale tier and model tier are independent dials.

---

## 5. Ranked root-cause summary

| Rank | Root cause | Findings | Severity |
|---|---|---|---|
| 1 | **Distillation deleted the team-design content** — the contract was built from a field audit that only examined *recording* on an already-good team, and the "model-agnostic" refactor erased the template's concrete role taxonomy, `strongest-builder/xhigh` defaults, and serialization rules instead of parameterizing them. | **F0** (→F1) | P0 |
| 2 | **Tiering delegated to an empty, single-model, single-provider source** — the protocol claims the rubric supplies "which model runs what"; no rubric does; Mode C loads only the session model's rubric, so multi-model/multi-provider runtime teams cannot be expressed at all. | **F2** | P0 |
| 3 | **No topology contract / self-check / intake** — nothing steers toward good team design, nothing validates it (READY on a guess), and the intake never gathers what design needs (roles, independence, runtime models, scale). | F1, F3, F4 | P0/P1 |
| 4 | **The only "supervisor" checks decay, not design** — the co-operator the operator asked for was swapped for drift-detection cadences that are structurally blind to an initially-bad team. | **F10** | P1 |
| 5 | **One program-scale build hardcoded as universal; fan-out contradiction; no template/corpus** — scale mismatch marked READY, Fable-vs-contract fan-out conflict, no team template, no persisted packs to regress. | F5, F6, F7, F8 | P2 |

**One-line diagnosis:** *tune-goal productized the recording lessons of one expertly-hand-designed program build and, in genericizing them, deleted the team design itself* — so it now wraps state-file plumbing around whatever team the model improvises, certifies it green, and cannot express the multi-provider teams the operator runs or scale down to the builds the operator does.

**Recommended fix sequence:** F0/F2 (restore + parameterize the deleted topology and tier defaults; wire multi-provider rubric loading) → F4 (team-design + scale + runtime-model intake) → F1 (topology contract) → F3 + F10 (topology/design-fitness self-check — this *is* the t0 supervisor the operator asked for) → §4 scale tiers → F5/F6/F7/F8. F0 and F2 are load-bearing; F3/F4/F10 stop regressions and answer the operator's own instinct; the rest raise the ceiling.

---

*Propose-only: no pipeline, skill, or rubric file was modified. Companion reports in this directory: `consult.md` (UX critique — cited throughout where we concur), `research.md` (best-practices gap analysis).*
