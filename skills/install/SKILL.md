---
name: install
description: >-
  Guided install for omnitune. Interviews the operator and audits the host
  repo to build an accurate omnitune.config.yaml, adapting question depth to how
  technical the operator is. Never writes config until the operator confirms the
  understanding is correct. Triggers on "/omnitune:install", "set up omnitune",
  "configure the tuner".
---

# install — the install-time auditor loop

Setup is an **interview that audits its own understanding before writing anything.** Do not generate `omnitune.config.yaml` from assumptions; build it from confirmed answers.

## Workflow (run in order)

### 1. Detect + draft
Scan the host repo without writing anything, then **draft the config yourself** — including the technical fields. The operator should validate a draft, not author one from scratch.
- Read `CLAUDE.md` / `AGENTS.md` / `README.md` for domain + conventions.
- List candidate skill roots (`skills/`, `.claude/skills/`) and agent dirs (`.claude/agents/`).
- Sample `SKILL.md` files to infer naming + routing style.
- **Draft `routing[]`** — for each skill, propose the keyword phrases a user would type, inferred from its name + description + first-action section.
- **Draft `context_pointers[]`** — infer which files each skill cites (voice, brand, design docs).
- **Draft** output paths, and note candidate `house_rules` / `reserved_decisions` files.
This adapts to any business: the wizard does the technical authoring by reading the repo; routing tables and pointers are never the operator's to write blind.

### 2. Gauge explanation depth (not field coverage)
Ask one calibration question:
> "So I pitch this right — are you comfortable reading YAML and file paths, or would you rather I explain each piece in plain language?"

This sets **how** you confirm, not **what** gets covered — every operator gets the full drafted config either way.
- **Technical** → show the draft config; confirm in batches; terse.
- **Non-technical** → walk one drafted item at a time in plain language with examples ("I think when someone types 'review this campaign' it should go to your `campaign-review` skill — does that sound right?"). No jargon, no blank fields to fill.

### 3. Confirm the draft
Walk the operator through the drafted fields at the chosen depth. For each: state the inference and the evidence, ask them to confirm or correct.
- **Rule:** every field is pre-filled from the repo; the operator's job is validation. A correction re-drafts that field.
- **Optional escape hatch (offered, never required):** "Want a developer to eyeball the routing table before I save?" — for an operator who'd rather defer the technical bits, not a wall they hit.
- Low-confidence inferences are flagged explicitly ("I wasn't sure about this one") so they get extra scrutiny — never silently shipped.

### 4. Reflect
Restate, in plain language, what you learned about the repo, then show the **draft** `omnitune.config.yaml`:
> "Here's what I understand about your setup — did I get it right? Correct anything that's off."

### 5. Confirm (loop 3–5)
Operator approves or corrects. Re-interview the corrected parts. Repeat until approved.

### 6. Dry-run (validate by doing)
Before writing, prove the config works:
- Run **Mode B** on one sample prompt the operator gives (or a synthetic one) — show the rewrite.
- Run **Mode A** on one of the host's real skills — show the top findings.
- If either misbehaves (wrong routing, missing pointer), fix the draft config and re-confirm.

### 7. Write
Only now write `omnitune.config.yaml` to the repo root. Print:
- "You're set up."
- The three commands (`/omnitune:tune-prompt`, `/omnitune:tune-skill`, `/omnitune:sync`) with a one-line example of each.
- A pointer to `wiki/Configuration.md` for hand-edits.

## Fail-closed invariant

Nothing is written before step 7. The operator is the final reviewer of the context this wizard built — the install must not silently decide domain facts on the operator's behalf. (This mirrors "the agent is not the auditor of its own work.")
