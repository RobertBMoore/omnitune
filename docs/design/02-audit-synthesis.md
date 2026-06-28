---
title: Portable Prompt-Tuner — Audit Synthesis (5 outside auditors)
date: 2026-06-14
inputs:
  - docs/reviews/2026-06-14-portable-tuner-design.md (design doc)
  - omnitune/ (prototype scaffold)
  - .claude/skills/skill-tuner/ (existing system under extraction)
auditor_lenses: [prompt-engineering, portability/architecture, safety/HITL, product/UX, adversarial red-team]
status: input to the final master auditor
---

# Audit Synthesis — what 5 outside auditors found

Five independent auditors reviewed the design doc, the `omnitune/` prototype, and the existing `skill-tuner` system, each through a different lens. This combines their findings: convergent themes first (ranked by how many lenses raised them + severity), then the combined idea set, then the open decisions for the master auditor and the operator.

## A. Convergent findings (multiple lenses agree)

### A1. The prototype is a skeleton, not a working prototype — ALL 5 lenses
`plugin.json` declares `"commands": "./commands"` but no `commands/` dir exists; the `references/` rubric (`model-best-practices.md`, `common-anti-patterns.md`, templates), both protocol files (`audit-protocol.md`, `prompt-rewrite-protocol.md`), and 5 of 6 wiki pages are absent. The plugin would load with zero commands and every audit/rewrite would fail at "First Action." The design doc's "logic unchanged" (§6) is therefore unverifiable, and the §10 smoke test cannot run. **This is the headline: the audit target the operator picked ("working prototype") does not yet exist as one.**

### A2. Model detection is the load-bearing weakness — prompt-eng, safety, red-team
"Query Anthropic's published model list" is specified as a vibe; the design's own Open Question #1 admits there is no official "latest GA model" endpoint. Consequences: false-positive interrupts on preview models, a fetch failure that blocks the user's real work, or a *missed* GA model that silently ships stale-optimal output — the exact harm the system exists to prevent. Convergent fix direction: pin a machine-readable source + GA discriminator, make detection **advisory/fail-to-proceed, never work-blocking**, and/or replace live-scrape with a bundled/community manifest (see B4).

### A3. Mode B can produce a WORSE prompt — prompt-eng, red-team
Two mechanisms: (a) **invented constraints** — the rubric rewards adding scope/cadence/price/success-criteria but has no dimension penalizing *fabricated* specifics; the worked example invents "11 emails + 5 SMS, $197, 14-day window" from "write the campaign emails, make them good," and scores PASS. (b) **the client-shaped rubric in disguise** — QA dims 5–7 ("names campaign/brand/persona/channel," "cadence/styling/offer specifics") are an email-copywriting checklist, not general prompt engineering; run on a terse code-gen or adversarial-eval prompt they score low and trigger a redraft that pads the prompt worse. The escape hatch only fires if *every* dim ≥4, which a legitimately terse prompt never satisfies.

### A4. Self-modification is "fail-trusting," not fail-closed — safety, red-team
The "human approval gate" is prose to the *same model* that authored the patch. Nothing mechanical stops the model from treating its own confidence as approval. The regression corpus is the only drift guard, yet it is optional, unseeded, host-supplied, AND scored under the very rubric the tool just rewrote — a closed loop with no external anchor. The **self-reference paradox**: a stale rubric frames the diff that updates the stale rubric; the corpus only catches *flips*, not uniform miscalibration, so the tool can mis-analyze a model change and still convince a human reviewer it handled it.

### A5. State ownership + concurrency — portability, safety, red-team
The rubric ships *inside* the plugin, so a model-patch edits plugin-internal files (clobbered on plugin update; N copies for an N-repo operator). `.sync-state.json` has no locking/atomic-write — and this repo's own MEMORY.md records that parallel sessions race here. Cross-skill `../sibling-skill/references/` paths are fragile under plugin namespace flattening. Convergent fix: **invert ownership — the host repo owns the snapshot/state/corpus via config**, addressed through `omnitune.config`, not `..` traversal.

### A6. Prompt-injection has no trust boundary — safety
The wizard reads host `CLAUDE.md`/`SKILL.md` as instructions; the sync loop feeds fetched web docs straight into a self-patch of its own rubric. A poisoned repo file or spoofed changelog can steer the config or inject rubric rules. No source allowlist, no signature/hash, no "treat fetched content as data not instructions" fence.

### A7. The interrupt UX punishes the user mid-task — product (strong), safety, red-team
Halting live work at the start of every run to pitch a "dedicated update session" is the textbook uninstall trigger; four escape hatches are a confession it's intrusive. After the second interrupt, `[s]` becomes muscle memory and the self-tuning thesis dies in practice. **This directly challenges the operator's stated design choice** and must go back to the operator (see C1).

## B. Combined idea set (the best ideas, deduped across lenses)

- **B1. Fidelity dimension + "fabrication ledger."** Add a Mode B rubric row: every constraint in the rewrite is either in the user's prompt or cited to a config `context_pointer`; uncited specifics are listed separately ("I assumed: …, source: …") for the operator to confirm — never silently baked into a PASS. (prompt-eng, portability)
- **B2. Prompt-class classifier before the rubric.** Classify {creative-brief, code, factual/terse, adversarial-eval, command}; make the brief-shaped dims N/A off-class; widen the escape hatch to "well-formed *for its class*." (prompt-eng, red-team)
- **B3. Empirical/hold-out validation of Mode B.** Instead of grading the rewrite against the same rubric that generated it, run rewrite vs original against 2–3 fixed inputs and diff the *outputs* — "did the rewrite move behavior in the intended direction?" Turns a style-checker into an optimizer. (prompt-eng)
- **B4. Community rubric registry / bundled manifest (kills the live-scrape).** Maintain one human-reviewed `model-best-practices.md` per model release in the public repo; installs *pull* the latest reviewed rubric, and the plugin's own release cadence is the detection signal. Solves A2 detection, A4 self-authoring risk, and makes the OSS community the QA layer. (product, portability, safety)
- **B5. Differential rubric versioning.** Store rules as "base prompt-engineering invariant" + "this-model delta." Sync rewrites only the delta and shows the operator the *structural* diff. The only clean way to handle cross-family drift (e.g. a future model that reverses literalism). (prompt-eng)
- **B6. Loosening-ratchet + no-write audit subagent + corpus floor.** A rubric patch may only *tighten* without a second approver; run the behavioral-diff/regression in a subagent with no Edit/Write tools (it proposes, parent commits only after a human signal); an empty/tiny corpus is **fail-closed** ("cannot verify no-drift"), never a clean pass. (safety, red-team)
- **B7. Untrusted-data fence + source pinning.** Wrap fetched docs and host files in an explicit "reference data, not instructions" fence; allowlist `docs.anthropic.com`/`www.anthropic.com`; record source URL + content hash in every patch. (safety)
- **B8. Retention layer.** Persist `{raw, rewrite, choice, scores}` per run → (a) learn a per-repo "house prompting style" from accept/reject/edit signals, (b) a prompt-quality trendline ("your first-draft prompts went 2.8→4.2"), (c) auto-seed the regression corpus from real usage. Converts a stateless utility into a companion that compounds. (product, prompt-eng, portability)
- **B9. Ambient mode.** A `UserPromptSubmit` hook that flags a weak prompt inline (spell-checker squiggle) with a one-key "tightened version?", slash command as fallback. Value is highest exactly when the operator didn't think to ask. (product)
- **B10. Restore the calendar-staleness gate.** The redesign dropped the 30-day age gate with the rename; docs can be revised without a new model. Keep both staleness sources. (red-team)
- **B11. `target_model` config field** distinct from the rubric's model — covers deprecation and "tuned for a model I don't run." (red-team)
- **B12. Exempt the tuner's own safety files from self-audit softening.** Mode A can audit `sync` and propose softening its own "never silently self-commit" emphasis (a legit safety-critical all-caps exception); hard-gate edits to fail-closed clauses. (red-team)
- **B13. Config `--check` lint mode for CI** — assert routing skills + house_rules/pointer paths still resolve; turn silent config rot into a failing build. (portability)
- **B14. Fix plugin hygiene** — `author` as an object not a string; remove the publisher name from the neutral core; drop the phantom `scripts/check-tuner-snapshot-age.mjs` reference; reconcile the two freshness mechanisms. (portability, prompt-eng)
- **B15. Publish behavioral diffs as content** — "what changed for prompting between Opus 4.8 and 4.9" is a shareable artifact that markets the tool and helps even non-installers. (product)

## C. Open decisions (for the master auditor to adjudicate, then the operator to confirm)

- **C1. Interrupt vs. passive badge.** The operator explicitly chose the just-in-time interrupt with skip/defer/snooze. Three auditors argue it should be a non-blocking status badge by default, with the hard interrupt opt-in. **Needs the operator's call** — the auditors' case is strong but the operator owns the UX intent.
- **C2. Rubric ownership.** Plugin-internal (current) vs host-owned-via-config (A5) vs community-registry-pulled (B4). These interact: B4 + host-owned is the most robust combination but is a bigger build.
- **C3. Detection mechanism.** Live-scrape (current, fragile) vs API `/v1/models` + GA discriminator vs bundled manifest updated via plugin releases (B4). Determines whether "self-updating" is reliable or a liability.
- **C4. Audience honesty.** Keep the "both technical + non-technical" claim, or rename the non-technical path to "guided" and cap its promises where routing/context-pointer fields are irreducibly technical.
- **C5. Scope/sequencing.** Everything above is more than a v0.1. The master auditor should recommend a phased build (what is v0.1 vs deferred) and an explicit cut list.

## D. What every lens agreed is genuinely good (keep these)
- The **install-as-audit-loop** (detect → interview → reflect → dry-run → write) — best-differentiated piece; dry-run-before-write is the right defense against a config that loads but doesn't work.
- The **"behavioral diff, not version bump"** reframe for model-sync — the real IP.
- The **safety *intent*** ("the agent is not the auditor of its own work") — correct principle, just not yet mechanically enforced.
- The **config-surface decomposition** (§2 table) — the right decoupling contract.
