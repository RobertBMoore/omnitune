---
name: portable-skill-tuner-package
description: Extract the skill-tuner system (/omnitune:tune-skill + /omnitune:tune-prompt) into a repo-agnostic, drop-in package with a wiki and a self-updating model-sync mechanism
created: 2026-06-14
source_mode: skill-tuner Mode B (prompt rewrite)
target_skill: none (meta-task: skill-tuner extraction/packaging)
---

# Prompt — Package the skill-tuner system for any repo

Design, build, and document a portable, repo-agnostic version of this repo's `skill-tuner` system — the `/omnitune:tune-skill` file-auditor (Mode A) and the `/omnitune:tune-prompt` prompt-rewriter (Mode B) — so it can be dropped into any repository or business with only a small config file to customize, and so it keeps its model best-practices rubric current as Anthropic ships new models.

Begin with `superpowers:brainstorming`, then write a plan with `superpowers:writing-plans`, and only then build. Do not jump straight to implementation; this is a multi-deliverable build and the approach decision in step 1 is load-bearing.

**Source to extract (read these in full first):**

- `.claude/skills/skill-tuner/SKILL.md` — two-mode entry point, mode-selection table, Mode A/B routers, freshness contract, flags
- `.claude/skills/skill-tuner/audit-protocol.md` — Mode A 7-dimension rubric and interactive loop
- `.claude/skills/skill-tuner/prompt-rewrite-protocol.md` — Mode B rewrite checklist, QA loop, output/file contract
- `.claude/skills/skill-tuner/references/opus-4-8-best-practices.md` — the model best-practices snapshot (carries `model:`, `sources[]`, `lastSynced`, `refreshCommand` frontmatter — this is the file the auto-sync keeps current)
- `.claude/skills/skill-tuner/references/common-anti-patterns.md`, `skill-md-template.md`, `agent-md-template.md`, `description-authoring-guide.md`
- `.claude/commands/omnitune:tune-skill.md`, `.claude/commands/omnitune:tune-prompt.md` — the two slash-command definitions

**1. Architecture decision (decide it, write it down).** Choose and justify the package format in the plan. Default: a self-contained Claude Code plugin (`plugin.json` + `skills/skill-tuner/` + `commands/` + `wiki/`) living in one new top-level folder, so an installing repo adds it without rewriting its own `.claude/`. State the one alternative you considered (e.g. a bare copy-in `skills/` folder with no plugin manifest) and why you rejected it.

**2. Decouple from the originating client.** The current skill hardcodes client specifics: the 7 client domain-skill list and prose-routing in `SKILL.md`, the client keyword→skill table in `prompt-rewrite-protocol.md` §1, client campaign/brand/anti-pattern/reserved-decision pointers throughout, and client-specific output paths (`reports/`, `docs/prompts/`). Replace every client-specific binding with a single host-config file the installing repo fills in — declaring at minimum: the host's skill root path, the host's domain keyword→skill map, the host's house anti-patterns / reserved-decisions file (optional), and the report/prompt output directories. The core package must contain zero client-specific strings; ship the client's current values as one *example* config, not as defaults baked into the logic.

**3. Wiki.** Produce a `wiki/` of markdown covering: Home/overview; How-It-Works (Mode A audit flow, Mode B rewrite + QA loop, the 7-dimension rubric, the freshness contract); Install/Setup (both the plugin-install path and the copy-in path); Configuration (every host-config field with a worked example); Auto-Sync (how the model-refresh detects and applies a new model); and FAQ/troubleshooting.

**4. Auto-model-sync.** Build the mechanism that keeps the best-practices snapshot current. It must: check Anthropic's published model list/changelog; compare the latest model id against the snapshot's `model:` frontmatter; and, when a newer model exists, run the existing `--refresh` path — re-fetch every URL in `sources[]`, re-derive the rules against the live docs, rename `opus-4-8-best-practices.md` to the new model slug (e.g. `opus-4-9-best-practices.md`), update every pointer to it across the package, and stamp `lastSynced`/`lastReviewed` to the run date. Deliver it as **detect-and-propose, not silent self-commit**: the check opens a PR (or posts an announcement) for a human to approve before the package rewrites its own rubric. Provide both an on-demand command and a scheduled (cron / `/schedule`) entry, and demonstrate a dry-run that correctly detects the current model with no false positive.

**Done when:** a single new top-level package folder exists containing the full skill + both commands + the `wiki/` + the auto-sync routine; the core is grep-clean of client-specific strings; it ships an example host-config and a one-page quickstart; and it passes a smoke test — copied into a scratch repo and pointed at that repo's own config, `/omnitune:tune-prompt` returns a rewritten prompt and `/omnitune:tune-skill` produces an audit report against that repo's files.

**Caveat (surface, do not pre-empt):** an "auto-patch itself" loop that edits its own best-practices rubric runs against this repo's operating rule that *the agent is not the auditor of its own work* and *confirms with the human before any live write*. Keep the human-approval gate (PR / announcement) in the design unless the sponsor explicitly waives it.
