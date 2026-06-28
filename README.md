# Omnitune

**Keep your prompts and skills in tune with every AI model — automatically.**

Omnitune is a model-agnostic Claude Code plugin that audits your skills/agents and rewrites ad-hoc prompts against the *current* best practices of whatever model your session is running. It keeps a per-model rubric library and selects the right one automatically, so your prompting stays current as models evolve.

> Built and open-sourced by [Digital Research Group](https://digitalresearchgroup.com) — a gift to the community. MIT licensed, no telemetry.

## What it does

- **`/omnitune:tune-prompt "<text>"`** — rewrite an ad-hoc prompt into model-optimized form, self-scored in a QA loop (with a fabrication ledger so it never invents requirements) before you see it.
- **`/omnitune:tune-skill <name>`** — audit a `SKILL.md` or agent file against the current model's prompt-engineering best practices (7-dimension rubric) and apply interactive fixes.
- **`/omnitune:install`** *(optional)* — a guided interview that learns your repo and writes `omnitune.config.yaml` for repo-aware audits; the tune commands work without it.
- **`/omnitune:sync`** — when your session runs a model the rubric library doesn't cover yet, derive a behavioral-diff rubric to propose (human-approved, never silent).

## Quickstart

```text
/plugin marketplace add RobertBMoore/omnitune
/plugin install omnitune@omnitune
/reload-plugins
/omnitune:tune-prompt "your rough prompt"   # works immediately — no setup needed
```

That's it — `tune-prompt` and `tune-skill` run **standalone** (model-rubric only) the moment the plugin is installed. The model your session is running is detected automatically (including Nimbalyst ids like `claude-opus-4-8[1m]`).

Optional, for repo-aware power use:

```text
/omnitune:install            # builds omnitune.config.yaml by interview
```

This teaches Mode A/B your skills, routing, house style, and where to save reports/prompts — enrichment, not a prerequisite.

To get updates automatically, open `/plugin` → **Marketplaces → omnitune** → **Enable auto-update** (a one-time toggle). Organizations can roll Omnitune out hands-off via managed settings — see [`deploy/managed-settings.json`](deploy/managed-settings.json) and [`RELEASING.md`](RELEASING.md).

## Why it self-updates

A prompt that was optimal for one model can be suboptimal for the next — newer models calibrate length differently, are more literal, even reverse prior behaviors. Omnitune keeps a per-model rubric library and selects the rubric for the model your session is actually running; if it has none, `/omnitune:sync` proposes one — audited and human-approved, never silently self-patched. See [`wiki/Auto-Sync.md`](wiki/Auto-Sync.md).

## Configuration

Everything repo-specific lives in `omnitune.config.yaml`. Copy `omnitune.config.example.yaml` (a fictional TrailGear brand is the worked example) and edit, or let `/omnitune:install` build it. Field reference: [`omnitune.config.schema.md`](omnitune.config.schema.md).

## Docs

Browsable docs live in [`wiki/`](wiki/) — open [`wiki/index.html`](wiki/index.html) for the offline single-page version. Design rationale is in [`docs/design/`](docs/design/).

## Contributing

Issues and PRs welcome — see [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

MIT © Digital Research Group. No telemetry.
