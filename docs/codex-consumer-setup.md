# Use omnitune under Codex in your own repo

Codex has no plugin system, so omnitune ships to your repo as a git submodule plus a managed `AGENTS.md` block that Codex auto-loads.

## Setup
1. **Add omnitune as a submodule** at `.omnitune/`:
   ```
   git submodule add https://github.com/RobertBMoore/omnitune .omnitune
   ```
   (Optional pin: `cd .omnitune && git checkout <sha> && cd ..`.) Commit the submodule.
2. **Install the AGENTS.md block** (safe on an existing `AGENTS.md` — it only edits its own managed block):
   ```
   python3 .omnitune/scripts/agents_merge.py
   ```
3. **(Optional) repo-aware config:** create `omnitune.config.yaml` at your repo root for routing/context. Without it, tune/sync run standalone on the model rubric alone.

Now a Codex session in this repo auto-loads the omnitune block and can run `tune-prompt`, `tune-skill`, and `sync` — following `.omnitune/skills/*/SKILL.md` (paths prefixed with `.omnitune/`), behind omnitune's safety invariants.

## Update
```
git submodule update --remote .omnitune
python3 .omnitune/scripts/agents_merge.py
```
