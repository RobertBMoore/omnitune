# Design — Sync-Automation Phase 2 (mechanize the prose-only gates)

- **Status:** approved design, awaiting implementation plan
- **Date:** 2026-07-03
- **Depends on:** Phase 1 (`sync_propose.py`, H1 `hook_guard.py`) — shipped in `2942d0c` + `f6d31ea`
- **Related:** `docs/superpowers/specs/2026-06-29-iterated-audit-gate-design.md`, `.../2026-07-01-seed-regression-corpus-design.md`
- **Scope decision:** Tier 1 only (G1–G4). Tier 2 (orchestration driver, fetch-hop/id validators) and Tier 3 (wiki-trigger, staleness) are deferred to Phase 3.

## 1. Context & goal

The v0.2 gated self-apply flow in `skills/sync/SKILL.md` has 11 steps. Most are already backed by a tested, deterministic script (`resolve_model`, `detect_model`, `sync_sources`, `sync_propose`, `audit_ledger`, `rubric_ratchet`/`ratchet_gate`, `tuner_check`, `version_log`, `sync_state`, `hook_guard`, `build_wiki_html`). What remains are **seams the agent still executes by hand from prose** — several of which are *safety or correctness backstops*. A backstop enforced only by prose is one an agent can skip on its own confidence, which is exactly the failure mode omnitune's fail-closed posture exists to prevent.

**Goal:** mechanize the four Tier-1 gaps into focused, CLI-runnable, independently-tested units, and rewire `skills/sync/SKILL.md` to call them. **No gate semantics change** — this converts existing prose rules into runnable checks.

A code-grounded reconstruction found nine gaps total (the handoff's "11/14" tallies came from parallel sessions and split orchestration finer). This spec covers the four that close a safety/correctness hole:

| # | Gap | Prose location today |
|---|-----|----------------------|
| G1 | Regression-corpus floor check (≥5 or "cannot verify no-drift" → propose-only) | SKILL §4 (Gated self-apply) |
| G2 | Manifest add/update + semantic validation (hand-edited `models.json`) | Derive step §5 + no validator |
| G3 | Panel carry-forward set assembly (open findings → next round) | SKILL §2 (Loop / Reconcile) |
| G4 | Post-apply revert on lint failure | SKILL §5 (Post-apply lint) |

## 2. Locked decisions

1. **Four focused units, not one module.** Matches the repo's one-script-per-concern pattern (`sync_propose`, `sync_sources`, `ratchet_gate` are each single-purpose with a paired `test_*.py`). Rejected: a consolidated `sync_gates.py` (couples unrelated concerns); functions-only with no CLIs (breaks SKILL.md's `python3 scripts/X.py` driveability).
2. **G3 lives on `audit_ledger.py`** as a function (the module is functions-only, no CLI), reusing `convergence()`'s status resolution so it can never disagree with termination.
3. **Corpus floor stays a constant + `--floor` flag (default 5).** No new config key; `model_sync.regression_corpus` already supplies the folder path.
4. **Auto-seed is opt-in (`--seed N`), off by default.** Preserves the propose-only spirit; the checker reports seed candidates but does not write fixtures unless asked.
5. **G4 revert is path-scoped.** Only the rubric path passed is reverted (checkout-if-tracked, delete-if-new); unrelated working-tree edits are never touched.
6. **No live network, no orchestration driver, no config-schema churn.**

## 3. Scope

**In:** four units (G1–G4) + their tests + `skills/sync/SKILL.md` rewiring + Definition-of-Done update.
**Out (Phase 3):** end-to-end sync driver (G5), fetch-hop provenance validator (G6), two-key id-presence check (G7), local wiki-regen trigger (G8), calendar-staleness computation (G9).

## 4. Architecture

Each unit is dependency-free (stdlib only, `miniyaml` for config where needed), CLI-runnable with `main()`+usage, and mirrors the exit-code conventions of the existing scripts (`0` pass, `1` gate-fail, `2` bad-invocation/tooling-unavailable).

### 4.A `scripts/corpus_check.py` (G1) — regression-corpus floor gate

- `floor(regression_dir, min_items=5)` → `{count, floor, ok, reason, seed_candidates}`.
  - `count` = `*.md` in `regression_dir` minus `README.md`.
  - `ok = count >= floor`. When `not ok`, `reason` is the verbatim SKILL §4 string: `"cannot verify no-drift — manual review required"`.
  - `seed_candidates` = list of prompt files found under the `output.prompts` dir (default `docs/prompts/`) not already represented in the corpus.
- `seed(regression_dir, prompts_dir, n)` → copies up to `n` candidate prompts into the corpus as fixtures (deterministic ordering by filename; skips existing; returns the list written). Invoked only via `--seed N`.
- CLI: `corpus_check.py <regression_dir> [--floor N] [--prompts DIR] [--seed N]`. Prints JSON status; exit `0` if `ok`, `1` if under floor. `--seed` re-checks after seeding and reports the new count.
- **Depends on:** filesystem only. **Consumed by:** SKILL §4 (replaces "if corpus < 5 … manual review").

### 4.B `scripts/manifest_propose.py` (G2) — manifest entry emit + validate

Two verbs in one cohesive module (manifest correctness):

- `entry <id> <models.json>` → a ready-to-merge model row: `{id, provider, family, status, ga_date, deprecated_date, rubric, source_urls}`. Built from `resolve_model` (normalization/provider/family) + `sync_sources` (source_urls, provider entrypoints). **On update** (the id already exists in the manifest) the existing `status`, `family`, `ga_date`, and `deprecated_date` are preserved (mirrors `sync_propose`'s `(entry or {}).get(...)` fallback); **on add** they default to `status=ga`, dates `null` (never fabricated). `rubric` = `references/rubrics/<provider>/<id>.md`. Prints the JSON row for the operator to merge.
- `validate <models.json>` → semantic check of **every** entry (complements H1's structural integrity):
  - `status` ∈ `{ga, limited, deprecated, retired}`.
  - `rubric` path (when non-null) matches `references/rubrics/<provider>/<id>.md`.
  - every `source_urls` host ∈ `providers.<provider>.allowlist_domains` (reuse `sync_sources.allowed`).
  - dates are `null` or ISO `YYYY-MM-DD` (no fabricated non-null placeholders).
  - Returns a problems list; prints them; exit `1` if any, else `0`.
- **Depends on:** `resolve_model`, `sync_sources`. **Consumed by:** derive step (emit) + a pre-write gate (validate).

### 4.C `carry_forward(path)` in `audit_ledger.py` (G3) — panel re-review payload

- `carry_forward(path)` → sorted `[{fingerprint, summary, severity}]` for every finding whose **newest** status is still open (raised, not `reconciled`/`declined`). Reuses the same newest-status-wins resolution `convergence()` uses, so the carry-forward set and the termination decision are always consistent.
- Summaries are taken from the finding's most recent round appearance; severity from the same.
- Function-only (no CLI added — matches the module; the panel loop calls it the way it already calls `record_round`/`convergence`).
- **Depends on:** ledger internals only. **Consumed by:** SKILL §2 Loop (replaces hand-assembled carry-forward set).

### 4.D `scripts/apply_guard.py` (G4) — post-apply lint + scoped revert

- `apply_guard.py <rubric-path> [repo_root]` (`repo_root` defaults to the git toplevel; config = `<repo_root>/omnitune.config.yaml`, manifest = `<repo_root>/skills/omnitune/references/models.json`):
  1. Run `tuner_check.check(repo_root, config_text, models_json_path)`.
  2. **Pass** → exit `0`.
  3. **Fail** → revert only `<rubric-path>`: `git checkout HEAD -- <path>` if the file is tracked at HEAD, else delete the newly-written file; print the `tuner_check` problems; exit `1`.
  - Git unavailable / bad invocation → exit `2` (mirrors `ratchet_gate.py`).
- Path-scoped revert guarantees unrelated working-tree edits are untouched (important under this repo's concurrent sessions).
- **Depends on:** `tuner_check`, `git`. **Consumed by:** SKILL §5 (replaces "or the change is reverted").

## 5. Data flow (derive → gated apply, with the four units wired)

```
sync_propose ─┐
              ├─ (agent drafts rubric)
manifest_propose entry ── operator merges row ── manifest_propose validate  (G2, exit 1 blocks)
              │
audit panel loop:
   record_round ─▶ carry_forward ─▶ next round ─▶ convergence  (G3 feeds the loop)
              │
   CONVERGED ─▶ rubric_ratchet (tighten-only) ─▶ corpus_check floor  (G1, exit 1 → propose-only)
              │
   write rubric ─▶ apply_guard (tuner_check; revert on fail)  (G4, exit 1 reverts)
              │
   human approval ─▶ commit ─▶ version_log.record ─▶ build_wiki_html
```

Every G-unit is a **gate that fails closed**: a nonzero exit drops the flow back to propose-only or reverts the write. None can be waved through on model confidence.

## 6. Testing & DoD

- **Per-unit dependency-free `unittest`** (tmpdirs/fixtures), matching existing `test_*.py`:
  - `test_corpus_check.py`: under-floor / exactly-at-floor / over-floor; `README.md` excluded; seed-candidate listing; `--seed` writes N, skips existing, re-checks.
  - `test_manifest_propose.py`: `entry` shape + no fabricated dates + rubric-path convention; `validate` catches bad status, wrong rubric path, off-allowlist source, non-ISO date; clean manifest passes.
  - `test_audit_ledger.py` (extended): `carry_forward` returns only still-open findings; excludes reconciled/declined; empty ledger → `[]`; all-declined → `[]`; agrees with `convergence().open_material`.
  - `test_apply_guard.py`: pass → exit 0, file kept; fail (tracked) → reverted to HEAD, exit 1; fail (new) → deleted, exit 1; unrelated edits untouched; git-absent → exit 2.
- **Definition of Done:**
  1. Four units implemented + all four suites green.
  2. Existing suite still green (**234 passing** at baseline; total grows).
  3. `skills/sync/SKILL.md` §2/§4/§5 + derive step rewired to invoke the scripts; Definition-of-Done section updated to reference them.
  4. No new config keys; no gate-semantics change; no live network.
  5. `carry_forward` output verified consistent with `convergence()` on the same ledger.

## 7. Non-goals

Orchestration driver, fetch-hop/id validators, wiki-trigger, staleness computation — deferred to Phase 3 with its own decision gate. This spec deliberately mechanizes only the four gaps that harden an existing safety/correctness backstop.

## 8. Sources

- `skills/sync/SKILL.md` (v0.2 gated self-apply flow — the prose being mechanized)
- `scripts/audit_ledger.py`, `scripts/sync_propose.py`, `scripts/sync_sources.py`, `scripts/tuner_check.py`, `scripts/ratchet_gate.py` (existing patterns + integration points)
- `omnitune.config.schema.md`, `omnitune.config.yaml` (`model_sync.regression_corpus`, `output.prompts`)
