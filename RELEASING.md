# Maintaining & deploying Omnitune

Omnitune (`RobertBMoore/omnitune`) is its own marketplace (`omnitune`) and the plugin it
distributes (the marketplace entry uses `source: "./"`). There is a single channel: **`main`**.

## Channel model
- `main` is the stable channel. Consumers track it; merged commits are what they get.
- Keep `main` green: contributors work on feature branches → PR → CI (`validate.yml`) → merge.
- Dogfood unreleased changes with `claude --plugin-dir .` (loads the working tree).
- Versioning is **SHA-based** — never add a `version` to `plugin.json`/marketplace entry (CI's `validate_plugin.py` blocks it; a pinned version silently freezes updates).

## How users install
```text
/plugin marketplace add RobertBMoore/omnitune
/plugin install omnitune@omnitune
/reload-plugins
```
Auto-update for individuals is a one-time toggle: `/plugin` → Marketplaces → `omnitune` → Enable auto-update.

## Hands-off org rollout (managed settings)
Deploy `deploy/managed-settings.json` to each machine's managed path so the plugin auto-installs
and auto-updates with no per-user action (public repo → no token needed):
- macOS: `/Library/Application Support/ClaudeCode/managed-settings.json`
- Linux/WSL: `/etc/claude-code/managed-settings.json`
- Windows: `C:\Program Files\ClaudeCode\managed-settings.json`

Push it via MDM (Jamf/Kandji/Intune), the `managed-settings.d/` drop-in, or Anthropic
server-managed settings (admin console) if you have a Team/Enterprise org.

## Pre-publish privacy gate
Before any public push, run the clean-sweep with the private denylist:
`python3 scripts/check_public_clean.py . --denylist scripts/.public-denylist.txt` → must be OK.
