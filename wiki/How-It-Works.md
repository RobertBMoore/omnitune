# How It Works

omnitune has two user-facing modes and two operational commands, all reading one config file and a per-model rubric.

## The rubric library
The plugin ships a library of rubrics, organized per provider, under `skills/omnitune/references/rubrics/<provider>/`:
- `<provider>/_core.md` — that provider's model-invariant prompt-engineering rules (e.g. `anthropic/_core.md`, `openai/_core.md`).
- `<provider>/<model>.md` — each model's specific calibration (effort defaults, literalness, structure needs), layered on its provider `_core`.
- `models.json` — the manifest: which models exist, their status (`ga`/`deprecated`/`retired`), and which rubric file each maps to.

At the start of every run, the plugin reads **the model your session is running**, matches it in `models.json`, and loads that rubric. No network call, no "latest model" guess — it tunes for the model actually in use. (See [Auto-Sync](Auto-Sync.md).)

## Mode A — `/omnitune:tune-skill <name>`
Audits a `SKILL.md` or agent file against the session model's rubric across these dimensions: instruction hygiene, structural clarity, context economy, tool/permission alignment (agents), trigger-description fidelity, internal consistency, and register/voice (copy-focused targets only). Each finding cites a rubric section.

Aggregation uses a **floor rule, not an average**: any dimension scoring 1 (Critical) caps the verdict at "do not pass" — a safety/correctness finding can never be averaged away. It writes a report to your configured `output.reports/` and offers an interactive `[a]pply / [s]kip / [e]dit / [q]uit` loop per finding.

## Mode B — `/omnitune:tune-prompt "<text>"`
Rewrites an ad-hoc prompt into model-optimized form. Two safety mechanisms make it trustworthy:

1. **Prompt-class gate (first step).** It classifies the prompt — `creative-brief`, `code`, `factual-terse`, `adversarial-eval`, `command`, or `other` — and only applies the brief-shaped QA dimensions (context completeness, constraint specificity, success criteria) to the classes that need them. A terse or code prompt is **never** padded with requirements it doesn't want.
2. **Fabrication ledger.** Every specific the rewrite adds that wasn't in your prompt (a count, price, date, scope) must be either *cited* to a config context-pointer or *laddered* as an explicit "I assumed X — confirm." It cannot silently invent requirements and still pass.

The draft is self-scored against the rubric in a QA loop (max 3 drafts) before you ever see it, then saved to `output.prompts/` and offered as `[r]un / [c]opy / [e]dit / [a]bandon`.

## The two operational commands
- **`/omnitune:install`** — the adaptive install wizard ([Install-Setup](Install-Setup.md)).
- **`/omnitune:sync`** — derives a rubric when your session runs a model the library doesn't cover yet, propose-only ([Auto-Sync](Auto-Sync.md)).

## The decoupling contract
The plugin core names no company, campaign, or domain file. Everything repo-specific lives in `omnitune.config.yaml` ([Configuration](Configuration.md)). That's what lets the same plugin tune an email shop, an outdoor-gear store, or a codebase with no changes to the core.
