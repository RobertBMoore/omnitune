# Regression corpus

Baselines that `/omnitune:sync` re-scores under the **old vs. new** rubric during its no-drift verify step (see `skills/sync/SKILL.md` step 4). If a rubric change flips an item's verdict, sync surfaces it instead of silently claiming "no drift." The floor is **5 items**; below it, verify fails closed (*"cannot verify — manual review required"*).

**This is omnitune's own dogfood corpus** — chosen to span the Mode B prompt-classes (`command`, `code`, `factual-terse`, `creative-brief`, `adversarial-eval`) plus a Mode A `skill-audit` target and a Mode C `goal-pack` brief, so drift in any class/mode is catchable. Consumer repos accumulate their own corpus (optionally auto-seeded from `output.prompts/` history).

**Fixture format** — each `<slug>.md` carries:
- frontmatter `class:` (one of the seven categories) + `mode:` (`A` = audit, `B` = rewrite, `C` = orchestration pack),
- the raw input (a prompt, a `SKILL.md` snippet for `skill-audit`, or a project brief for `goal-pack`),
- a `**Baseline:**` line — the reference a re-score is compared against.

Nothing parses these at runtime; the frontmatter lets `scripts/test_regression_corpus.py` assert the corpus stays ≥ 5 items and covers every class.
