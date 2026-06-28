# Install & Setup

## 1. Install the plugin
Quickest path — add the marketplace and install (user scope = available in all your repos), then reload:

```text
/plugin marketplace add RobertBMoore/omnitune
/plugin install omnitune@omnitune
/reload-plugins
```

- Marketplace: `omnitune`, tracking the `main` channel. Commands register namespaced: `/omnitune:tune-prompt`, `/omnitune:tune-skill`, `/omnitune:install`, `/omnitune:sync`.
- **Auto-update** is a one-time per-user toggle: `/plugin` → Marketplaces → `omnitune` → Enable auto-update.
- **Teams:** commit [`docs/install/team-settings.json`](../docs/install/team-settings.json) into a repo's `.claude/settings.json` to prompt collaborators on trust; or roll out hands-off org-wide with [`deploy/managed-settings.json`](../deploy/managed-settings.json) (see [`RELEASING.md`](../RELEASING.md)).

## 2. Run `/omnitune:install`
Setup is an **interview that audits its own understanding before writing anything** — it drafts your config from the repo, then asks you to confirm. It never writes `omnitune.config.yaml` from guesses.

What it does, in order:
1. **Detect + draft.** Reads your `CLAUDE.md`/`AGENTS.md`/`README.md`, lists your skills, and **drafts the technical fields for you** — the routing keyword table and context-pointers — by reading the repo. You don't author routing tables blind.
2. **Gauge.** One question sets how much it explains, not what it covers: comfortable with YAML, or prefer plain language? Every operator gets the full drafted config either way.
3. **Confirm.** It walks each drafted field at your chosen depth — "I think 'review this campaign' should route to your `campaign-review` skill — right?" — and you confirm or correct. Low-confidence guesses are flagged for extra scrutiny.
4. **Dry-run.** Before saving, it proves the config works: rewrites one sample prompt (Mode B) and audits one of your real skills (Mode A), and shows you the results.
5. **Write.** Only now does it write `omnitune.config.yaml` to your repo root, and prints the three commands with an example of each.

## Edge cases the wizard handles
- **No skills yet** — produces a valid Mode-B-only config (empty `routing[]`); the Mode A dry-run is skipped.
- **Monorepo / multiple skill roots** — it asks which package root owns the config.
- **Non-technical operator** — the technical fields are drafted *for* you; an optional "have a developer eyeball the routing table?" hand-off is offered, never required.

## Verify
After install, run `/omnitune:tune-prompt "a rough prompt"` and `/omnitune:tune-skill <one-of-your-skills>`. Both should run against your new config. See [Configuration](Configuration.md) to hand-edit anything, and [FAQ](FAQ.md) if a command doesn't fire.
