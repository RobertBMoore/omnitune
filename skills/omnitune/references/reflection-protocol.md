---
name: reflection-protocol
description: >-
  Knowledge source for the reflection clause omnitune Mode C packs emit — the
  local-Dream contract: a scheduled fresh-context session that curates a lesson
  store (adopt-or-discard) and files an append-only orchestration-drift audit.
  Provider-shared and model-agnostic: it composes with orchestration-pack.md
  (whose reflection clause points here) and the session model's rubric, which
  supplies the in-session session-close reflection this contract curates.
lastReviewed: 2026-07-13
---

# Reflection protocol — the local Dream (omnitune Mode C)

## What it is

The reflection clause of an orchestration pack, expanded. Every pack Mode C
emits carries a one-paragraph reflection clause (see `orchestration-pack.md` →
*Reflection clause*); this file is the full contract that clause points at.

It is modeled on the managed-agent **Dreams** pattern: not a per-turn step but a
periodic, offline, fresh-context pass that curates what the run has accumulated.
It is the **curation half** of the memory pattern and does not stand alone:

- **Session-close reflection** (in-session, from the session model's rubric)
  appends raw lessons to the lesson store as a run ends — cheap, immediate, lossy.
- **The local Dream** (this contract) periodically reads that accumulation with
  fresh context and curates it — merges, replaces, corrects, promotes.

Neither substitutes for the other: without session-close append there is nothing
to curate; without the Dream the store only grows and rots.

## The standing verdict — external checking is a cadence, not a resident

The orchestrator cannot be its own auditor, but the answer is not a standing
co-operator agent that doubles cost and drifts alongside it. External checking is
three scheduled legs, each catching a different decay, and **no resident agent is
added**:

- **Deterministic gates** (`record_check`, G1/G2) catch **bookkeeping decay** —
  every merge and tag.
- **Scheduled fresh-context reflection** (this contract) catches **judgment
  drift** — on the cadence below.
- **The dumb staleness watchdog** (`staleness_watchdog.sh`, G4) catches
  **orchestrator death** — something the orchestrator need not be alive to run.

## Cadence

Coarser than per-turn. **Default: milestone close or 24 hours, whichever comes
first** (the value the pack's reflection clause carries; see
`orchestration-pack.md`). A pack may set a different cadence from the brief, but
never per-turn — reflection is a synthesis pass, not a running commentary.

## Contract

Each point is one binding rule a pack's reflection clause inherits. `R1`..`R7`
are the contract; `scripts/test_orchestration_reference.py` parses the table
below and fails if any point is missing or demoted to prose.

| ID | Reflection-contract point |
|---|---|
| R1 | **Bounded input.** A run reads only the transcripts since the last reflection, plus the state files, evidence tails, and git metadata, under an explicit size cap. If the window exceeds the cap, the run narrows scope and says so in its output — it never reads everything. (A prior unbounded audit exhausted its context budget.) |
| R2 | **Steering, not editing.** Each run accepts a short steering instruction (focus areas, content to preserve, output conventions) and is a synthesis pass over its inputs, never an editor: a targeted single-entry fix is made by editing the output artifact directly, never by instructing the reflection to make it. |
| R3 | **Read-only inputs; curation rules.** Inputs are never modified. Lesson-store curation merges duplicates, replaces stale or contradicted entries with the latest value, and records each correction with why. |
| R4 | **Two artifacts, two disposal semantics.** A run produces a **curated lesson store** (adopt-or-discard) and an **orchestration-drift audit** filed append-only under `audits/` with severities every run — the audit is never discardable, whether or not the operator acts on it. |
| R5 | **Adoption is explicit, never default.** The live lesson store changes only by a recorded swap step — a LOG entry citing the reflection artifact; until then the orchestrator keeps reading the prior store. A failed or interrupted run keeps its partial output, labels it partial, never adopts it, and reports the failure in the next status artifact — a failed reflection is information. |
| R6 | **Output is pushed, not parked.** The drift-audit summary and a lesson-store diff attach to the next status artifact as a numbered adopt/discard ask, so the operator sees them without going to look. |
| R7 | **Promotion queue.** Each output ends with a promotion queue: lessons proposed for the constitution or an agent definition, each applied by the orchestrator or declined with a reason before the next milestone closes — memory is not policy until promoted (mirrors `orchestration-pack.md` B10). |

## Decoupling

This file and every reflection clause Mode C emits are project-agnostic: no
client, company, campaign, or product names; the field evidence is referred to
only generically. Everything project-specific (cadence overrides, the lesson-store
and audit paths, the status channel) enters a pack only from the user's brief or
`omnitune.config.yaml` — never from this file.
