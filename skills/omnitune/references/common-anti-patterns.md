---
name: common-anti-patterns
description: Catalogued prompt smells omnitune Mode A scans for, with before/after examples. Repo-agnostic — examples are illustrative; the smell each catches is what matters.
lastReviewed: 2026-06-14
---

# Common Anti-Patterns — omnitune reference

Each entry: the smell, what current models do with it, and a before/after. Examples are illustrative.

## 1. Hedging in load-bearing instructions
**Model behavior:** treats the instruction as optional even when it isn't; downstream behavior becomes inconsistent.
**Before:** "Try to read the reference before writing."
**After:** "Read the reference before writing. It is the calibration source. Do not skip this step."

## 2. Ambiguous pronouns across sentences
**Model behavior:** binds the pronoun to the nearest noun, which may not be the intended antecedent.
**Before:** "The skill uses the snapshot and the router. It is always loaded first."
**After:** "The skill uses the snapshot and the router. The snapshot is always loaded first."

## 3. Router rows that thematically overlap
**Model behavior:** picks one arbitrarily; output becomes non-deterministic run to run.
**Before:** three rows — "Understanding products", "Understanding buyers", "Understanding funnel" — each pointing at a different file.
**After:** one row — "Product, buyer, and funnel context → see the Context Router section" — with a sub-section that sequences the three.

## 4. Tool declared but never used
**Model behavior:** assumes the tool is required somewhere and wastes reasoning tokens hunting for when to use it. Remove unused tools from the declared list.

## 5. Tool needed but not declared
**Model behavior:** the tool call fails silently; the agent may retry or escape without completing. Detect by scanning prose for tool references and cross-checking the declared list.

## 6. Trigger description doesn't match real phrasing
**Model behavior:** the skill fails to trigger when it should, or fires on unrelated prompts.
**Before:** "description: Handles email workflows."
**After:** "description: Writes conversion-focused emails. Triggers on 'write a nurture email', 'draft email 3 of the cart sequence', 'rewrite this subject line', 'critique this email'."

## 7. Stale cross-references
**Model behavior:** loads whatever it can fuzzy-match, which may be the wrong file. Detect: every `path/to/file.md` reference must resolve from the repo root (confirm with `Glob` at audit time).

## 8. Conflicting guidance between files
**Model behavior:** picks one based on recency in context; behavior depends on which file was read first. Detect: same topic (voice, length, tone) specified in two files with no explicit precedence.
**Fix:** the more specific file wins by default — state it explicitly in both files.

## 9. Imperative and declarative mixed in one paragraph
**Model behavior:** loses track of what's a directive vs context.
**Before:** "The copy skill is used for all marketing copy. You should always read the reference first. It was built in 2026. Run the critique after writing."
**After:** "The copy skill produces marketing copy.\n\n**Directive:** read the reference before writing. Run the critique after writing."

## 10. Success criteria omitted
**Model behavior:** completes when it thinks it's done, which may be earlier than expected.
**Fix:** add an explicit "Definition of done." e.g. "Output is ready when the master file is written per the template AND it passes the QA gate AND the handoff is offered."

## 11. Invented requirements in a rewrite (Mode B)
**Model behavior:** a prompt rewrite silently adds specifics (counts, prices, dates, scope) the user never stated, laundering assumptions into an authoritative-looking result.
**Fix:** the fabrication ledger — every added specific is cited to a config pointer or surfaced as "I assumed X — confirm." (See `prompt-rewrite-protocol.md`.)
