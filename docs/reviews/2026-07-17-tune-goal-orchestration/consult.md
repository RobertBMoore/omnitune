# Consultant review — `/omnitune:tune-goal` from the end user's seat

**Reviewer:** Consultant (Opus 4.8, x-high) — three-agent review team (auditor / researcher / consultant)
**Date:** 2026-07-17
**Question:** The operator reports that tune-goal packs specify a *bad orchestration of agents*. Sitting in the end user's chair, is the agent-team the pack designs actually good to live with — and if not, what exactly do we change?

**Method:** Read the full user-facing surface (`commands/tune-goal.md`, `wiki/Tune-Goal.md`, `skills/omnitune/SKILL.md`, `tune-goal-protocol.md`, `references/orchestration-pack.md`, `reflection-protocol.md`, both gate templates, the Opus 4.8 / Fable 5 / `_core` rubrics, the regression brief fixture). Simulated a realistic mid-size brief and walked the protocol by hand without fixing up the result. Pulled the two prior sessions (`3d08a743`, `f6c6ad3d`).

**Session-model note:** this walk selects the **Opus 4.8** rubric (the model this session runs). The two "bad" field packs were generated on **Fable 5**. That divergence is itself a finding (see §2.6) — the two rubrics give *opposite* delegation defaults.

**Teammate incorporation:** at synthesis time `audit.md` and `research.md` did **not yet exist** in this directory (empty as of the write). This report therefore stands alone; cross-references to the pipeline audit and the best-practices gap analysis could not be folded in. Where my findings likely overlap theirs, I flag it inline as *[likely also in audit/research]* so the operator can dedupe later.

---

## 1. The simulated brief and the pack it yields

### 1.1 The brief (a real user would paste this)

```
/omnitune:tune-goal "
Project: Cadence — a team availability & meeting scheduler for small teams.
Outcome: ship v1 — Google OAuth login, calendar connect, an availability grid,
and a booking flow. Two people build it: me (operator/PM) and one full-stack dev.
Stack: Next.js (App Router) + Postgres (Prisma) + Playwright e2e.
Environments: staging (staging.cadence.app) and production (cadence.app).
Deploy: `vercel deploy` (staging), `vercel deploy --prod` (production).
Gates: `pnpm lint`, `pnpm test`, `pnpm e2e`.
We want to move fast but not break prod.
"
```

This is squarely the case the wiki invites: multiple milestones, a deploy that can block, parallel-ish work, a "don't break prod" approval. The "When it earns its weight" table (`wiki/Tune-Goal.md:11-19`) says *use tune-goal*. No `omnitune.config.yaml` in the user's repo → **standalone mode**.

### 1.2 Walking Step 0 — brief-intake gate

The gate (`tune-goal-protocol.md:16-35`) needs six facts. Honest inventory of my brief:

| Required fact | In brief? | Gate action |
|---|---|---|
| Deploy target (stages, cmd, dev URL) | Mostly — staging URL given, no explicit "verify at" URL | Ask which URL e2e verifies against |
| Gate commands **+ the env each names** | Commands yes; **envs missing** (`pnpm test` DB URL? `pnpm e2e` BASE_URL?) | Ask — skip-as-pass rule needs the names |
| Checkpoint owners | **Missing** — only "don't break prod" | Ask; propose a prod-deploy checkpoint |
| Quiet hours + break-glass severity | **Missing** | Ask |
| Milestone shape | Derivable (4 features) | Propose M0–M4, confirm |
| Target directory | **Missing** (standalone) | Offer to save |

So the gate emits ~5 numbered questions. **This step is genuinely good** — it refuses to invent commands/owners/URLs and ladders every assumption. Keep it. The user answers tersely:

```
1. e2e verifies against https://staging.cadence.app
2. pnpm test needs DATABASE_URL; pnpm e2e needs BASE_URL
3. I own all checkpoints, here in this chat
4. Quiet hours 23:00–08:00 CT; only a P0 breaks them
5. M0 scaffold, M1 auth, M2 calendar+grid, M3 booking, M4 launch — yes
6. Save under docs/orchestration/cadence/
```

### 1.3 Walking Step 1 — rubric selection (**where it breaks**)

`tune-goal-protocol.md:50-54` states plainly:

> *"The rubric, never this protocol, supplies the model-shaped values: **the delegation default (which model orchestrates, what builders/auditors run on)**, effort and verbosity defaults… Where the rubric is silent, ladder the choice as an assumption."*

I read the Opus 4.8 rubric and `_core.md` looking for that delegation default. **It is not there.** The only delegation content in the entire Opus 4.8 rubric is one behavioral line (`claude-opus-4-8.md:41`): *"Subagents: fewer by default — steer explicitly when you want parallel fan-out; rein in single-file delegation."* `_core.md` §5.4 adds a generic "use subagents for parallel/isolated work" sentence. **Neither names which model orchestrates, what builders run on, what auditors run on, how many, or on what effort.**

The consequence, followed honestly: the rubric is *silent* on the concrete topology, so **Step 1's fallback fires and the entire agent-team design is laddered as an assumption** — improvised by the generating model, badged "I assumed," and shipped. The one thing the user is complaining about — the orchestration of agents — is the one thing the pipeline does **not** actually specify. Everything downstream (state files, gates, reflection cadence, line caps) is pinned to the byte; the team topology is a guess with a disclaimer.

### 1.4 The pack it emits (component by component, un-fixed-up)

Following `orchestration-pack.md` components (a)–(g) + the reflection clause:

**(a) Goal prompt** — a MISSION statute book: mission, M0–M4 with per-milestone reading maps, the state-file schema block verbatim, the numbered checkpoint list (CP-prod-deploy at minimum), the definition of done. *Fine, if heavy.*

**(b) Constitution** — CLAUDE.md-shaped, ~90 lines, auto-loads every session: bootstrap block, guardrails digest, the loop with RECORD, context-economy rules, precedence order, evidence rule, two-line delegation policy. *Auto-loaded into every context window.*

**(c) Agent definitions — the improvised part.** With no rubric topology, the model ladders a team. For "Cadence, a UI-bearing app," the plausible emit (and what the wiki's own worked example seeds, `Tune-Goal.md:96`) is:

| Role | Count | Model/effort (laddered) | Contract |
|---|---|---|---|
| Orchestrator (the operator's driver session) | 1 | session model, xhigh | judgment, dispatch, all merges, consumes verdicts |
| Builder subagent(s) | 1–2 | session model | implement milestone, commit from first block, report summary+SHA+gate tails |
| **Read-only code auditor** | 1 | session model | files `audits/<M>-code.md` per milestone |
| **Read-only UX auditor** | 1 | session model | files `audits/<M>-ux.md` per milestone |
| Reflection session (local Dream) | periodic | fresh context | curated lesson store + append-only drift audit, every milestone-close-or-24h |
| Staleness watchdog | cron | none (bash) | alerts on stale heartbeat |
| Chartered child sessions (B11) | on new goal | — | own charter + ledger + 1 pointer line in CURRENT |

**(d) State-file contracts** — seven artifacts: CURRENT (≤25 lines), MILESTONES table, append-only LOG, DECISIONS ADRs, BACKLOG, **session registry with per-session heartbeat**, **~8KB rotated continuity buffer**.

**(e) Guardrails digest** — env pin, destructive-command deny list at the settings layer, secrets placement, operator-only items.

**(f) Operator pre-flight checklist** — disable host MCPs/plugins, injected-catalog size audit, numbered checkpoints, device-pass calendar, quiet hours + break-glass, **wire the watchdog to a scheduler + alert channel yourself**.

**(g) Gate scripts** — `record_check.py` (blocks every merge/tag; with default `auditors: []` it **blocks any tag lacking ≥1 `audits/<M>-*.md`**), `staleness_watchdog.sh` (cron).

**Self-check (Step 3)** passes: traceability walk is clean (all P0-1..P3-9, T1..T15 map), the two scripts `py_compile`/`bash -n` cleanly, the ladder is complete, seven components exist, constitution ≤90 lines, CURRENT ≤25. **Verdict: READY.**

That is the crux in one sentence: **a pack whose agent team is an unsteered guess passes every check the pipeline runs, and ships marked READY.** *[likely also in audit.md]*

---

## 2. Critique — living with this team on a two-person v1

The evidence base is explicit (`orchestration-pack.md:17-24`): *"a multi-day, high-change single-orchestrator field build and its independent orchestration audit."* The entire contract is calibrated to **that** scale. tune-goal then applies it wholesale to any brief that trips a low bar. My two-person Cadence build gets program-grade apparatus. Concretely:

### 2.1 The team is right-*shaped* but wrong-*sized* — and the sizing is never chosen
The core architecture (state in files, judgment in orchestrator, labor in disposable builders, evidence over memory) is sound; the audit said so. But **there is no scale dial.** A solo/pair v1 and a 20-agent multi-week program get the same seven state files, the same mandatory milestone auditors, the same scheduled reflection session, the same registry/handshake machinery. Nothing in the protocol asks "how big is this?" and tailors the emit. This is the single largest source of "bad orchestration": *scale mismatch presented as READY.*

### 2.2 Mandatory milestone auditors are gate-enforced ceremony
`record_check.py` C2 **blocks the milestone tag** unless an audit report file exists (`orchestration-pack.md:99`, `record_check.py:108-123`). For M0 (scaffold) this means a two-person team cannot close the milestone through its own gate until someone files a prose audit — of a scaffold. Worse, **the gate checks the *presence of a file*, not the *quality of a review*** — so it is trivially satisfied by a stub and simultaneously obstructive. The predictable user response is to (a) write fake audit files to unblock, or (b) delete the gate. Either outcome discredits the record discipline that is the whole point of the pipeline.

### 2.3 Half the state machinery is for concurrency the team doesn't have
Session registry, per-session heartbeat, one-driver-per-worktree, stand-down handshake before relaunch (`orchestration-pack.md:69-70`, B7) are all machinery for **many concurrent orchestrator sessions**. With one operator + one dev working mostly sequentially, these are dead ceremony that still cost bookkeeping and still get gate-checked.

### 2.4 The reflection session solves a problem the supervised team doesn't have yet
The local-Dream (`reflection-protocol.md`) — a scheduled fresh-context session producing two artifacts with different disposal semantics, a promotion queue, adopt/discard asks pushed to status — earns its cost on a *multi-week autonomous single-orchestrator run* where nobody is watching for judgment drift. On a two-person actively-supervised build, **the operator is the drift check.** Running the full Dream cadence here is meta-process overhead.

### 2.5 Operator burden is front-loaded and partly theater
Pre-flight (`orchestration-pack.md:81-86`) demands, before feature one: disable MCPs/plugins, audit catalog size, set checkpoints, build a device-pass calendar, declare quiet hours + break-glass, and **wire the watchdog to a scheduler and an alert channel** (the wiki admits "the script cannot schedule itself," `Tune-Goal.md:138`). A solo operator will skip the wiring — at which point the watchdog, a headline safety leg, silently does nothing, and *crash detection becomes theater.* *[likely also in audit.md]*

### 2.6 The topology flips with the generating model — and nothing pins the runtime model
Generate this pack on **Opus 4.8** → rubric says "fewer subagents, rein in single-file delegation" → a lean, orchestrator-does-more team. Generate the **identical brief on Fable 5** → rubric says "MORE subagents, async orchestration, keep long-lived context-holding subagents" (`claude-fable-5.md:28,51`) → a fan-out team. **Same project, opposite designs, decided by whichever model happened to be loaded.** And the pack is tuned to the *generator's* model while **nothing records or pins the model the team will actually run on.** Generate on Opus, run on Fable (or vice versa) and the delegation policy is mis-tuned with no warning. The two "bad" field packs were Fable-generated; this session is Opus — the operator may be comparing across this exact fault line.

### 2.7 "Collect all verdicts → consolidated fix waves" stalls a small team
B6 (`orchestration-pack.md:145-146`) forbids per-fix redeploys: collect every audit verdict, then batch. On a large parallel build this prevents redeploy thrash. On a two-person build where the dev is builder *and* fixer, it forces wait-then-batch latency and context reloading to optimize a deploy-cost profile the small team doesn't have.

### 2.8 The pack is exempt from the best practices it enforces
The constitution (~90 lines) + guardrails digest + statute-book goal prompt + inline continuity buffer all load into **every** context window. `_core.md` §1.8/§2 context-economy rules would flag some of this — but **Mode C never runs Mode A on its own output.** There is no step that audits the emitted constitution/goal-prompt against the session model's own rubric. The generator preaches concision and ships a governance load. *[likely also in research.md]*

### 2.9 Overlapping external checks multiply triage
Three "external check" legs (deterministic gates, scheduled reflection, watchdog) **plus** two milestone auditors **plus** the drift audit means findings overlap; the solo operator triages duplicates. B4 release-once mitigates *rework*, not *triage load*.

### 2.10 The deadlock is self-inflicted and predictable
Concrete failure: milestone tag blocked because `audits/<M>-ux.md` isn't filed — because the two-person team never actually spun up a standing UX auditor. The team cannot close the milestone through the gate without either faking the file or writing a formal disposition (`orchestration-pack.md:112-118`, G2). A gate meant to catch *recording decay* now blocks *shipping* on *ceremony the scale never needed.*

### 2.11 What the prior sessions actually show (and don't)
Both named sessions are the **construction** of this pipeline, not consumption of its output:
- `3d08a743` ("Optimize Fable 5 goal prompts") — the user *builds* Mode C and, tellingly, asks for *"an AI 'Co-Operator' Agent that runs above the Orchestrator."* The design's answer (`reflection-protocol.md:33-46`) **explicitly rejects a standing co-operator** in favor of scheduled cadences. The user intuited they wanted a supervisor; the design talked them out of it without surfacing the fork.
- `f6c6ad3d` ("Execute fable5 orchestration pack charter") — the build session that wrote the 21 pipeline files **hit its session limit mid-run** ("You've hit your session limit · resets 8:30am"). The very session building the crash-resilience machinery ran out of budget partway — live evidence that these long autonomous runs are fragile, which is the problem the watchdog exists to paper over.

**The load-bearing observation:** the orchestration contract was **reverse-engineered from one large build's audit and has never been output-validated** — nobody has generated a pack, run a real project team from it, and audited the result. The self-check only validates *mechanics*. The operator's current complaint is the **first output-side signal**, and the pipeline had no tripwire for it because **nothing scores the team the pack designs.** *[likely also in audit.md]*

---

## 3. Prioritized recommendations (TOP-10)

Ordered by user impact. Each names the exact file and the change.

**1. Add a scale-tier to the intake gate; tier-gate the whole emit.**
`skills/omnitune/tune-goal-protocol.md` (new Step 0.5) + `references/orchestration-pack.md` (mark each component/gate `always-on` vs `tier-gated`). Ask team size + horizon and select a profile — `solo/pair` (lean), `squad` (default), `program` (full) — that governs auditor count, whether the reflection session schedules, and whether registry/handshake machinery emits. This is the meta-fix from which most others fall out; without it a two-person v1 gets program-grade apparatus marked READY.

**2. Pin a concrete delegation topology in each rubric — stop laddering the team.**
`references/rubrics/anthropic/claude-opus-4-8.md`, `claude-fable-5.md`, `_core.md`: add a **Delegation defaults** block giving the actual topology the protocol already *claims* to read — orchestrator model+effort, builder model+effort, auditor model+effort, and the fan-out trigger. Today `tune-goal-protocol.md:50-52` promises this and the rubric doesn't deliver, so the one design the user is complaining about is improvised and disclaimed.

**3. Add an orchestration-fitness self-check that constrains team *quality*, not just mechanics.**
`skills/omnitune/tune-goal-protocol.md` Step 3: add checks such as — no role without a distinct responsibility *and* a distinct `tools:` allowlist; auditor roles ≤ tier cap; every mandatory gate maps to a failure the brief's scale can actually suffer; total always-loaded governance ≤ a byte budget. Today a structurally valid pack with a nonsensical team passes every check and ships READY.

**4. Make milestone audits proportional (fix G1 C2).**
`references/orchestration-pack.md` (G1 C2) + `references/pack-templates/record_check.py` CONFIG: require an audit report only for milestones the brief flags user-facing/risky, and let the **gate battery** (lint/test/e2e green at HEAD) satisfy the requirement when no dedicated auditor role exists. Blocking a scaffold tag on a missing UX-audit *file* is gameable ceremony that discredits the gate.

**5. Decouple the team's runtime model from the generator's model.**
`skills/omnitune/tune-goal-protocol.md` Step 0 (new required fact) + `commands/tune-goal.md`: ask "which model(s) will the team run on?" and select delegation defaults from **that** model's rubric, not the session's. Otherwise an Opus-generated pack ships Opus's "fewer subagents" default to a team that will run on Fable (opposite default), silently.

**6. Right-size the state-file set by tier.**
`references/orchestration-pack.md` component (d): mark the session registry, per-session heartbeat, stand-down handshake, and ~8KB continuity buffer as **multi-session-only** (squad/program). A solo/pair pack ships CURRENT + MILESTONES + LOG + DECISIONS + BACKLOG only. Registry/handshake machinery is dead weight when one driver works at a time.

**7. Make the scheduled reflection session opt-in below program tier.**
`references/orchestration-pack.md` (reflection clause) + `references/reflection-protocol.md` (Cadence): default the local-Dream on only at squad/program tier and horizon ≥ N days; for solo/pair degrade to "session-close append only; operator reviews at milestone close." A full Dream cadence on a two-week supervised build is meta-process the team doesn't need.

**8. Turn Mode A on the pack's own output (governance-footprint budget).**
`skills/omnitune/tune-goal-protocol.md` Step 3 + `references/orchestration-pack.md` component (b): run the emitted constitution and goal prompt through the **session rubric's** context-economy rules, and cap the always-loaded footprint per tier (solo/pair constitution ≤ ~40 lines). The pack currently preaches concision while shipping a governance load into every context window.

**9. Surface the co-operator/supervisor choice as a reserved decision instead of deciding it silently.**
`references/reflection-protocol.md:33-46` + `skills/omnitune/tune-goal-protocol.md` Step 4: present the fork (scheduled cadence vs a standing supervisor session) as a numbered reserved decision and let the operator choose. The originating user explicitly asked for a co-operator; the design overruled them without showing the tradeoff.

**10. Add a round-trip validation fixture that scores the emitted team, closing the feedback loop.**
`tuner/regression/` (new generate-then-audit fixture) + a new `references/rubrics/anthropic/orchestration-fitness.md` scoring dimension: emit a pack for the FieldNotes/Cadence brief, then score the *emitted team design* (role sizing, topology, gate proportionality), not just traceability. The contract was derived from one build's audit and never output-validated; the first real complaint had no automated tripwire because nothing scores what the pack designs.

---

## 4. Open questions for the operator

1. **Scale envelope.** Is tune-goal meant to serve solo/pair v1 builds at all, or only multi-day multi-agent programs? The wiki's bar is low; the contract is calibrated high. Which is the true target — because Rec 1 depends on the answer.
2. **The co-operator you asked for.** In `3d08a743` you wanted a standing supervisor above the orchestrator; the design gave you scheduled cadences instead. Do you still want the co-operator option reopened (Rec 9), or are you satisfied the cadence answer was right?
3. **Generate-vs-run model.** Do you routinely generate a pack on one model and run the team on another? If yes, Rec 5 is urgent; if you always match them, it's minor.
4. **The actual bad artifacts.** Can you point to the *generated pack files* a real project consumed (paths)? The two named sessions built the pipeline; they didn't run a project from a pack. Real output would let us validate fixes against ground truth instead of my simulation.
5. **Auditor value.** On your real builds, do the mandatory code+UX auditors produce reviews you act on, or are they filed-and-ignored? That decides whether Rec 4 should *soften* the requirement or *strengthen* the review behind it.
6. **Watchdog reality.** Is the staleness watchdog actually wired to a scheduler + alert channel on your runs, or is it a checklist item that gets skipped? If skipped, the crash-detection leg is theater and Rec 1's tiering should drop it for small builds rather than pretend it protects them.

---

## Appendix — what I could not incorporate
- **`audit.md` / `research.md`** were not present in this directory at synthesis time; findings tagged *[likely also in audit/research]* are my best guess at overlap for later dedupe.
- **The Miracle Academy field build** (`9455aeb3…`) and its `ORCHESTRATION-AUDIT.md` are the true upstream evidence but live outside this repo; I relied on the distilled P0-1..P3-9 / T1..T15 rows in `orchestration-pack.md` rather than the raw audit.
- **Simulation, not live generation.** I walked the protocol by hand; I did not invoke Mode C to emit an actual pack. The team roster in §1.4 is the honest expected emit, not a captured artifact.
