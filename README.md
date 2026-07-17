# Omnitune

**Keep your prompts, skills, and project goals in tune with the AI model you're running.**

Omnitune is a model-agnostic Claude Code plugin that audits reusable skills/agents, rewrites ad-hoc prompts, and turns complex project goals into launch-ready orchestration packs for the model your session is running. It resolves the best available rubric automatically; an exact match is used when available, and a closest-family fallback is clearly badged.

> Built and open-sourced by [Digital Research Group](https://digitalresearchgroup.com) — a gift to the community. MIT licensed, no telemetry.

## What it does

- **`/omnitune:tune-prompt "<text>"`** — rewrite an ad-hoc prompt into model-tuned form, self-scored in a QA loop; added specifics must be cited or surfaced as assumptions.
- **`/omnitune:tune-skill <name>`** — audit a `SKILL.md` or agent file against the current model's prompt-engineering best practices (7-dimension rubric) and apply interactive fixes.
- **`/omnitune:tune-goal "<brief>"`** — turn a multi-milestone project brief into an operating pack: goal statute, short constitution, scoped builders/auditors, resumable state, guardrails, operator checkpoints, and runnable record/liveness gates.
- **`/omnitune:install`** *(optional)* — a guided interview that learns your repo and writes `omnitune.config.yaml` for repo-aware audits; the tune commands work without it.
- **`/omnitune:sync`** — when your session runs a model the rubric library doesn't cover yet, derive a behavioral-diff rubric to propose (human-approved, never silent).

| What you have | Use | What comes back |
|---|---|---|
| One rough task or request | `tune-prompt` | A tighter, model-tuned prompt |
| An existing reusable skill or agent | `tune-skill` | A severity-ranked audit and interactive fixes |
| A project that must survive milestones, handoffs, or multiple sessions | `tune-goal` | A launch pack that turns operating discipline into files, roles, checkpoints, and gates |

## Quickstart

```text
/plugin marketplace add RobertBMoore/omnitune
/plugin install omnitune@omnitune
/reload-plugins
/omnitune:tune-prompt "your rough prompt"   # works immediately — no setup needed
/omnitune:tune-goal "Use docs/project-brief.md; save the pack under docs/orchestration/"
```

That's it — all three tune modes work **without config** the moment the plugin is installed. The model your session is running is detected automatically (including Nimbalyst ids like `claude-opus-4-8[1m]`); Mode C combines that rubric with its built-in pack and reflection contracts. When neither config nor the brief names a destination, `tune-goal` presents the pack in chat and offers to save it.

Optional, for repo-aware power use:

```text
/omnitune:install            # builds omnitune.config.yaml by interview
```

This adds repo-aware routing, context, house style, and saved report/prompt paths — enrichment, not a prerequisite. Set `output.packs` when you also want a default directory for dated Mode C packs.

To get updates automatically, open `/plugin` → **Marketplaces → omnitune** → **Enable auto-update** (a one-time toggle). Organizations can roll Omnitune out hands-off via managed settings — see [`deploy/managed-settings.json`](deploy/managed-settings.json) and [`RELEASING.md`](RELEASING.md).

## Why `tune-goal` is different

A strong first prompt is not enough for long-running agent work. Common failure modes include stale state, remembered rather than recorded evidence, parallel collisions, guessed human decisions, and an orchestrator disappearing silently. `tune-goal` moves those risks out of chat and into an explicit operating system for the build.

It is best for Git-backed, multi-milestone work with deployments, parallel agents, operator approvals, or continuity across context windows. For a one-off task, `tune-prompt` is lighter.

Before emitting a pack, Mode C asks numbered questions for missing deploy targets, gate commands and environments, checkpoint ownership, quiet hours, milestones, and the save location — and for the team-design facts (scale, runtime models per role, and workstream independence) that let it size and tier the agent team. Every added project-specific detail must come from the brief/config or be labeled as an assumption. It then runs the recording self-check (contract traceability, all seven required components, the fabrication ledger, line caps, Python/Bash gate syntax) and the topology self-check (every agent tiered and justified, roles mapping to the brief, fan-out matching each runtime rubric). An unresolved check is never presented as ready.

CI fails if any of 25 recording mappings, eleven topology-contract points, or seven reflection rows is missing or empty, or if either gate template fails Python/Bash syntax checks. These structural checks do not guarantee a project outcome or replace product tests, security review, CI, or human launch approval. See the [Tune Goal guide](wiki/Tune-Goal.md) for the full lifecycle and a privacy-safe, production-shaped example.

## Why it self-updates

A prompt that was optimal for one model can be suboptimal for the next — newer models calibrate length differently, are more literal, even reverse prior behaviors. Omnitune keeps a per-model rubric library and selects the rubric for the model your session is actually running; if it has none, `/omnitune:sync` proposes one — audited and human-approved, never silently self-patched. See [`wiki/Auto-Sync.md`](wiki/Auto-Sync.md).

## Configuration

The core contains no domain knowledge. Per-run specifics come only from the user's prompt/brief or optional `omnitune.config.yaml`; persistent repo defaults live in config. Copy `omnitune.config.example.yaml` (a fictional TrailGear brand is the worked example) and edit, or let `/omnitune:install` build it. Field reference: [`omnitune.config.schema.md`](omnitune.config.schema.md).

## Docs

Browsable docs live in [`wiki/`](wiki/) — open [`wiki/index.html`](wiki/index.html) for the offline single-page version. Design rationale is in [`docs/design/`](docs/design/).

**Using omnitune under Codex (in your own repo):** see [`docs/codex-consumer-setup.md`](docs/codex-consumer-setup.md).

## Contributing

Issues and PRs welcome — see [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

MIT © Digital Research Group. No telemetry.
