# Configuration

Everything repo-specific lives in `omnitune.config.yaml` at your repo root. The plugin core holds no domain knowledge of its own. `/omnitune:install` generates this file; you can also hand-edit it. Full field reference: [`omnitune.config.schema.md`](../omnitune.config.schema.md).

## Worked example
```yaml
project:
  name: "TrailGear"
  domain: "Direct-to-consumer outdoor gear (tents, packs, apparel)."
skills:
  root: "skills/"
  agents: ""                      # "" if you have no agent files
routing:                          # keyword -> skill, for Mode B target detection
  - skill: "product-blurb"
    keywords: ["product blurb", "write a blurb", "blurb for the", "product copy"]
context_pointers:                 # files Mode B cites when a target is detected
  - when: "product-blurb"
    point_to: ["brand/voice.md"]
house_rules: "brand/voice.md"     # voice/anti-patterns the tuner must respect; "" if none
reserved_decisions: ""            # decisions to SURFACE not pre-empt; "" if none
output:
  reports: "reports/"
  prompts: "docs/prompts/"
model_sync:
  channel: "badge"                # badge (default) | interrupt | manual
  target_model: ""                # override session-model detection (headless/CI)
  snooze_default: "24h"
  regression_corpus: "tuner/regression/"
```
(A fuller fictional TrailGear example ships in [`omnitune.config.example.yaml`](../omnitune.config.example.yaml) — nothing is baked into the core.)

## How the fields drive the modes
- **`routing[]`** — Mode B matches your raw prompt's words against these keywords to pick the target skill. Empty is valid (Mode B then runs without target context).
- **`context_pointers[]`** — when a target is detected, Mode B cites these files. This is also what the fabrication ledger checks "cited" against.
- **`house_rules`** — Mode A's voice dimension (D7) and Mode B's caveats read this. If empty, D7 scores N/A.
- **`reserved_decisions`** — Mode B surfaces (never pre-empts) any decision in this file that a rewrite touches.
- **`output.*`** — where reports and rewritten prompts are saved.

## Common edits
- **Add a skill to routing:** append a `routing[]` entry with the phrases users would type for it.
- **Add a voice/style source:** set `house_rules` to its path; Mode A will start scoring copy skills against it.
- **Turn off model notices:** set `model_sync.channel: manual` (air-gapped/CI). See [Auto-Sync](Auto-Sync.md).
- **CI config check:** run the install wizard's `--check` (v0.2) to assert every `routing` skill and pointer path still resolves — catches silent config rot after renames.
