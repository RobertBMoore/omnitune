# Design — Codex Portability Layer (D2)

- **Date:** 2026-06-29
- **Status:** approved design, pre-implementation
- **Parent effort:** "Support tuning OpenAI models + work with Codex." D1 (provider-aware rubric foundation) merged to `main` at `56c6c60`. This is **D2**, the next slice; D3–D5 remain out of scope.

---

## 1. Context & goal

After D1, omnitune resolves OpenAI/`gpt-5.5` model ids and ships an OpenAI rubric — but only when the host harness is **Claude Code / Nimbalyst**, because detection reads the model id from that harness's system-prompt line ("The exact model ID is …") and the skills are written in Claude Code tool names.

**Goal of D2:** make omnitune's skill *content* work when the host harness is **Codex** (or another non-CC agent) — a portability layer, not a native Codex integration. Concretely: harness-aware model detection + a Claude Code→Codex tool-mapping reference + a platform-adaptation note. The user explicitly chose this over shipping a native `AGENTS.md` (deferred).

**Mechanical reality (researched):** Codex CLI does not load Claude Code plugins. Its active model is set in `config.toml` (`model = "gpt-5.5"`) at `~/.codex/config.toml` (global) and `.codex/config.toml` (project, cwd→root precedence, `$CODEX_HOME` override). There is **no `CODEX_MODEL` env var**, and a runtime `--model`/`/model` override is not written back to config.toml. So Codex detection is inherently less authoritative than Claude Code's and must be multi-source + honest about the gap.

## 2. Locked decisions

1. Scope = **portability layer** (detection + tool mapping + platform note), not a native AGENTS.md entry.
2. Detection is **config-file-first** (deterministic), with the assumed model always surfaced in a badge so a runtime override can be corrected.
3. Codex specifics live in a helper script + a reference file, never in skill logic (decoupling contract).

## 3. Scope

**In scope (D2):**
- Harness-aware model-detection precedence in the SKILL/sync prose + `scripts/detect_model.py` (reads Codex `config.toml`).
- `skills/omnitune/references/codex-tools.md` — Claude Code→Codex tool mapping, scoped to omnitune's actual tool use.
- A platform-adaptation note in `skills/omnitune/SKILL.md` (+ brief mirror in the sync SKILL).
- `scripts/test_detect_model.py` + CI registration.

**Out of scope (follow-on):** native `AGENTS.md` Codex entry (D2b); any change to `resolve_model.py` core; auto-sync derivation (D3-adjacent); version log (D4); doc pages (D5).

## 4. Architecture

### 4.A Harness-aware model detection

Replace the single CC/Nimbalyst detection step (in `skills/omnitune/SKILL.md` §2 and `skills/sync/SKILL.md` Detection) with a documented **precedence** the agent follows top-down, stopping at the first hit:

1. **Native system-prompt model id** — Claude Code / Nimbalyst expose it as "The exact model ID is …"; use it verbatim if present.
2. **`python3 scripts/detect_model.py`** — reads the Codex-resolved model from `config.toml` (see 4.B). Use its output if non-empty.
3. **`omnitune.config.model_sync.target_model`** — the operator's configured override.
4. **Newest GA model in the manifest** — and **badge the assumption**.

The resolved id string then flows through the existing `scripts/resolve_model.py` (unchanged) for normalization + provider routing + rubric selection. Whenever detection falls to tier 2–4, the run surfaces the existing non-blocking badge naming the **assumed model**, with a one-line caveat that a runtime `--model`/`/model` override is invisible to config-file detection — so the operator can correct it.

### 4.B `scripts/detect_model.py`

A small, dependency-free helper. Contract: `detect_codex_model(start_dir=None, codex_home=None) -> str | None`.
- Walk from `start_dir` (default cwd) upward to the filesystem root; at each level check `<dir>/.codex/config.toml`; the **closest-to-cwd** file with a top-level `model` key wins (matches Codex's cwd-overrides-root precedence).
- If none found, read the global config: `$CODEX_HOME/config.toml` if `CODEX_HOME` is set, else `~/.codex/config.toml`.
- Parse only the **top-level** `model = "<id>"` (the value before the first `[table]` header), so a `[profiles.*] model = …` does not leak in. Return the id string, or `None` if absent.
- Never raise (a missing/garbage config returns `None`, so the prose falls through to tier 3/4). CLI form prints the id or nothing.

### 4.C `skills/omnitune/references/codex-tools.md`

A Claude Code→Codex tool-mapping reference, scoped to the tools omnitune's skills actually reference (verified by grep): 

| omnitune (Claude Code) | Codex equivalent |
|---|---|
| `Bash` (run `python3 scripts/*`) | native shell |
| `Read` / `Write` / `Edit` (Mode A edit loop) | native file tools |
| `Task` / subagent (sync v0.2 no-write audit subagent) | `spawn_agent` / `wait_agent` / `close_agent` (needs `multi_agent = true`) |
| `TodoWrite` | `update_plan` |
| `WebFetch` (sync doc fetch) | native web/fetch tool, honoring the provider `allowlist_domains` fence |

Plus a "Model detection on Codex" subsection pointing at 4.A/4.B. Credits the superpowers `codex-tools.md` precedent; kept omnitune-specific (only the tools omnitune uses).

### 4.D Platform-adaptation note

One block near the top of `skills/omnitune/SKILL.md`: "This skill uses Claude Code tool names and CC/Nimbalyst model detection. Under a non-CC harness (Codex, Gemini, …), read `references/codex-tools.md` for tool equivalents and the model-detection fallback." A one-line mirror in `skills/sync/SKILL.md` Detection.

## 5. Data flow

```
session start
  → detect model id (precedence 4.A): system-prompt → detect_model.py → config.target_model → newest-GA(+badge)
  → resolve_model.resolve(id, models.json)   (unchanged)
  → load <provider>/_core + <model> rubric → Mode A / Mode B
  → if detection fell back: badge the assumed model + the --model-override caveat
```

## 6. Testing

`scripts/test_detect_model.py` (unittest, dependency-free, registered in `.github/workflows/validate.yml`):
- project `.codex/config.toml` model beats global `~/.codex` (via `codex_home` arg);
- closest-to-cwd project config wins over an ancestor's;
- `$CODEX_HOME` honored for the global file;
- top-level `model` parsed; a `[profiles.x] model=…`-only file → `None`;
- missing/garbage config → `None`, never raises.

## 7. Decoupling & safety

No provider/harness nouns enter skill *logic* — `detect_model.py` and `codex-tools.md` hold the Codex specifics, consistent with the decoupling contract. The WebFetch→Codex mapping reiterates the provider `allowlist_domains` fence so portability cannot weaken it.

## 8. Sources (verified 2026-06-29)

- https://developers.openai.com/codex/config-reference
- https://developers.openai.com/codex/environment-variables
- https://developers.openai.com/codex/config-basic
- superpowers `using-superpowers/references/codex-tools.md` (tool-mapping precedent)
