---
name: audit-protocol
description: Scoring rubric for omnitune Mode A (file audit) — dimensions, severity, floor-rule aggregation, report schema. Repo-agnostic; reads the session model's rubric + omnitune.config.
lastReviewed: 2026-06-14
---

# Audit Protocol — omnitune Mode A

Score a target skill/agent file against the **session model's rubric** (`references/rubrics/<provider>/<model>.md` + `references/rubrics/<provider>/_core.md`, selected upstream by the freshness/detection step). Each finding quotes a Core or model-rubric section/rule (e.g. "Core §1.2"). Domain specifics (voice, house rules) come from `omnitune.config` — never hardcoded.

## Documentation router (Mode A)

| Task | Read |
|---|---|
| Scoring a skill | this file → `references/rubrics/<provider>/<session-model>.md` → `references/rubrics/<provider>/_core.md` → `references/common-anti-patterns.md` → `references/skill-md-template.md` → target `SKILL.md` + the files its router points to |
| Scoring an agent | this file → the two rubrics → `references/agent-md-template.md` → target agent file |
| Writing a description finding | `references/description-authoring-guide.md` |

## Dimensions (score each 1–5)

### D1 — Instruction-following hygiene
**Catches:** hedges (`try to`, `consider`, `maybe`, `where possible`), ambiguous pronouns, conflicting guidance between sections, soft phrasing where a directive is needed. (Core §1.) The session model's rubric may mark this **HIGH severity** (e.g. Opus 4.8's literalism).
**5:** directives unambiguous; no hedges except in genuinely optional paths. **3:** noticeable hedging in load-bearing instructions; ≥1 ambiguous reference. **1:** consistently softens instructions or contradicts itself.

### D2 — Structural clarity
**Catches:** missing/incomplete frontmatter, absent or overstuffed router, inconsistent heading hierarchy, broken XML/markdown. (Core §2.) The model rubric may mark this HIGH for small models (e.g. Haiku).
**5:** frontmatter complete; router ≤12 rows and scannable; headings nest cleanly. **3:** frontmatter missing ≥1 field; router >15 rows or rows overlap. **1:** hard to parse at a glance.

### D3 — Context economy
**Catches:** main file >~400 lines with no router, reference-worthy content inlined, duplication that should factor into `references/`. (Core §6.11.)
**5:** main file focused; references factored out. **3:** over-long or missed factoring. **1:** bloated.

### D4 — Tool/permission alignment (agents only)
**Catches:** declared tools the agent never uses, or instructed actions needing undeclared tools.
**5:** tools list matches instructed behavior. **3:** 1–2 unused or 1 missing. **1:** significantly misaligned. **Skills: N/A** (exclude).

### D5 — Trigger-description fidelity
**Catches:** `description:` triggers don't cover the prompts users actually type. (Core §6.1/§6.2.)
**Data source (preference order):** 1) `--sample-prompts <path>`; 2) the target's existing `description:` examples; 3) heuristic — does the description cover the claimed scope?
**5:** triggers cover real invocation phrasing. **3:** misses a common variant. **1:** doesn't match real usage.

### D6 — Internal consistency
**Catches:** router references files that don't exist, duplicate guidance with unclear precedence, rename-fragile cross-refs. (Core §6.) Confirm each `path/to/file.md` resolves (use `Glob`).
**5:** all cross-refs resolve; precedence explicit. **3:** ≥1 broken cross-ref or unclear precedence. **1:** multiple broken refs or contradictory guidance.

### D7 — Register/voice consistency (copy-focused targets only)
**Decoupled.** A target is "copy-focused" only if `omnitune.config` says so — i.e. `house_rules` is set AND the target produces customer-facing copy. Score it against whether it points at and respects the config's `house_rules` / voice source.
**Applies:** copy-focused targets only. If `omnitune.config.house_rules` is empty or the target isn't copy-focused → **N/A** (exclude).

## Severity mapping

| Score | Severity | Action |
|---|---|---|
| 5 | Excellent | No finding |
| 4 | Good | No finding |
| 3 | Medium | Finding + suggested fix |
| 2 | High | Finding + strong recommendation |
| 1 | Critical | Finding + recommend immediate fix |

## Aggregation — floor rule, not mean

The report is driven by **per-dimension findings.** The overall verdict uses a **floor rule:** any dimension scoring **1 caps the verdict at "Critical — do not pass,"** regardless of the others. A safety/correctness finding must never be averaged away. N/A dimensions are excluded entirely. (Do **not** use an arithmetic mean — it can launder a critical.)

## Safety — auditing omnitune's own files

If the target is one of omnitune's own skills/protocols (`sync`, `omnitune`, this file), **do not propose softening a fail-closed safety clause or the never-self-commit invariant**, even where Core §1.3 (calm register) would otherwise flag its emphatic language — those are the §1.3 safety exception. Flag-and-preserve; never soften.

## Report schema

When configured, write to `<omnitune.config.output.reports>/YYYY-MM-DD-<target>.md`; in **standalone mode** (no `omnitune.config.yaml`) present this same report in chat and offer to save it. Either way the schema is:

```markdown
# Tune Report — <target>
**Date:** YYYY-MM-DD · **Target:** <path> · **Model rubric:** <session-model> (synced <date>)
**Verdict:** <Pass | Critical — do not pass> · **Findings below threshold:** N

## Finding 1 — <dimension> (score X/5, severity <level>)
**Location:** <file>:<lineStart>-<lineEnd>
**Issue:** <one paragraph>
**Proposed fix:**
```diff
- <before>
+ <after>
```
**Rationale:** <why this improves the current model's parseability or output quality — cite Core/model-rubric §>
```

## Interactive loop behavior

For each finding (score < 4): show it, show the diff, prompt:
```
[a]pply / [s]kip / [e]dit proposal / [q]uit loop:
```
`a` apply via `Edit` · `s` skip · `e` redraft the proposal · `q` stop (keep applied edits). After the loop, print: `N applied, M skipped, K edited-then-applied. Re-run if structural changes were applied.`
