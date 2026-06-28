---
name: prompt-rewrite-protocol
description: omnitune Mode B — rewrite an ad-hoc prompt into optimized form for the session model, gated by a prompt-class classifier and a fabrication ledger, self-scored in a QA loop before presenting. Repo-agnostic; routing + pointers from omnitune.config.
lastReviewed: 2026-06-14
---

# Prompt Rewrite Protocol — omnitune Mode B

Return a rewritten, model-optimized version of the user's raw prompt plus a short explanation of what changed — but only after it passes the QA loop. The rubric is the **session model's** rubric (`references/rubrics/<model>.md` + `_core.md`, selected upstream). Domain routing/pointers come from `omnitune.config`.

## Step 0 — Prompt-class gate (run FIRST)

Classify the raw prompt before touching it:

| Class | Looks like |
|---|---|
| `creative-brief` | long-form generative work (copy, docs, designs, plans) |
| `code` | write / edit / debug code |
| `factual-terse` | a short factual ask, or a deliberately minimal instruction |
| `adversarial-eval` | a test / probe / eval prompt where the exact wording is the point |
| `command` | a one-line directive / automation |
| `other` | meta-tasks, mixed |

**The class controls which QA dimensions apply** (see the QA rubric). A legitimately terse, code, or eval prompt is **never** padded with brief-shaped requirements (scope statements, success criteria, "go above and beyond"). When the class is unclear, ask one classifying question rather than assume — guessing wrong here is how the tool makes a good prompt worse.

## Analysis checklist (run in order)

### 1. Detect target (config-driven)
Match the raw prompt against `omnitune.config.routing[]` keywords. If a target skill is detected, load its `SKILL.md` frontmatter + the top of its first-action/router section; the rewrite then adds accurate pointers from `omnitune.config.context_pointers[]`. No target detected → proceed without target-specific context (valid for meta/general prompts).

### 2. Missing context pointers (config-driven)
For a detected target, check whether the prompt names the nouns the target needs, using `omnitune.config.context_pointers[]`, `house_rules`, `reserved_decisions`. Add accurate pointers. **Never invent a pointer to a file you have not confirmed exists.**

### 3. Constraint specificity
Name length/cadence, register/format, deliverable shape, and concrete specifics — **subject to the fabrication ledger below.** Any specific you add that the user didn't supply must be cited or laddered, never silently asserted.

### 4. Success criteria
Add a checkable "done" statement if absent (for classes where it applies — see QA rubric).

### 5. Hedge + reserved-decision scan
Convert hedges on load-bearing steps to imperatives. Where the rewrite touches a `omnitune.config.reserved_decisions` item or a `house_rules` anti-pattern, add a one-line caveat to **surface (not pre-empt)** it.

## The fabrication ledger (non-negotiable)

Every constraint the rewrite **adds that was not in the user's raw prompt** must be one of:
- **(a) cited** — to a `omnitune.config.context_pointer` or a verifiable repo fact, or
- **(b) laddered** — listed in an **Assumptions** block: *"I assumed: <X> — confirm or correct."*

A specific (count, price, date, scope, cadence) that is neither cited nor laddered is a **fabrication**. Do not bake it into the rewrite as if the user stated it. Inventing requirements is the primary way a rewrite produces a confidently-worse prompt — the QA loop fails any draft that does it (dimension 9).

## Review/QA loop

After producing a draft from Step 0 + §1–5, **do not present it.** Self-score it against the session model's rubric (read it, or hold it in context). This is the docs-endorsed self-correction pattern: draft → review against criteria → refine.

### QA rubric (score each 1–5; applicability by class)

| # | Dimension | Applies to |
|---|---|---|
| 1 | Scope explicitness | all |
| 2 | Positive framing | all |
| 3 | Calm directive register | all |
| 4 | No hedges on load-bearing steps | all |
| 5 | Context completeness | creative-brief, code (N/A for factual-terse / command / adversarial-eval unless context is genuinely needed) |
| 6 | Constraint specificity | creative-brief, code (N/A for factual-terse / command / adversarial-eval) |
| 7 | Success criteria | creative-brief, code, command (N/A for factual-terse / adversarial-eval) |
| 8 | Structure (XML/numbered where it helps; long data above the ask) | all where the target benefits |
| 9 | **Fidelity (fabrication check)** | **all** — every added constraint is cited or laddered; no invented requirements |

### Pass bar, cap, loop
- **Pass:** every **applicable** dimension ≥ 4, none at 1–2, **and dimension 9 ≥ 4** (a fabrication is an automatic fail regardless of the rest). N/A is recorded, not counted.
- **Cap:** at most 2 redrafts (3 drafts total). Re-score only what changed + anything it could have regressed.
- **On cap without pass:** present the best draft, mark the verdict **CONDITIONAL**, name each still-failing dimension with one line. Never silently ship a sub-bar rewrite.

### Verdict block (surface above the choice loop)
```
QA verdict: PASS (draft 2 of max 3) · class: code
  1 Scope 5 · 2 Positive 5 · 3 Register 5 · 4 Hedges 5
  5 Context N/A · 6 Constraints N/A · 7 Success 4 · 8 Structure 5 · 9 Fidelity 5
```

### Escape hatch (class-aware)
If the raw prompt is already well-formed **for its class** (e.g. a terse prompt that is appropriately terse, with every *applicable* dimension ≥ 4), do not rewrite. Return: *"Already well-formed for its class (<class>). No rewrite needed,"* and list target / context / constraints / success criteria as present. This is a signal, not a failure.

## Output format (after the QA loop passes)
```
Improved prompt:
<full rewritten prompt, ready to run>

QA verdict: <PASS | CONDITIONAL> (draft N of max 3) · class: <class>
<one-line dimension scores>

Assumptions (if any — from the fabrication ledger):
- <added specific> — confirm or correct

Why I changed it:
- <short line per change>

Saved to: <output.prompts>/<YYYY-MM-DD>-<slug>.md   (omit this line in standalone mode)
```

## File output (when configured)
**With config:** write the rewrite to `<omnitune.config.output.prompts>/<YYYY-MM-DD>-<slug>.md`. Create the dir if missing; never overwrite — append `-v2` etc. The file body is the prompt only (no verdict, no rationale). Show the path under `Saved to:`.

**Standalone (no `omnitune.config.yaml`):** do **not** write a file. Present the improved prompt in chat and offer to save it (the user names a path, or `/omnitune:install` sets `output.prompts`). Omit the `Saved to:` line.

## User-choice prompt
```
[r]un it / [c]opy it / [e]dit further / [a]bandon:
```
`r` submit as a new turn · `c` fenced code block · `e` ask what to change, redraft, re-run QA · `a` exit.

## Feedback loop
If the same rewrite pattern recurs (e.g. always adding the same pointer for one skill), propose upgrading that target's `SKILL.md` so it handles the vague form natively. If the QA loop keeps failing the same dimension across unrelated prompts, propose tightening the rule in `_core.md` or this protocol.
