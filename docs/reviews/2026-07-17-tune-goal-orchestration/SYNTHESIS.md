# Synthesis — tune-goal orchestration review (3-agent panel + operator Q&A)

**Coordinator:** review session `c4c4537d` · **Date:** 2026-07-17
**Inputs:** `audit.md` (pipeline audit, ground-truth provenance), `research.md` (cited July-2026 best-practice gap analysis), `consult.md` (end-user simulation and critique), plus four operator answers collected mid-review.
**Status:** PROPOSE-ONLY consolidation. No pipeline files modified.

---

## 1. The diagnosis (all three reviewers converge)

**One line:** tune-goal productized the *recording* lessons of one expertly-hand-designed program build and, in genericizing them, **deleted the team design itself** — so it now wraps state-file plumbing around whatever team the emitting model improvises, certifies it green, and cannot express the multi-provider, multi-scale teams the operator actually runs.

The causal chain, provable from ground truth (audit F0):

1. The Miracle Academy field audit only ever examined **recording discipline** ("architecture A-, recording discipline C-") on a team a human had already hand-built well. Its lesson taxonomy (P0-1..P3-9) contains zero team-design lessons *by construction*.
2. The intermediate `ORCHESTRATION-TEMPLATE.md` still carried concrete topology: a named role taxonomy (security/code-quality/ux/domain auditors), agent skeletons with `model: <strongest available builder model>` / `effort: xhigh`, and a full serialization section (read-only fans out; writers serialize on worktrees).
3. The "model-agnostic" refactor into `orchestration-pack.md` **erased all of it**, redirecting to "the rubric" — and no rubric ever received the content. `agent-md-template.md` has no `model:`/`effort:` slots at all, so a pack *literally has no channel* to express tiering.
4. Nothing downstream catches this: the intake never asks team-design questions (F4), the contract has no topology rules (F1), and the self-check validates only recording mechanics — a mono-model, mis-tiered, improvised team ships **READY** (F3).

Cost of the defect, quantified (research G1): packs default the whole team to the one session model — the exact single-tier configuration Anthropic's published data shows a tiered team (frontier lead + workhorse workers) beats by **90.2%**.

Secondary convergent findings:
- **G4/F5** — the contract bakes Opus-era blocking serialization (B4/B6/B7) into *binding* constitution rules a rubric layer can't override, directly contradicting Fable 5's documented reversals (more subagents, async, long-lived workers). Fable-5 packs fight the model they target.
- **F10/G12** — the operator's original "Co-Operator" request was silently swapped for drift-detection cadences. Drift detection measures change-from-prior-state; a team that is *born* bad has no drift and is invisible to it forever. The operator's suspicion was directionally right — by omission, not commission.
- **F6/consult §2** — one 152-spawn program build hardcoded as universal scale; a two-person v1 gets program-grade apparatus (mandatory milestone auditors, session registry, reflection Dream, watchdog) marked READY.
- **F7** — `output.packs` unset in the repo's own config: packs emit chat-only, so no corpus exists to review or regress; this review is the first output-side signal and had to reconstruct the output.

## 2. What is right and must be preserved (research §2.3)

State-in-files · judgment-in-orchestrator · isolated workers with distilled reports (matches current context-engineering guidance) · deterministic gate scripts · fabrication-ledger discipline · the brief-intake refusal to invent specifics · `reflection-protocol.md`, which is a faithful file-based reimplementation of Anthropic's managed-agent Dreams. Fixes target defaults and topology, **not** this architecture.

## 3. Operator decisions resolved during the review

| Question | Answer | Disposition |
|---|---|---|
| Scale envelope | "You decide from findings" | **Decided — §4 tier model** (audit §4, consult Rec 1 concur) |
| Generate-vs-run model | Often differ; sometimes multi-provider (ChatGPT, Grok) | **Confirmed P0** — drives the delegation-tier layer + runtime-model intake |
| Co-operator | Concept liked; current mechanism "not ideal"; "need a better way" | **Decided — §5 layered oversight stack** replaces both the silent rejection and a standing resident |
| Bad pack artifacts | "Check the sessions DB" | Traced: the July sessions **built** the generator; no pack was ever consumed. Simulation + dry-run stand as evidence; F7 fixes the corpus gap going forward |

## 4. Scale recommendation (firm, as requested)

Three tiers, selected by two new intake questions — **max concurrent writers** and **horizon in days**. **Program tier = the current contract unchanged** (the only tier the field evidence validates); the new tiers *strip* apparatus rather than the contract adding any:

| Tier | Selector | Team | State files | Reflection | Watchdog | Audit-per-tag (C2) |
|---|---|---|---|---|---|---|
| **Solo/Pair** | ≤1 writer or ≤~3 days | orchestrator + 1 builder; combined auditor only on user-facing/risky milestones | CURRENT, MILESTONES, LOG, DECISIONS, BACKLOG | off (session-close append; operator reviews) | optional | satisfied by gate battery |
| **Squad** (default) | 2–4 writers or 1–3 weeks | + parallel domain builders on isolated worktrees; code + UX auditors | + session registry | milestone-close | on | user-facing milestones |
| **Program** | 5+ agents or 3+ weeks | full role taxonomy | all seven | milestone-close or 24h | required | all auditor roles |

Scale tier and **model tier are independent dials** — a lean pair team may still run builders on Haiku or Grok.

## 5. Supervision — the "better way" (replaces the co-operator fork)

Layered oversight, each layer catching a different failure at a different cost (research §1.12; audit F10):

1. **Deterministic gates** (record_check + lint/test/e2e) — bookkeeping decay. Always on. *(exists)*
2. **Human checkpoints** — direction, scope, irreversible actions. Always on. *(exists)*
3. **Orchestration-fitness review at pack-emit and milestone-0** — scores the team's *initial design* (the thing drift audits structurally cannot see). NEW — this is the t0 supervisor the operator's instinct asked for. Wired to the topology self-check.
4. **Per-milestone fresh-context verifier** of the orchestrator's own decisions/synthesis (cheap tier, disposable) — the missing middle layer; auditors today review the product, never the orchestrator's judgment. NEW.
5. **Scheduled reflection (local Dream)** — cross-run drift. Squad/Program tiers. *(exists; tier-gate it)*
6. **Standing/hierarchical supervisor** — reserved for true program scale (10+ agents). Surface as an explicit reserved decision instead of deciding it silently.

## 6. Action plan (phased; every item names its file)

### Phase 1 — Restore the deleted topology layer *(P0 — the load-bearing pair F0+F2/G1)*
1. **New `references/delegation-tiers.md`** (or a `delegation:` block in `models.json`): role → recommended model + effort **per provider** — frontier orchestrate/hard-audit · workhorse build · cheap explore/triage — seeded from tier notes already in the repo (Haiku "cheap leg", gpt-5.4-mini "for subagents", grok-code-fast; template's `strongest-builder`/`xhigh`). Cross-provider parity caveats included (structured outputs, vision, reasoning-extraction sensitivity).
2. **`references/agent-md-template.md`**: add `model:` and `effort:` frontmatter slots (mirrors the live subagent spec and SDK `AgentDefinition`).
3. **`references/orchestration-pack.md`**: add the **Topology contract** — role-derivation rule (roles from the brief's workstreams/domains, not a fixed pair); parallelism rule restored from `TEMPLATE:77-84` (read-only fans out freely; writers serialize on isolated worktrees); per-agent explicit justified `model:`+`effort:`; the four-part dispatch brief (objective · output format · tools/sources · boundaries); expand the two-line delegation policy into a real section; define the UX/security/domain auditor roles B2/B13 already assume.
4. **Rubrics (`_core.md` + per-model, all providers)**: add a **Delegation defaults** block — the rubric supplies the *fan-out posture* (Opus: fewer/serial; Fable: more/async/long-lived); the tier layer supplies *who runs what*.
5. **`tune-goal-protocol.md:51-53`**: fix the false promise; Step 1 loads the tier layer + the **runtime team's** rubrics (multi-provider set), not only the session rubric.

### Phase 2 — Intake and scale tiers *(P0/P1 — F4, F6, §4)*
6. **`tune-goal-protocol.md` Step 0**: team-design intake block — scale (writers + horizon → tier), workstream independence, required specializations, **runtime model set** (accept multi-provider), audit rigor. Ladder when unanswered.
7. **`orchestration-pack.md`**: mark each component/gate/rule `always-on` vs `tier-gated` per the §4 table.
8. **`pack-templates/record_check.py` + contract G1-C2**: audit-per-tag proportional to tier; gate battery satisfies at Solo/Pair.

### Phase 3 — Self-check and supervision *(P1 — F3, F10, F5/G4)*
9. **`tune-goal-protocol.md` Step 3.5 — topology self-check**: every agent carries justified model+effort; roles map 1:1 to workstreams (no unmapped role, no unowned domain); no all-one-tier team without stated reason; fan-out matches the target rubric's posture; Fable-5 targets scanned for reasoning-extraction language and required long-async affordances; failures → **CONDITIONAL** verdict, named.
10. **Supervision stack (§5)**: orchestration-fitness review at emit + M0; per-milestone fresh-context verifier role in the topology contract; tier-gate reflection; co-operator fork presented as a reserved decision (`orchestration-pack.md` reflection clause, `reflection-protocol.md`, protocol Step 4).
11. **`orchestration-pack.md` B4/B6/B7**: split correctness-serialization (one writer per file/branch — always binding) from throughput-serialization (collect-then-wave, blocking dispatch — an Opus-era default the target rubric may relax to async).

### Phase 4 — Ecosystem *(P2 — F7, F8, G2, G7, G9, G10)*
12. **`orchestration-pack.md` — coordination substrate section**: prefer native primitives (subagents / agent teams' file-locked task list + mailbox / `isolation: worktree` / Workflow tool) when the runtime is Claude; keep the file-based registry as the provider-agnostic fallback — which is also the *right* abstraction for mixed-provider teams no native primitive can host.
13. **`omnitune.config.yaml` + install default**: set `output.packs` so a pack corpus exists.
14. **New `pack-templates/agent-team.md`** (role archetypes with model/effort/tools/context-budget slots, restored from `TEMPLATE:17-52`) + topology anti-patterns in `common-anti-patterns.md` (mono-model team; over-fan-out; general-purpose build spawn; program apparatus on a pair build).
15. **`tuner/regression/`**: golden emitted pack with topology assertions (generate-then-score fixture — closes the loop that let this defect ship unnoticed).
16. **Polish**: untrusted-output line in guardrails (e); reflection cites the Dreams 1–100 session bound and may run on a cheaper model; optional adversarial-verify pass for CRITICAL findings; fix `claude-opus-4-8` `ga_date: null` in `models.json`.

## 7. Open items for the operator

1. Sign off on the §4 tier table (delegated to the panel; presented firm — Program unchanged, new tiers strip).
2. Sign off on the §5 supervision stack as "the better way" (fitness-at-t0 + per-milestone verifier, no standing resident below 10+ agents).
3. Green-light implementation (Phases 1–2 are the load-bearing fix; 3–4 complete it).
