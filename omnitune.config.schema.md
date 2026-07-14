# omnitune.config.yaml — field reference

The single customization point for omnitune. The core plugin reads this; it contains no domain knowledge of its own. `/omnitune:install` generates this file by interview; you can also hand-edit it.

| Field | Required | Meaning |
|---|---|---|
| `project.name` | yes | Human label for the repo/business. Used in report headers. |
| `project.domain` | yes | One line describing what the repo/business does. Supplies persistent domain context without hardcoding it in the plugin. |
| `skills.root` | yes | Directory where the host keeps its skills (e.g. `skills/` or `.claude/skills/`). |
| `skills.agents` | no | Directory for agent files (e.g. `.claude/agents/`). Empty string if none. |
| `routing[].skill` | yes* | A skill name. *Required if you want Mode B target detection. |
| `routing[].keywords` | yes* | Phrases in a raw prompt that map to that skill. |
| `context_pointers[].when` | no | A skill/topic that, when detected, should pull in specific files. |
| `context_pointers[].point_to` | no | Files Mode B cites when `when` matches. |
| `house_rules` | no | Path to a file of domain anti-patterns/voice/style the tuner must honor. `''` if none. |
| `reserved_decisions` | no | Path to decisions the tuner must **surface, not pre-empt**. `''` if none. |
| `output.reports` | yes | Where Mode A writes audit reports. |
| `output.prompts` | yes | Where Mode B saves rewritten prompts. |
| `output.packs` | no | Where Mode C writes orchestration packs (one dated subdirectory per pack). When absent, Mode C asks for a target directory or presents the pack in chat with an offer to save — it never blocks. |
| `model_sync.channel` | yes | `badge` (default; non-blocking notice), `interrupt` (just-in-time halt with update/skip/defer/snooze), or `manual` (only on `/omnitune:sync`). |
| `model_sync.target_model` | no | Override session-model detection (headless/CI where the model id can't be read). `""` = auto-detect from the session. |
| `model_sync.snooze_default` | no | Default snooze window — only used when `channel: interrupt`. |
| `model_sync.regression_corpus` | no | Folder of prompt, skill, and goal fixtures used by the fail-closed corpus floor before a gated rubric apply. |

## How the rubric is selected

omnitune does **not** ask "is there a newer model in the world." At the start of each run it reads the model **this session is running**, matches it against `references/models.json`, and loads `references/rubrics/<provider>/<model>.md`. A miss is the only sync trigger — and even then the run proceeds on the closest-family rubric with a badge, never blocked.

## Validation rules

- A missing required field blocks install — the wizard asks rather than guessing.
- `routing` may be empty; Mode B then runs without target-specific context (still valid). On a repo with no skills, the wizard still produces a valid prompt/goal config.
- `house_rules` / `reserved_decisions` paths must exist if non-empty, else the wizard flags them.
- `model_sync.channel: manual` disables the badge/interrupt entirely (use for air-gapped or CI hosts); detection runs only on explicit `/omnitune:sync`.
- `model_sync.channel: badge` is the default — a non-blocking end-of-run notice when the current model lacks a tuned rubric or a newer GA model exists.
