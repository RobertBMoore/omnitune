# omnitune wiki

A portable Claude Code plugin that keeps prompts, reusable skills, and long-running project goals tuned to the **model your session is actually running** — across supported providers, in any repo.

## Pages
- **[How-It-Works](How-It-Works.md)** — the three tune modes, their quality loops, rubric selection, and the freshness contract.
- **[Tune-Goal](Tune-Goal.md)** — when to turn a brief into an orchestration pack, what the seven-part pack contains, and a complete fictional example.
- **[Install-Setup](Install-Setup.md)** — installing the plugin and the guided `/omnitune:install` interview.
- **[Configuration](Configuration.md)** — every `omnitune.config.yaml` field, with a worked example.
- **[Auto-Sync](Auto-Sync.md)** — how the model-sync interrupt + behavioral-diff loop keeps the rubric current.
- **[FAQ](FAQ.md)** — troubleshooting, offline use, adding a skill to routing.

## The 60-second mental model

1. **Use it immediately — no setup.** `tune-prompt` sharpens one request, `tune-skill` audits reusable instructions, and `tune-goal` turns a project brief into a launch pack that can survive milestones, handoffs, and context loss. Each selects the rubric for the model your session is running.
2. **Choose the lightest mode that fits.** Use Mode B for one task, Mode A for one reusable skill/agent, and Mode C when work needs durable state, bounded agents, human checkpoints, deployments, or external liveness checks.
3. **Add config when you want repo-awareness — optional.** `/omnitune:install` interviews you and your repo, then writes `omnitune.config.yaml`. Set `output.packs` for a default Mode C save location; when neither config nor the brief names a destination, Mode C works in chat and offers to save.
4. **It stays current.** A missing model rubric triggers a non-blocking badge or your configured sync channel. Rubric changes follow audited, fail-closed gates and are never silently self-committed.

## Design principles
- **Repo-agnostic core.** Zero domain assumptions; project specifics come only from the user's prompt/brief or optional config.
- **Model-aware + human-gated sync.** The best available rubric is selected locally; new rubric changes are independently audited and human-committed.
- **Human stays the operator.** Project checkpoints, reserved decisions, and launch approval are surfaced rather than guessed; rubric changes are independently audited and human-committed.
