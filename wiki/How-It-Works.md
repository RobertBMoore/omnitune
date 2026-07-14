# How It Works

omnitune has three user-facing tune modes and two operational commands. All three modes select the rubric for the session model; config is optional enrichment, not a prerequisite.

## The rubric library
The plugin ships a library of rubrics, organized per provider, under `skills/omnitune/references/rubrics/<provider>/`:
- `<provider>/_core.md` — that provider's model-invariant prompt-engineering rules (e.g. `anthropic/_core.md`, `openai/_core.md`).
- `<provider>/<model>.md` — each model's specific calibration (effort defaults, literalness, structure needs), layered on its provider `_core`.
- `models.json` — the manifest: which models exist, their status (`ga`/`deprecated`/`retired`), and which rubric file each maps to.

At the start of every run, the plugin reads **the model your session is running**, matches it in `models.json`, and loads that rubric. No network call, no "latest model" guess — it tunes for the model actually in use. (See [Auto-Sync](Auto-Sync.md).)

## Providers, Codex & lineage
The library is **provider-aware** — Anthropic (Claude) and OpenAI (GPT-5 / Codex) rubrics, resolved by one tested resolver (`scripts/resolve_model.py`) that handles normalization, provider routing, and fallback. Under OpenAI's **Codex** harness (which has no Claude Code system prompt) the model is detected from `.codex/config.toml` via `scripts/detect_model.py`, and a repo-root **`AGENTS.md`** — which Codex auto-loads — carries the Claude-Code→Codex tool mappings, the detection precedence, and the safety invariants. To run omnitune under Codex in your **own** repo, add it as a git submodule and inject the managed `AGENTS.md` block (see `docs/codex-consumer-setup.md`). When the plugin derives a rubric, an **iterated independent-audit gate** (no-write reviewers run to mechanical convergence) plus the tighten-only ratchet gate it before any human commit, and every applied rubric is recorded in an append-only **version log** (`references/version-log.json`) — shown on the **Models** page, so the docs can't drift from the library.

## Mode A — `/omnitune:tune-skill <name>`
Audits a `SKILL.md` or agent file against the session model's rubric across these dimensions: instruction hygiene, structural clarity, context economy, tool/permission alignment (agents), trigger-description fidelity, internal consistency, and register/voice (copy-focused targets only). Each finding cites a rubric section.

Aggregation uses a **floor rule, not an average**: any dimension scoring 1 (Critical) caps the verdict at "do not pass" — a safety/correctness finding can never be averaged away. It writes a report to your configured `output.reports/` and offers an interactive `[a]pply / [s]kip / [e]dit / [q]uit` loop per finding.

## Mode B — `/omnitune:tune-prompt "<text>"`
Rewrites an ad-hoc prompt into model-tuned form. Two safety mechanisms make it trustworthy:

1. **Prompt-class gate (first step).** It classifies the prompt — `creative-brief`, `code`, `factual-terse`, `adversarial-eval`, `command`, or `other` — and only applies the brief-shaped QA dimensions (context completeness, constraint specificity, success criteria) to the classes that need them. A terse or code prompt is **never** padded with requirements it doesn't want.
2. **Fabrication ledger.** Every specific the rewrite adds that wasn't in your prompt (a count, price, date, scope) must be either *cited* to a config context-pointer or *laddered* as an explicit "I assumed X — confirm." It cannot silently invent requirements and still pass.

The draft is self-scored against the rubric in a QA loop (max 3 drafts) before you ever see it, then saved to `output.prompts/` and offered as `[r]un / [c]opy / [e]dit / [a]bandon`.

## Mode C — `/omnitune:tune-goal "<brief>"`
Turns a persistent objective into an operating system for the build. Instead of trusting one enormous chat to remember everything, Mode C moves state into files, judgment into the orchestrator, bounded work into named agents, and evidence into gates.

It first asks numbered questions for any missing launch fact: deploy targets, gate commands and required environments, checkpoint ownership/channel, quiet hours, milestone shape, and target directory. It never silently fills those gaps. Every project-specific detail in the result must be cited to the brief/config or listed as an assumption.

A complete pack contains seven components: a goal prompt, a short auto-loaded constitution, builder and read-only auditor definitions, resumable state-file contracts, a guardrails digest, an operator pre-flight checklist, and runnable record/liveness scripts. Model-specific delegation, effort, and verbosity come from the active rubric; project facts come from the brief or config.

Before handoff, Mode C checks all required components, the fabrication ledger, contract traceability, line caps, and Python/Bash gate syntax. An unresolved check is never treated as ready. The pack does not execute the project or approve launch; it makes the operating contract explicit and reviewable, with scriptable invariants gated. See [Tune-Goal](Tune-Goal.md) for best-use guidance and a full example.

## The two operational commands
- **`/omnitune:install`** — the adaptive install wizard ([Install-Setup](Install-Setup.md)).
- **`/omnitune:sync`** — derives a rubric when your session runs a model the library does not cover; unavailable or failed safety gates fall back to propose-only, and a human always makes the final commit ([Auto-Sync](Auto-Sync.md)).

## The decoupling contract
The plugin core names no company, campaign, or domain file. Everything repo-specific comes from the user's prompt/brief or `omnitune.config.yaml` ([Configuration](Configuration.md)). That's what lets the same plugin tune an email shop, an outdoor-gear store, or a codebase with no changes to the core.
