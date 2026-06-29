# Design — Wiki/HTML Kept In Sync (D5)

- **Date:** 2026-06-29
- **Status:** approved design, pre-implementation
- **Parent:** D1–D4 merged to `main` at `543681b`. This is **D5**; **D6** (automated OpenAI sync derivation) is deferred.

## 1. Goal
Document OpenAI/Codex/audit-gate/version-log support in the wiki, and make the generated HTML render the **model lineage from `version-log.json`** so the "what's supported / last synced" docs cannot drift from reality.

## 2. Scope
**In:** a generated "Models & lineage" section in `scripts/build_wiki_html.py` sourced from `version-log.json` + `models.json`; prose updates to existing wiki pages; regenerate `wiki/index.html`; a test for the generator.
**Out:** automated OpenAI sync derivation (D6); new standalone doc pages beyond the generated Models section; any change to the rubric library / audit gate / version-log helpers.

## 3. Architecture
### 3.A `build_wiki_html.py` — generated Models section
- Add `_models_section(models_json, version_log_json) -> html` that builds a table: **provider · model id · status · last-synced · sources** (one row per manifest model; last-synced/sources pulled from the matching `version-log.json` entry where present). Pure, reads the two JSON files; tolerant of a missing/empty log (renders the manifest rows with blank lineage).
- Add a `("__models__", "models", "Models")` sentinel to `PAGES`; in `build()`, when the page is `__models__`, use `_models_section(...)` as the body instead of reading a `.md` file. Everything else (nav, search, template) is unchanged.
- Re-running the build always reflects the current JSON → no drift.

### 3.B Prose updates (existing wiki pages, minimal)
- `wiki/How-It-Works.md`: note provider-aware library (Anthropic + OpenAI/Codex), Codex detection, the iterated audit gate, and the version log.
- `wiki/Auto-Sync.md`: note the iterated independent-audit gate + that each applied rubric records a `version-log.json` entry.

### 3.C Regenerate
Run `python3 scripts/build_wiki_html.py` → commit the updated `wiki/index.html`.

## 4. Testing
`scripts/test_build_wiki.py`: `_models_section(...)` over a fixture manifest+log renders a row per model, includes a known model id (`gpt-5.5`) and its provider, and does not raise when the log is empty/missing. Registered in `validate.yml`.

## 5. Safety & decoupling
The generator reads data files only; no provider nouns hardcoded in logic. `check_public_clean.py` must still pass on the regenerated HTML (only model ids + public doc URLs are rendered).
