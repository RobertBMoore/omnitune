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
- **Teams:** commit `docs/install/team-settings.json` into a repo's `.claude/settings.json` to prompt collaborators on trust; or roll out hands-off org-wide with `deploy/managed-settings.json` (see `RELEASING.md`).

## 2. Use it immediately — no setup required
Both modes work the moment the plugin is installed, with **zero config**:

```text
/omnitune:tune-prompt "a rough prompt you want sharpened"
/omnitune:tune-skill path/to/SKILL.md
```

In standalone mode the tool reads the model **your session is running** (including Nimbalyst ids like `claude-opus-4-8[1m]`), selects that model's rubric, rewrites/audits against it, and shows the result in chat — no `omnitune.config.yaml` needed. `/omnitune:tune-skill` audits any explicit file path directly.

Config is **optional enrichment**, not a prerequisite — add it (next) only when you want repo-aware routing, context pointers, saved report/prompt paths, and house-style awareness.

## 3. (Optional) Run `/omnitune:install` for repo-aware mode
Optional — the modes already work without it (above). Run it when you want omnitune to learn your repo: routing by skill, context pointers, house rules, and where to save reports/prompts. Setup is an interview that audits its own understanding before writing anything — it drafts your config from the repo, then asks you to confirm. It never writes omnitune.config.yaml from guesses.

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
Run `/omnitune:tune-prompt "a rough prompt"` and `/omnitune:tune-skill <a skill file>`. In standalone mode both run against the session model's rubric and print to chat; once you've run `/omnitune:install`, they additionally honor your config's routing, context pointers, and output paths. See [Configuration](Configuration.md) to hand-edit anything, and [FAQ](FAQ.md) if a command doesn't fire.
