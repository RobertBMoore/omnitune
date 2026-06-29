# Design — Iterated Independent-Audit Gate (D3)

- **Date:** 2026-06-29
- **Status:** approved design (audit-panel-hardened), pre-implementation
- **Reviewed by:** independent 3-reviewer panel (convergence-logic · omnitune-fidelity/safety · process-practicality) — all returned REVISE; their findings are folded in below.
- **Parent effort:** D1 (rubric foundation) + D2 (Codex portability) merged to `main` at `9390606`. This is **D3**; D4 (version log) and D5 (docs) remain out of scope.

---

## 1. Context & goal

omnitune's v0.2 "gated self-apply" already mechanizes the dangerous moment — omnitune rewriting its own rubric via `/omnitune:sync` — with a no-write audit subagent, a tighten-only ratchet (`rubric_ratchet.py`), a fail-closed regression corpus, two-key model confirmation, and human-only commit. D3 replaces the *single* audit pass with an **iterated, author-independent panel that runs to mechanical convergence**, then runs the existing gates unchanged.

**What D3 honestly is (and is not).** The convergence helper makes the loop's *termination* deterministic — the agent cannot declare its own audit *finished*. The panel adds *context-independent* reviewers (fresh context, no-write, not the author). D3 does **not** make *thoroughness* provable, and (when all reviewers share one model) does not remove model-level systematic blind spots. The ratchet + regression corpus + human commit remain the real safety backstops; D3 strengthens the *entry condition* in front of them. The spec says this plainly so the gate is not oversold.

## 2. Locked decisions

1. Convergence termination is **mechanical** (`scripts/audit_ledger.py`), computed from an **append-only event log** the agent cannot rewrite.
2. D3 wraps the **rubric-derivation path**, reusing the existing ratchet/corpus/human-commit gates unchanged.
3. A **change-magnitude cheap-path** keeps cost proportionate: trivial diffs use the existing single-pass audit; only substantial changes pay for the panel.
4. Defaults: **2** clean rounds, cap **3**, material **high**; validated and config-overridable within safe bounds.

## 3. Scope

**In scope:** `scripts/audit_ledger.py` + tests; the iterated-panel protocol in `skills/sync/SKILL.md`; the change-magnitude cheap-path; config params + **blocking** `tuner_check.py` validation; `.gitignore` entry for the ledger; CI registration.

**Out of scope:** the pre-build *plan* audit (a one-time D1-design activity, not a feature); the version log (D4); docs (D5); any change to `rubric_ratchet.py`, the regression corpus, or two-key confirm (reused as-is).

## 4. Architecture

### 4.A `scripts/audit_ledger.py` — deterministic convergence tracker

Dependency-free; mirrors `sync_state.py` (atomic temp+`os.replace`, tolerate-and-reset). The **agent supplies judgment** (which findings exist, their severity, their resolution); the **helper computes termination** and treats all agent-supplied strings as opaque. The ledger is an **append-only event log** keyed by a monotonic `seq`.

**Events**
- `round`: `{seq, type:"round", round_no, reviews:[{reviewer_id, lens, findings:[{fingerprint, severity, summary}]}]}`. A finding is **open** until a later `status` event resolves it.
- `status`: `{seq, type:"status", fingerprint, status, reason}` — `status ∈ {open, reconciled, declined}`.

**Fingerprint (parent-computed, deterministic — not reviewer free-form).** Reviewers return `(location, category, severity, summary)`; the parent calls `fingerprint(category, location)` to derive a stable key, so the same defect always collides to the same fingerprint and distinct defects can't be hand-merged. `category ∈ {correctness, safety, citation, domain, structure, other}`; `location` = a rubric section id/anchor or `global`.

**API**
- `fingerprint(category, location) -> str` — pure slug `slug(category)+":"+slug(location)`.
- `reset(path)` — start an empty ledger for a derivation run.
- `record_round(path, round_no, reviews) -> dict` — append a `round` event (reject a duplicate/earlier `round_no` — rounds are monotonic). Validate finding shape; coerce an unknown severity to `low`. **A round is `complete` only if ≥ `min_reviews` (default 2) distinct `reviewer_id`s submitted reviews and none equals the author id**; an incomplete round is recorded but does **not** count toward convergence.
- `set_status(path, fingerprint, status, reason) -> dict` — append a `status` event. `reconciled`/`declined` **require** a non-empty `reason` (else rejected). This is the only way a finding leaves `open`; the agent cannot rewrite a prior round.
- `convergence(path, clean_rounds=2, cap=3, material="high") -> dict` → `{verdict, trailing_clean, rounds, open_material:[...], declined_material:[...]}`:
  - Severity rank `low<medium<high<critical`; **material** = rank ≥ rank(`material`); an unknown `material` arg normalizes to `high` (never raises).
  - Each fingerprint's **current status** = its newest `status` event, else `open`.
  - **new-material in round R** = material fingerprints whose first appearance is round R.
  - A **clean round** = a *complete* round that (a) introduced no new-material finding **and** (b) leaves no material finding `open` as of its `seq`. (a) and (b) reinforce: a re-listed still-open finding keeps a round from being clean.
  - `open_material` = material fingerprints whose current status is `open`. `declined_material` = those `declined` (surfaced to the human).
  - **Verdict precedence:** `rounds == 0` → `NOT_CONVERGED`. Else **CONVERGED** iff `trailing_clean ≥ clean_rounds` **and** `open_material` empty. Else **CAP_EXCEEDED** iff `rounds ≥ cap` (escalate with `open_material`). Else **NOT_CONVERGED**. Never raises.

### 4.B Protocol — iterated panel in `skills/sync/SKILL.md`

Extends v0.2.1 gated-self-apply. Two-key model confirmation runs **first** (unchanged). Then:

1. **Change-magnitude gate (cheap-path).** Diff the proposed rubric vs current using the existing ratchet diff. **Trivial** change (≤ `audit_panel_threshold` changed directives, no new sections, no severity changes — e.g. a `(verify)` resolution or a `lastSynced` bump) → run the **existing single-pass no-write audit** (v0.2 behavior, unchanged) and skip the panel loop. **Substantial** change (new rubric, new sections, multiple rules) → the panel loop below.
2. **Capability probe.** If independent subagent dispatch is unavailable (no `Task`; Codex without `multi_agent = true`, per `references/codex-tools.md`) → **fall back to propose-only**; never run "reviewers" in the parent's own context (that would be self-review).
3. `audit_ledger.reset(<ledger-path>)`.
4. **Round R:** dispatch a panel of **2–3 independent no-write reviewers** — tools exclude `Edit`/`Write`/`Bash`, no further dispatch, no network; fresh context; **none is the author** — with **materially distinct lens prompts**: (a) correctness/fidelity, (b) fail-closed safety + citation discipline, (c) provider-domain accuracy. **Where the harness allows, run at least one lens on a different provider model** (the repo runs under both Claude and OpenAI) to reduce correlated blind spots. The parent passes the **carry-forward set** (prior rounds' still-open findings, by fingerprint + summary) into each reviewer prompt so round R is a true *re-review*. Each reviewer returns `(location, category, severity, summary)`; the parent computes fingerprints and calls `record_round(round_no=R, reviews=[...])` with reviewer ids.
5. **Reconcile.** For each open material finding, either fix the rubric and `set_status(fp, "reconciled", reason)`, or `set_status(fp, "declined", reason)` with a written justification. (Reasons are persisted and surfaced at human sign-off — a decline is auditable, not a rubber stamp.)
6. `convergence(...)`. `NOT_CONVERGED` → next round (step 4). `CAP_EXCEEDED` → stop, surface `open_material` to the operator, **fall back to propose-only**. `CONVERGED` → continue.
7. **Existing gates, unchanged and still mandatory even on a thin CONVERGED audit:** tighten-only ratchet → regression-corpus floor (≥5 or manual-review) → post-apply lint (`tuner_check.py`) → **maintainer sign-off / human commit** (shown the declined-material reasons + any CAP escalation). The panel never commits.

### 4.C Config + validation

`omnitune.config.model_sync`: `audit_clean_rounds` (2), `audit_round_cap` (3), `audit_material_severity` (`high`), `audit_panel_threshold` (changed-directive count for the cheap-path, e.g. 3). `tuner_check.py` validates these **blocking** (consistent with its fail-closed contract): types correct; `audit_clean_rounds ≥ 1`; `audit_round_cap ≥ audit_clean_rounds`; `audit_material_severity ∈ {low,medium,high,critical}` **and not stricter than `high`** (raising it would silently neuter the panel — treat as a loosening requiring explicit human sign-off, like the ratchet). Absent keys → defaults.

### 4.D State & concurrency

Ledger path is **per derivation run, in the gitignored namespace**: `omnitune/.audit-ledger-<session-or-run-id>.json` (sibling of `.sync-state.json`). Add the glob to `.gitignore` so intermediate findings never become committable. `reset()` at step 3 makes a stale ledger from a crashed run harmless; per-run keying prevents concurrent `/omnitune:sync` runs from clobbering each other (the same hazard `sync_state.py` was hardened against).

## 5. Data flow

```
/omnitune:sync derives a proposed rubric  → two-key model confirm (unchanged)
  → change-magnitude gate: trivial → single-pass v0.2 audit; substantial → panel loop:
       capability probe (no independent dispatch → propose-only)
       reset() → [ panel (2–3 no-write reviewers, distinct lenses, carry-forward) → record_round
                   → reconcile (set_status + reason) → convergence() ]
                 NOT_CONVERGED: repeat | CAP_EXCEEDED: escalate+propose-only | CONVERGED: continue
  → ratchet → regression corpus (≥5) → tuner_check → human sign-off (sees declines/escalations) → commit
```

## 6. Worked example (substantiates convergence)

Defaults 2/3/high. Proposed rubric drops the core floor-rule.
- **R1** (complete: reviewers `r-safety`, `r-correct`): safety reviewer reports `(location="audit-floor", category="safety", severity="critical")` → parent fp = `safety:audit-floor`, recorded open. New material → R1 not clean. `trailing_clean=0`.
- **Reconcile:** author restores the floor-rule → `set_status("safety:audit-floor","reconciled","restored the floor-rule section")`.
- **R2** (carry-forward includes the now-reconciled item; reviewers re-check it): no new material; `safety:audit-floor` current status `reconciled` → clean. `trailing_clean=1`.
- **R3:** no new material; nothing open → clean. `trailing_clean=2`, `open_material` empty → **CONVERGED**. (A clean-from-start rubric converges at R2; persistent new material by R3 → `CAP_EXCEEDED` → propose-only.)

## 7. Safety & decoupling

`audit_ledger.py` holds no provider/model nouns and treats fingerprints/summaries as opaque — pure bookkeeping. The append-only event log means the agent adds judgment but cannot *rewrite* it; resolution requires a reasoned `status` event; declines and escalations are surfaced to the human. Independence is *context-level* (no-write fresh reviewers, author excluded), optionally *model-level* (cross-provider seat) — not a guarantee against shared model bias, which is why the ratchet/corpus/human gates stay mandatory. All existing v0.2 invariants are preserved; D3 only adds a stricter, mechanically-terminated entry condition.

## 8. Testing

`scripts/test_audit_ledger.py` (unittest, dependency-free, registered in `validate.yml`):
- new material resets trailing-clean; two clean rounds + all resolved → CONVERGED.
- an `open` material finding blocks CONVERGED even across clean rounds; a re-listed still-open finding keeps a round non-clean.
- `reconciled`/`declined` require a reason (rejected otherwise); a `declined`-with-reason counts resolved and appears in `declined_material`.
- a status event resolves a finding that is **not** re-listed in later rounds (the reconciliation path works).
- **anti-gaming:** an incomplete round (< `min_reviews`, or author-as-reviewer) does not count toward convergence; `rounds==0` → NOT_CONVERGED; `clean_rounds=0`/`cap<clean_rounds` are rejected by validation (tested in `test_tuner_check`).
- `material="high"` ignores low/medium; unknown `material` normalizes to high; intra-round duplicate fingerprint → "open wins".
- monotonic round_no enforced; append-only (no silent overwrite); atomic write + tolerate-and-reset on corruption; `reset` clears state; per-run path keying.

## 9. Sources

- `docs/design/04-design-v0.2.md`; `skills/sync/SKILL.md` (v0.2.1 flow + safety invariant); `scripts/rubric_ratchet.py`, `scripts/sync_state.py` (reused patterns); D3 audit-panel findings (2026-06-29).
