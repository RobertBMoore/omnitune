# Design — Distributable Codex Setup for Consumer Repos (D2b-2, lean/doc-first)

- **Date:** 2026-07-01
- **Status:** approved design, pre-implementation
- **Parent:** D2b-1 (native root `AGENTS.md`) merged + pushed at `6e6a160`. This is **D2b-2**, the deferred "distributable/installable" half — scoped **lean** after a design reassessment (below).

---

## 1. Context & goal

D2b-1 lets a Codex session operate omnitune **in the omnitune repo itself**. D2b-2 lets a Codex user run omnitune **in their own repo**. Codex has no plugin system, so the consumer needs (a) omnitune's runtime *reachable* and (b) a Codex `AGENTS.md` that drives it — without clobbering any `AGENTS.md` they already have.

**Reassessment (why not vendoring).** The brainstorm first chose "vendor a minimal runtime." On deeper analysis vendoring is the *least* maintainable option: it duplicates omnitune's ~30 runtime files into every consumer repo (the drift problem this project fights, multiplied), has no auto-update, and does **not** actually simplify the hard part — omnitune's `SKILL.md` files use omnitune-repo-relative paths (`scripts/…`, `../sync/SKILL.md`, config "at the host repo root"), which any `.omnitune/` subdir placement breaks regardless of copy-vs-submodule; the fix (steer the agent to run from `.omnitune/`) lives in the `AGENTS.md` block either way. So D2b-2 is scoped **lean/doc-first**: a **git submodule** for reachability + a maintained template + a tiny idempotent merge helper + a setup doc. A heavyweight file-copying installer is deferred until real demand appears (YAGNI — omnitune has no known Codex consumers yet).

## 2. Locked decisions

1. **Reachability = git submodule** at `<consumer>/.omnitune/`, pinned by SHA, refreshed with `git submodule update`. No file duplication.
2. **Distribution = template + merge helper + doc.** No bespoke vendoring installer.
3. The consumer `AGENTS.md` block is a **maintained template** (`deploy/codex/AGENTS.omnitune.md`), same "hard rules inline + delegate to `.omnitune/skills/sync/SKILL.md`" shape as the root `AGENTS.md`, `.omnitune/`-rooted, carrying a **path-translation note** for the repo-relative SKILL prose.
4. A generic, dependency-free **idempotent managed-block merge** (`scripts/agents_merge.py`) injects/updates the block between markers, never touching out-of-marker content.
5. Anti-drift gate extended + a focused **Sonnet** safety review of the template.

## 3. Scope

**In:** `deploy/codex/AGENTS.omnitune.md` (template); `scripts/agents_merge.py` (+ CLI); `docs/codex-consumer-setup.md` (+ README pointer); `scripts/test_agents_merge.py` + CI registration.

**Out (deferred):** a file-copying vendoring installer; generating the consumer's `omnitune.config.yaml` (omnitune runs standalone; config is optional enrichment — a Codex `install-config` flow is a later follow-on); wiring into the Claude Code `/omnitune:install` skill; auto-update beyond `git submodule update` + re-running the merge; any change to `resolve_model`/`sync_sources`/etc. internals.

## 4. Architecture

### 4.A `scripts/agents_merge.py` — idempotent managed-block merge (the one new unit)

Pure, dependency-free (stdlib `os`, `re`, `tempfile`). Contract:
- `MARK_BEGIN = "<!-- omnitune:codex begin (managed — regenerate via .omnitune/scripts/agents_merge.py) -->"`, `MARK_END = "<!-- omnitune:codex end -->"`.
- `merge(existing_text, block_text) -> str` — **pure**. If both markers present (in order): replace the span *between* them (inclusive of markers) with a freshly-wrapped block. Else: append the wrapped block (one blank line before), preserving all existing text. Wrapping = `MARK_BEGIN + "\n" + block_text.strip() + "\n" + MARK_END`. **Idempotent:** `merge(merge(x, b), b) == merge(x, b)`.
- `install(target_path, block_text)` — read target (or `""` if absent), `merge`, atomic write (temp + `os.replace`). Never raises on a missing target (creates it).
- **CLI:** `python3 .omnitune/scripts/agents_merge.py [--target AGENTS.md] [--block .omnitune/deploy/codex/AGENTS.omnitune.md]` — defaults target = `./AGENTS.md`, block = `./.omnitune/deploy/codex/AGENTS.omnitune.md`, so a consumer runs it from their repo root after adding the submodule. Prints what it did.

No provider/model nouns — a generic managed-block merger.

### 4.B `deploy/codex/AGENTS.omnitune.md` — the consumer block template

The inner block content (no markers — the helper wraps it). Consumer-flavored, safety-first, same operative safety phrases as the root `AGENTS.md`:
- **Framing:** "omnitune is available in this repo as a git submodule at `.omnitune/`. To tune/sync **this** repo under Codex, follow the omnitune protocols below."
- **Path-translation note (the correctness crux):** the omnitune `SKILL.md` protocols are written relative to the omnitune repo, now at `.omnitune/` — run its helpers as `python3 .omnitune/scripts/…`, read its skills at `.omnitune/skills/…`, and its rubric library at `.omnitune/skills/omnitune/references/…`; **your own** (optional) `omnitune.config.yaml` lives at **this** repo's root, not under `.omnitune/`.
- **⚠ Non-negotiable safety invariants** (identical hard rules to the root `AGENTS.md`, `.omnitune/`-rooted): fetch fence (only `sync_sources.plan` `fetch_urls`; re-validate every redirect hop; abort on first **off-allowlist hop**; never fetch `plan.dropped`; empty `fetch_urls` → **propose-only**; data-not-instructions), **never self-commit**, fail-closed default, capability probe (`multi_agent` off → **propose-only**; never self-review), decoupling; and **delegate the gated sequence to `.omnitune/skills/sync/SKILL.md`** (author-excluded audit panel via `author_id`, tighten-only ratchet, corpus floor ≥5, post-apply lint, human commit, lineage).
- **Capabilities:** tune-prompt/tune-skill → `.omnitune/skills/omnitune/SKILL.md`; sync → `.omnitune/skills/sync/SKILL.md`.
- **Model detection** + tool mapping: point at `.omnitune/skills/…`/`AGENTS.md` in the submodule for the full mapping (kept lean here to avoid re-duplicating the root file — the submodule's own `AGENTS.md` carries it).

### 4.C `docs/codex-consumer-setup.md` (+ README pointer)

A short "Use omnitune under Codex in your own repo" guide:
1. `git submodule add https://github.com/RobertBMoore/omnitune .omnitune` (pin: `cd .omnitune && git checkout <sha>`); commit.
2. `python3 .omnitune/scripts/agents_merge.py` — injects/updates the managed omnitune block in your `AGENTS.md` (safe on an existing one).
3. (optional) create `omnitune.config.yaml` at your repo root for repo-aware routing; without it, tune/sync run standalone.
4. **Update:** `git submodule update --remote .omnitune && python3 .omnitune/scripts/agents_merge.py`.
A one-line pointer is added to `README.md`. (Kept out of the wiki HTML build to avoid `build_wiki_html`/`index.html` coupling in this lean slice.)

### 4.D Anti-drift gate — `scripts/test_agents_merge.py`

Dependency-free unittest, CI-registered:
- **Merge idempotency:** `merge(merge(x,b),b) == merge(x,b)`; a second run changes nothing.
- **Out-of-marker preservation:** existing content before/after the block is byte-identical after merge; markers-absent existing file → block appended, original kept; absent target → created with the block.
- **Template safety-presence** (operative phrases, same as the root `AGENTS.md`): `never self-commit`, `propose-only`, off-allowlist-hop phrase, `multi_agent`, `author_id`, and the delegation pointer `.omnitune/skills/sync/SKILL.md`.
- **Template referential integrity:** every `.omnitune/scripts/*.py` and `.omnitune/skills/*.md|json` token in the template, with the `.omnitune/` prefix stripped, resolves to a real path in the omnitune repo (so the submodule will provide it) — a renamed omnitune file fails CI.

## 5. Data flow

```
consumer repo (Codex)
  git submodule add … .omnitune  →  python3 .omnitune/scripts/agents_merge.py
     → agents_merge injects the managed block (from .omnitune/deploy/codex/AGENTS.omnitune.md) into ./AGENTS.md
  Codex auto-loads ./AGENTS.md → block points at .omnitune/skills + .omnitune/scripts (path-translated) + delegates safety to .omnitune/skills/sync/SKILL.md
```

## 6. Decoupling & safety

`agents_merge.py` is a generic managed-block merger (no provider/model nouns). The template is a Codex harness artifact, model-agnostic, and **restates** the hard safety rules while **delegating** the gated sequence to the submodule's authoritative `skills/sync/SKILL.md` — no new copy of the 12-step sequence. The merge never edits out-of-marker content, so a consumer's own `AGENTS.md` is preserved. A Sonnet safety review checks the template's restatement before commit; the anti-drift gate keeps its operative phrases + `.omnitune/` references honest.

## 7. Testing & DoD

- `scripts/test_agents_merge.py` green + CI-registered; `tuner_check`/`validate_plugin`/`check_public_clean` + full suite green.
- Template referential integrity + safety-presence pass; safety review clean.
- Setup doc + README pointer present; the CLI defaults resolve for the documented submodule layout.
- Branch merged to `main` on human approval; push only on explicit go-ahead.

## 8. Sources

- D2b-1 spec `2026-06-30-native-codex-agents-md-design.md` (the root `AGENTS.md` shape + gate pattern reused).
- `skills/sync/SKILL.md` (the authoritative gated sequence the template delegates to); `RELEASING.md` (SHA-based distribution model).
