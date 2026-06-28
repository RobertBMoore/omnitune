# omnitune wiki

A portable Claude Code plugin that keeps your prompts and skills tuned to the **current** Anthropic model — in any repo, for any business.

## Pages
- **[How-It-Works](How-It-Works.md)** — the two modes, the QA loop, the 7-dimension rubric, the freshness contract.
- **[Install-Setup](Install-Setup.md)** — installing the plugin and the guided `/omnitune:install` interview.
- **[Configuration](Configuration.md)** — every `omnitune.config.yaml` field, with a worked example.
- **[Auto-Sync](Auto-Sync.md)** — how the model-sync interrupt + behavioral-diff loop keeps the rubric current.
- **[FAQ](FAQ.md)** — troubleshooting, offline use, adding a skill to routing.

## The 60-second mental model

1. **Install once.** `/omnitune:install` interviews you and your repo, then writes `omnitune.config.yaml`. That file holds everything specific to you; the plugin core holds nothing about your domain.
2. **Use two modes.** `/omnitune:tune-prompt` rewrites a rough prompt into model-optimal form (self-scored before you see it). `/omnitune:tune-skill` audits a skill/agent file and applies fixes.
3. **It stays current.** When a newer Anthropic model ships, the tuner notices at the start of a run, asks if you want to update (or skip/defer/snooze), and — if you do — audits what actually changed before patching its own rubric. It never patches silently.

## Design principles
- **Repo-agnostic core.** Zero domain assumptions; all coupling lives in `omnitune.config.yaml`.
- **Model-agnostic + self-updating.** The rubric tracks whatever model is current.
- **Human is the auditor.** Install confirms before writing; model-sync proposes before patching. The tool never grades its own brain unsupervised.
