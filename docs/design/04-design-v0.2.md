---
title: Portable Prompt-Tuner — v0.2 Design (the trust layer)
date: 2026-06-14
builds_on: v0.1 (runnable, smoke-tested) + the 6-agent audit synthesis
status: in progress
---

# v0.2 — the trust layer

v0.1 made the plugin real, portable, and safe-by-abstinence (sync is propose-only; it cannot self-patch). v0.2 makes it **trustworthy enough to self-apply a rubric** and adds the verification scaffolding the audit panel demanded. Scope is the deferred list from the v0.1 decision record plus the live-sync mechanism.

## v0.2.1 — Gated self-apply (replaces v0.1 propose-only)
The audit panel's hardest finding (A4): the "human approval gate" was prose to the same model that wrote the patch. v0.2 makes the gate **mechanical**:

1. **No-write audit subagent.** The behavioral-diff + regression run in a dispatched subagent whose tool grant excludes `Edit`/`Write`/`Bash`. It returns a *proposed* rubric (as text) + a verdict. The parent never lets that subagent write.
2. **Tighten-only ratchet** (`scripts/rubric_ratchet.py`). Diff the proposed rubric against the current one. A patch may **tighten** unattended; any **loosening** — a lowered pass bar, a `must`→`should` weakening, a removed dimension, or a removed/softened safety clause — is **blocked** unless an explicit second-approver marker is present. The tool cannot quietly grade itself easier.
3. **Fail-closed regression corpus.** If `regression_corpus` is empty or below a floor (default 5 items), the verify path returns **"cannot verify no-drift — manual review required,"** never a clean pass. An unseeded corpus is fail-closed, not "0 flips, looks fine." Corpus auto-seeds from `output.prompts/` history.
4. **Two-key model confirmation.** Before acting on a "new model," the id must come from an allowlisted source AND be echoed to the operator for a yes ("I see `claude-fable-5` GA at <url> — correct?"). No silent action on a scraped/hallucinated id.
5. **Commit only after a human signal the model cannot self-emit.** The parent applies the (ratcheted, regression-checked) rubric only after the operator approves; the audit subagent that drafted it never commits.

## v0.2.2 — Config + manifest lint (`scripts/tuner_check.py`)
A runnable, CI-friendly validator (the panel's B13). Asserts:
- `omnitune.config.yaml` parses and has the required fields.
- Every `routing[].skill` exists under `skills.root`.
- Every `context_pointers[].point_to`, `house_rules`, `reserved_decisions` path resolves.
- `model_sync.channel` is one of `badge|interrupt|manual`.
- In the plugin's `models.json`, every **GA** model has an existing rubric file; deprecated/limited may be null.
Exit nonzero on any failure → silent config rot (a renamed skill, a moved voice file) fails the build instead of degrading Mode A/B at runtime.

## v0.2.3 — Atomic state (`scripts/sync_state.py`)
`tuner/.sync-state.json` handling, hardened for this-repo-style concurrent sessions:
- Atomic write (temp file + `os.replace`).
- Tolerate-and-reset on parse failure (a corrupt state file never blocks a run).
- Per-session keying into a map, not a single last-writer-wins record.
- Snooze stored as an ISO-8601 instant; comparison is monotonic; a malformed/absent deadline is treated as "expired, re-offer."

## v0.2.4 — Live model sync (Sonnet/Haiku setup — DONE this iteration)
- `models.json` now carries `sync_entrypoints` (stable discovery URLs + Anthropic-domain allowlist) and real `source_urls` per model.
- Sonnet 4.6 + Haiku 4.5 rubrics upgraded from `derived-tier` to `synced-from-docs` against the live overview (context window, output cap, thinking modes, pricing, knowledge cutoff). One item (effort default) remains `(verify)` — honestly flagged, to be closed when the effort docs are fetched.
- `/omnitune:sync` discovery flow: fetch `sync_entrypoints` (allowlisted), read the model's row, derive/verify the rubric, replace `verify_remaining` items, propose (v0.1) or gated-apply (v0.2.1).

## Cut from v0.2 (still deferred to v1.0)
Retention/house-style learning · behavioral-diff-as-published-content · community contribution registry · ambient `UserPromptSubmit` hook · global cross-repo snooze preference.

## Build order
1. `tuner_check.py` (lint) — TDD; immediately demonstrable against the scratch repo + the plugin itself.
2. `rubric_ratchet.py` (tighten-only) — TDD; the self-apply keystone.
3. `sync_state.py` (atomic state) — TDD.
4. `sync` SKILL upgrade to gated self-apply wiring the three scripts + the no-write subagent.
5. Smoke test the whole v0.2 path.

## Build status (2026-06-14) — v0.2 core COMPLETE
- ✅ `tuner_check.py` + `miniyaml.py` — 11 tests; demonstrated clean/broken on real repos.
- ✅ `rubric_ratchet.py` — 9 tests; demonstrated BLOCK on a real attempt to delete `_core`'s floor-rule section, ALLOW with `--approve-loosening`.
- ✅ `sync_state.py` — 5 tests (atomic, per-session, corrupt-tolerant, snooze).
- ✅ `sync` SKILL upgraded to gated self-apply (two-key model confirm → no-write subagent → ratchet → corpus floor → post-apply lint → human commit).
- ✅ **Live model sync proven on a real new model:** Claude **Fable 5** (GA 2026-06-09) fetched from live docs → sourced `claude-fable-5.md` rubric authored (captures the two Opus-4.8 reversals + the refusal-trigger rule) → manifest wired → plugin lints clean. Sonnet 4.6 / Haiku 4.5 upgraded to `synced-from-docs`.
- **25/25 script tests green.**

## Still deferred to v1.0
Retention/house-style learning · behavioral-diff-as-published-content · community contribution registry · ambient hook · global cross-repo snooze preference.
