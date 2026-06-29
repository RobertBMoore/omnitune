# Design — Version Logging System (D4)

- **Date:** 2026-06-29
- **Status:** approved design, pre-implementation
- **Parent:** D1+D2+D3 merged to `main` at `1cfe908`. This is **D4**; D5 (wiki/HTML + auto-sync derivation) remains out of scope.

## 1. Goal
A committed, append-only lineage so "is this rubric current / where did it come from?" is answerable, and (in D5) the wiki renders from it. Records every rubric add/update with its source + outcome.

## 2. Locked decisions
1. Storage = a **committed** `skills/omnitune/references/version-log.json` (machine-readable, validated, render-ready).
2. The helper mirrors `sync_state.py` discipline (atomic write, tolerate-and-reset, dependency-free).
3. Referential integrity is **blocking** in `tuner_check`; missing-entry-for-shipped-rubric is a soft **warning**.

## 3. Scope
**In:** `scripts/version_log.py` + tests; seed `version-log.json` for current shipped rubrics; `tuner_check.py` consistency check + tests; a one-line `/omnitune:sync` wiring; CI registration.
**Out:** wiki/HTML rendering (D5); automated OpenAI sync derivation (D5); changing the audit gate / ratchet / corpus.

## 4. Architecture

### 4.A `scripts/version_log.py` (dependency-free)
File shape: `{"schema": 1, "entries": [ ... ]}`. Each **entry**: `{"date": "YYYY-MM-DD", "model_id", "provider", "action": "add"|"update"|"deprecate", "last_synced", "source_urls": [...], "outcome"}`.
- `record(path, entry) -> dict` — require `date`, `model_id`, `action` (raise `ValueError` if missing or `action` invalid); default missing optional keys; **append** (never mutate prior entries); atomic write.
- `entries(path) -> list` — the entries list, or `[]` on missing/corrupt (tolerate-and-reset).
- `latest(path, model_id) -> dict|None` — the most recently appended entry for a model id (None if absent). Never raises.
- Atomic temp+`os.replace`; a corrupt file is treated as empty, never crashes a run.

### 4.B `tuner_check.py` — `_version_log_problems(skill_dir, models_json_path)`
If `references/version-log.json` exists (blocking):
- it parses and `schema` is an int;
- every entry has `date`, `model_id`, `action ∈ {add,update,deprecate}`;
- every entry's `model_id` exists in `models.json` (referential integrity).
Soft **warning** (via `manifest_warnings`): a model with a non-null `rubric` that has **no** log entry ("run /omnitune:sync or seed version-log.json").

### 4.C Seed + wiring
- Seed `version-log.json` with one `add` entry per currently shipped rubric (`claude-fable-5`, `claude-opus-4-8`, `claude-sonnet-4-6`, `claude-haiku-4-5`, `gpt-5.5`), `last_synced` from each rubric's frontmatter, `source_urls` from `models.json`, `outcome: "shipped"`.
- `skills/sync/SKILL.md` gated-self-apply: after the human commit, append a `version_log.record(...)` entry for the applied rubric.

## 5. Data flow
```
/omnitune:sync applies a rubric (after all gates + human commit)
  → version_log.record(references/version-log.json, {date, model_id, provider, action, last_synced, source_urls, outcome})
tuner_check: blocking referential integrity + soft "rubric without a log entry" warning
(D5 later: wiki renders the log)
```

## 6. Testing
`scripts/test_version_log.py`: record requires date/model_id/action (raises otherwise); append never mutates priors; `latest` returns the newest per model; `entries`/`latest` tolerate a corrupt file (→ []/None, no raise); atomic write. `tuner_check` tests: unknown-model entry → problem; malformed entry → problem; shipped-rubric-without-entry → warning not problem; clean log → no problems.

## 7. Safety & decoupling
No provider/model nouns in `version_log.py` (pure record-keeping). The log is append-only by API; `tuner_check` keeps it referentially honest. All D1–D3 invariants untouched.
