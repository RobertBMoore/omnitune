# Restore the dropped `omnitune` core skill — Design

**Date:** 2026-06-28
**Status:** Implemented + dogfooded (A+B+C) on branch `restore-omnitune-core-skill`
**Author:** Restoration session (post `prompt-tuner` → `omnitune` rename)

## Problem

The `prompt-tuner` → `omnitune` rename shipped an incomplete plugin. The
repo (`RobertBMoore/omnitune`, single squashed commit `7fb3465`) carried over
only `skills/install`, `skills/sync`, and four commands. The **core skill was
never committed.**

Both `commands/tune-prompt.md` and `commands/tune-skill.md` delegate to files
that do not exist anywhere in the repo or the installed plugin:

| Command | Delegates to | Status |
|---|---|---|
| `tune-prompt` | the `omnitune` skill (Mode B) · `skills/omnitune/prompt-rewrite-protocol.md` · `references/rubrics/<model>.md` | **all missing** |
| `tune-skill` | `skills/omnitune/audit-protocol.md` | **missing** |

There is no `omnitune:omnitune` core skill registered (only `install`/`sync`).
A live dogfood of `omnitune:tune-prompt` confirmed the failure: it loads
`omnitune.config.yaml` (step 1, OK) then dead-ends with no protocol or rubric
to follow.

## Goal

Make `omnitune:tune-prompt` and `omnitune:tune-skill` work **and make the whole
lifecycle (install → use → update) a breeze, robust inside Nimbalyst.** Approved
scope is **A + B + C**:

- **A — Restore** the core skill as a **faithful port** of the known-good
  upstream files with **mechanical renaming only** (no logic/content change to
  rubrics or protocols). Re-tuning content is deferred to `/omnitune:sync`.
- **B — Zero-config standalone mode** so first value takes one command, not an
  install interview first.
- **C — Model-id normalization** so Nimbalyst's `claude-opus-4-8[1m]` and dated
  snapshots match the right rubric instead of falsely falling back.

A and B/C are separable: A is a pure content port; B and C touch only the
config-gating and id-matching *glue*, never the ported rubric/protocol logic.

## B — Zero-config standalone mode

Today the core skill hard-stops when `omnitune.config.yaml` is absent ("run
`/omnitune:install` first"), so a user cannot rewrite a single prompt without
first completing the repo-audit interview. But Mode B already degrades
gracefully on every config input *except* that hard-stop and the save path
(`routing`/`context_pointers`/`house_rules`/`reserved_decisions` are all
optional; the schema already states "routing may be empty… still valid").

Changes (glue only — the QA loop, fabrication ledger, prompt-class gate, and
rubric logic are untouched):

- `skills/omnitune/SKILL.md` §"Before anything" step 1: replace the hard-stop
  with a branch — **config present** → load it (routing, pointers, house_rules,
  output paths). **Config absent** → run in **standalone mode**: rubric-only, no
  routing/pointers, every added specific laddered in the Assumptions block,
  result presented in chat. Never block; mention `/omnitune:install` once as the
  way to unlock repo-aware routing.
- `skills/omnitune/SKILL.md` Mode-selection table: the "no config present" row
  becomes "run standalone (still works); note `/omnitune:install` adds routing",
  not "tell the user to run install".
- `prompt-rewrite-protocol.md` "File output": save to `<output.prompts>/` only
  when configured; in standalone mode skip the mandatory write and present in
  chat, offering to save on request. The `Saved to:` line becomes conditional.
- `audit-protocol.md` / Mode A: audit an **explicit file path** even without
  config; only routing-name resolution needs config. No config + no explicit
  path → suggest `/omnitune:install` for repo-aware mode (still non-blocking).
- `commands/tune-prompt.md` and `commands/tune-skill.md`: soften the
  "if config does not exist, stop and tell me to run `/omnitune:install`" line
  to "proceed in standalone mode; mention `/omnitune:install` unlocks
  repo-aware routing." Load config when present.

## C — Model-id normalization (Nimbalyst + dated snapshots)

Detection matches the raw session model id against `models.json`. Nimbalyst
reports `claude-opus-4-8[1m]` (context-window suffix) and some models report
`claude-haiku-4-5-20251001` (date snapshot); neither exact-matches the rubric
id, so detection falls through to "closest-family" and shows a **false** "no
tuned rubric — running on fallback" badge even though the correct rubric exists.

Change — add one normalization rule to detection in BOTH
`skills/sync/SKILL.md` (Detection step 1) and `skills/omnitune/SKILL.md`
(rubric-selection step): before matching, **normalize** the session model id —
lowercase, strip any bracketed suffix (`[1m]`, `[…]`) and any trailing
`-YYYYMMDD` date snapshot — then match the normalized id against `models.json`.
Examples: `claude-opus-4-8[1m]` → `claude-opus-4-8`;
`claude-haiku-4-5-20251001` → `claude-haiku-4-5`. Only fall back to family (with
the badge) when the *normalized* id still misses. Document that in Nimbalyst the
id is read from the session system prompt ("The exact model ID is …").

## Source of truth

`DRG-Prompt-Tuner@release` — commit `c291584101950bfc5034bdfc1b757b3f4a7aabea`,
the exact commit the old `prompt-tuner@drg-tools` plugin shipped from. Private
repo, reachable via `gh`/`git`. Cloned to `/tmp/dpt-src` for the port.

The dropped directory there is `skills/prompt-tuner/`; it lands in the omnitune
repo as `skills/omnitune/`.

## What gets added

New directory `skills/omnitune/` — 13 files, copied verbatim **except** the
string renames in the next section:

```
skills/omnitune/
  SKILL.md                              # Mode A/B dispatcher (name: omnitune)
  prompt-rewrite-protocol.md            # Mode B (tune-prompt)
  audit-protocol.md                     # Mode A (tune-skill)
  references/
    models.json                         # model -> rubric manifest
    common-anti-patterns.md
    skill-md-template.md
    agent-md-template.md
    description-authoring-guide.md
    rubrics/
      _core.md                          # model-invariant rules
      claude-opus-4-8.md                # THIS session's model
      claude-sonnet-4-6.md
      claude-haiku-4-5.md
      claude-fable-5.md
```

## Mechanical renames (the only edits to ported content)

~28 occurrences of the four primary tokens (`prompt-tuner` ×16,
`tuner.config.yaml` ×4, `tuner-sync` ×6, `tuner-install` ×2), plus the
`/tune-skill`/`/tune-prompt` trigger strings and `tuner.config.schema.md`. The
exact replacement set is resolved by an exhaustive grep at implementation time,
not hand-counted. Meaning is preserved; only identifiers change so the skill
resolves under the omnitune namespace and the already-shipped sibling files
(`skills/install`, `skills/sync`, `omnitune.config.yaml`,
`omnitune.config.schema.md`, namespaced commands).

| Old token | New token | Rationale |
|---|---|---|
| `name: prompt-tuner` (SKILL.md frontmatter) | `name: omnitune` | Registers as `omnitune:omnitune`; commands say "Use the `omnitune` skill" |
| `tuner.config.yaml` | `omnitune.config.yaml` | Config already exists under the new name |
| `tuner.config.schema.md` | `omnitune.config.schema.md` | Schema already renamed in the repo |
| `/tuner-install` | `/omnitune:install` | Install skill is now `install` |
| `/tuner-sync` | `/omnitune:sync` | Sync skill is now `sync` |
| `tuner-sync` (bare, e.g. self-audit list) | `sync` | Sibling skill dir renamed |
| `../tuner-sync/SKILL.md` | `../sync/SKILL.md` | Relative path to the renamed sync skill |
| `/tune-skill`, `/tune-prompt` (trigger strings) | `/omnitune:tune-skill`, `/omnitune:tune-prompt` | Namespaced command form |
| `prompt-tuner` (headings, prose, self-audit list) | `omnitune` | Branding |

Known occurrence sites (from upstream `release`, paths relative to
`skills/prompt-tuner/` → become `skills/omnitune/`):

- `SKILL.md`: lines 2, 6, 12, 16, 20, 21, 36, 37, 38, 39, 57
- `audit-protocol.md`: lines 3, 7, 64, 66
- `prompt-rewrite-protocol.md`: lines 3, 7
- `references/agent-md-template.md`: line 3
- `references/common-anti-patterns.md`: lines 3, 7
- `references/description-authoring-guide.md`: lines 3, 30
- `references/models.json`: lines 4, 6, 95
- `references/rubrics/_core.md`: line 3

Note the `audit-protocol.md` self-audit safety clause (line 66) lists the
plugin's own skills as `tuner-sync, prompt-tuner, this file` → must become
`sync, omnitune, this file`. The fail-closed/never-self-commit invariants in that
clause must be preserved verbatim (do not soften), per the skill's own rule.

`lastReviewed:` date stamps and all rubric/protocol logic are copied unchanged.

## Config-key compatibility

The ported protocols reference config keys (`house_rules`, `reserved_decisions`,
`<output.reports>`, `<output.prompts>`, `skills.root`, `model_sync.channel`).
These match the keys already present in the repo's `omnitune.config.yaml` and
`omnitune.config.schema.md` (the shipped commands already reference the same
keys). Implementation must spot-check that every config key the ported protocols
read exists in the current schema; flag any mismatch rather than silently
adapting.

## Out of scope

- `skills/install`, `skills/sync`, `commands/*` — already correctly renamed.
- The cosmetic `regression_corpus: "tuner/regression/"` default in
  `omnitune.config.yaml` / `.example.yaml` / docs — a user-config path string,
  not a code reference. Left as-is unless explicitly requested.
- Any content/behavior re-tuning of rubrics or protocols.
- `scripts/` (`tuner_check.py` etc.) — CI tooling, not runtime; not touched by
  this restore.

## Verification — the re-dogfood

1. **Static:** `grep -rIE "prompt-tuner|tuner\.config|tuner-sync|tuner-install"
   skills/omnitune` returns only intended renamed forms (zero old tokens).
   Confirm all 13 files present. `python3 scripts/validate_plugin.py` passes and
   the existing `pytest` suite stays green (scripts are unaffected by the port).
2. **Reinstall:** rebuild/reinstall the plugin from the updated repo so the
   installed cache carries `skills/omnitune/`.
3. **Live zero-config `tune-prompt`** (this Nimbalyst session, model
   `claude-opus-4-8[1m]`): with the repo's own `omnitune.config.yaml` and also a
   simulated no-config case → C normalizes the id to `claude-opus-4-8` (no false
   fallback badge), B presents the rewrite in chat with QA verdict + fabrication
   ledger + prompt-class gate.
4. **Live `tune-skill`:** run against a real skill file (e.g.
   `skills/install/SKILL.md`) → must produce the Mode A severity-ranked report.
5. **Regression guard:** confirm that *with* a config present, behavior is
   unchanged (config still loaded, routing/pointers/output paths honored).
6. **Commit** the restored core skill, the B/C glue edits, and this spec once
   both modes pass.

## Risks

- **Skill-name collision/ergonomics:** core skill `name: omnitune` surfaces as
  `omnitune:omnitune`. This mirrors the old `prompt-tuner:prompt-tuner` pattern
  and is what the commands expect ("Use the `omnitune` skill"). Low risk.
- **Stale upstream content:** the ported rubrics reflect 2026-06-27 review state.
  Acceptable — `/omnitune:sync` is the designed path to refresh them; the dogfood
  only needs them to load and apply.
