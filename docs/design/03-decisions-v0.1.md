---
title: Portable Prompt-Tuner — v0.1 Decision Record
date: 2026-06-14
supersedes: design-doc open questions C1–C5
inputs: 5-auditor synthesis + master-auditor adjudication + operator answers (round 2)
status: locked spec for the v0.1 build
---

# v0.1 Decision Record

Locks the architecture after the 5-auditor + master-auditor review and the operator's round-2 answers.

## Decisions locked

| # | Decision | Source |
|---|---|---|
| **D1** | Model-sync default = **badge** (non-blocking end-of-run notice + sticky "N models behind"). The operator's just-in-time interrupt (update/skip/defer/snooze) is preserved verbatim as opt-in `model_sync.channel: interrupt`. | operator |
| **D2** | **Multi-model rubric library.** The plugin keeps tuned rubrics for several models, not just the latest — operators switch models per task. The rubric used on a run is selected by the model the **current session** is running on. | operator (new) |
| **D3** | **Detection = current-session-model match**, NOT a live "latest GA model" scrape. At run start, read the active session's model id; select the matching rubric from the library; a **miss is the sync trigger**. Local, deterministic, zero-network. The bundled manifest supplies the library + model-status metadata. | operator Q3 + endorsed |
| **D4** | **Sync = propose-only** in v0.1. On a model with no tuned rubric, `/omnitune:sync` derives a behavioral diff + targeted questions; a human applies the rubric once. Autonomous self-apply (no-write subagent + loosening-ratchet + corpus floor) is deferred to v0.2. | recommendation per master auditor |
| **D5** | **Adaptive wizard** for both audiences. It drafts the technical fields (routing, context-pointers) by inference from the repo and presents them in plain language to confirm/correct. Developer handoff is an optional escape hatch, not the primary non-technical path. | operator Q4 |
| **D6** | **Retention/deprecation policy.** The manifest tracks each model's status (`ga` / `deprecated` / `retired`) + dates. Keep rubrics for (a) all GA models, (b) any model used within the local retention window. Flag retired-model rubrics for removal but **never auto-delete — operator confirms.** | operator (new) |
| **D7** | **Panel must-fixes that land in v0.1:** injection fence + Anthropic-domain allowlist (A6/B7); Mode B fabrication ledger + prompt-class gate (A3/B1/B2); plugin hygiene — `author` as object, no publisher name in the neutral core (B14-valid); calendar-staleness gate retained alongside model-match (B10). | panel |

## D3 — Detection logic (the core change)

```
on every /omnitune:tune-skill or /omnitune:tune-prompt run:
  current_model = read the active session's model id   # known locally, no network
  rubric = library.lookup(current_model)               # references/rubrics/<model>.md
  if rubric exists:
      use it. (optionally: badge if a newer GA model exists in the manifest)
  else:
      pick the closest-family rubric as a fallback, and
      BADGE: "No tuned rubric for <current_model>; running on <fallback>. Run /omnitune:sync to derive one."
      # never block the run; the fallback rubric still produces useful output
```

- The session model is read from the run context. If it cannot be determined (headless/ambiguous), fall back to `omnitune.config.model_sync.target_model`, else the manifest's newest GA rubric, and badge the assumption.
- A calendar-staleness gate (B10) still applies: if the *selected* rubric's `lastSynced` is older than N days AND the manifest shows its source docs were revised, badge "rubric for <model> may be stale."

## D2/D6 — The rubric library + retention

```
omnitune/skills/omnitune/references/
  models.json                 # manifest: {id, family, status, ga_date, deprecated_date, source_urls}
  rubrics/
    claude-opus-4-8.md        # one tuned rubric per supported model (stable filenames)
    claude-sonnet-4-6.md
    ...
```

- **Selection:** by current-session model id (D3).
- **Retention:** keep rubrics for all `ga` models + any model in the local usage window (`tuner/.model-usage.json`). Mark `retired` rubrics as removable; **prompt the operator** before deleting.
- **Library updates** ship with plugin releases (a release is the freshness signal). `/omnitune:sync` can also derive a rubric on demand for a model the library lacks (propose-only, D4).

## D5 — Adaptive wizard

The wizard does the technical authoring; the operator validates:
1. **Detect + draft.** From repo scan, draft `routing[]` (skill → likely keywords) and `context_pointers[]` automatically.
2. **Gauge** skill level → set explanation depth (not field coverage; every operator gets the drafted fields).
3. **Confirm in plain language.** "I think a prompt like 'review this campaign' should go to your `campaign-review` skill — right?" Operator confirms/corrects per item.
4. **Escape hatch (optional):** "Want a developer to review the routing table before I save?" — offered, never required.
5. **Dry-run + write** as before.

## v0.1 cut list (explicitly deferred)

Autonomous self-apply of the rubric · empirical hold-out output-validation · base+delta differential rubric · retention/house-style learning · ambient `UserPromptSubmit` hook · community-contribution registry infrastructure · QA-subagent machinery · global cross-repo snooze preference.

## v0.1 Definition of Done

Plugin loads (real `commands/` + `references/`); `/omnitune:install` drafts + confirms a working config on a scratch repo; `/omnitune:tune-prompt` and `/omnitune:tune-skill` run against it; Mode B refuses to silently invent constraints (fabrication ledger) and doesn't pad off-class prompts (prompt-class gate); sync is propose-only; detection is session-model match with a non-blocking badge; injection fence in place; 6 wiki pages written; smoke test passes.
