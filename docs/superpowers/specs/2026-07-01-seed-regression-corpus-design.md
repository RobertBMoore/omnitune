# Design — Seed the Regression Corpus (dogfood)

- **Date:** 2026-07-01
- **Status:** approved design, pre-implementation
- **Parent:** the omnitune arc (D1–D6, D2b-1/2) is merged + pushed at `9ee58fd`. This is a small standalone follow-up — the one deferred capability item flagged in the post-arc sweep.

---

## 1. Context & goal

`/omnitune:sync`'s gated self-apply has a **fail-closed regression-corpus floor** (`skills/sync/SKILL.md` step 4): if `model_sync.regression_corpus` holds fewer than **5** items, the no-drift verify returns *"cannot verify — manual review required"* and falls back to propose-only. The config points `regression_corpus` at `tuner/regression/`, but that directory **does not exist** — so in the omnitune repo the verify path can never run, even when dogfooding rubric derivation here.

The corpus is **agent-consumed**: no code parses items; the sync SKILL re-scores them under old vs new rubric and flags any verdict flip. It is inherently a **per-host-repo accumulation** (each consumer builds their own from `output.prompts/`). This slice seeds omnitune's **own dogfood corpus** so the verify path is exercisable in-repo.

**Goal:** create a curated ≥5-item regression corpus at `tuner/regression/`, spanning the prompt-classes + a skill-audit target, plus a mechanical gate keeping it seeded and well-formed.

## 2. Locked decisions
1. **Curated dogfood corpus** (not filler, not reconcile-only): fixtures chosen for **class/mode coverage** so drift in any class is catchable.
2. Fixtures are **agent-readable markdown** with `class:`/`mode:` frontmatter + input + a baseline note. No code format is imposed (nothing parses them at runtime); the frontmatter exists only so the CI gate can assert coverage.
3. A **dependency-free CI gate** (`scripts/test_regression_corpus.py`) keeps the corpus ≥5 items and well-formed — "seeded" becomes a checked invariant.
4. **No config change** (`regression_corpus: "tuner/regression/"` already set) and **no `tuner_check` change** (scope kept tight; the dedicated test covers the corpus).

## 3. Scope
**In:** `tuner/regression/README.md`; 6 fixtures; `scripts/test_regression_corpus.py` + CI registration.
**Out:** changing the sync verify logic (unchanged — it already reads the corpus per the SKILL); a `tuner_check` corpus-path assertion; consumer-side corpus tooling; auto-seed-from-`output.prompts/` automation (remains the SKILL's documented source-feed).

## 4. Architecture

### 4.A `tuner/regression/` fixtures
Each fixture is `tuner/regression/<slug>.md`:
```
---
class: command | code | factual-terse | creative-brief | adversarial-eval | skill-audit
mode: A | B
---
# <title>

<the raw prompt text, or (for skill-audit) a small SKILL.md snippet>

**Baseline:** <one or two lines describing what a good tuning/audit looks like — the reference a re-score is compared against, so a verdict flip is visible.>
```
The **6 fixtures** (cover every Mode B prompt-class + a Mode A target):
1. `command` (mode B) — an ops/build instruction.
2. `code` (mode B) — a "write a function" prompt.
3. `factual-terse` (mode B) — a terse factual question (must **not** be padded).
4. `creative-brief` (mode B) — a short marketing-copy brief.
5. `adversarial-eval` (mode B) — a red-team/eval prompt.
6. `skill-audit` (mode A) — a small `SKILL.md` snippet to audit.

Content is generic/omnitune-flavored (no external domain nouns → decoupling preserved). ≥5 satisfied (6, with margin).

### 4.B `tuner/regression/README.md`
Explains: what the corpus is (regression baselines re-scored by `/omnitune:sync`'s verify to catch quality drift when a rubric changes); the fixture format; that sync flags verdict flips; that this is omnitune's **dogfood** set and consumer repos accumulate their own (optionally auto-seeded from `output.prompts/`).

### 4.C `scripts/test_regression_corpus.py` (gate)
Dependency-free unittest, CI-registered. Asserts:
- `tuner/regression/` exists and holds **≥ 5** fixture `.md` files (excluding `README.md`).
- Each fixture has frontmatter with a **valid `class:`** (in the allowed set) and **valid `mode:`** (`A`/`B`).
- The set of `class:` values **covers all six** categories (so a future edit can't collapse coverage while still hitting the count).

## 5. Testing & DoD
- `scripts/test_regression_corpus.py` green + registered in `.github/workflows/validate.yml`.
- Full suite + `tuner_check`/`validate_plugin`/`check_public_clean` stay green.
- `tuner/regression/` has 6 well-formed fixtures + a README; the sync verify floor is clearable in-repo.
- Branch merged to `main` on approval; push only on explicit go-ahead.

## 6. Sources
- `skills/sync/SKILL.md` step 4 (the corpus floor); `docs/design/{01,04}-design*.md` (the regression-check + fail-closed-corpus rationale); `omnitune.config.yaml` (`regression_corpus` path).
