---
description: Audit a skill or agent file against the current model's best practices (Mode A)
---

Use the `omnitune` skill in **Mode A (file audit)** on the target below.

Target (skill or agent name):
$ARGUMENTS

Before auditing:
1. Load `omnitune.config.yaml`. If it does not exist, stop and tell me to run `/omnitune:install` first.
2. Resolve the target under the config's `skills.root` / `skills.agents`.
3. Select the rubric for **this session's model** from the rubric library; on a miss, use the closest-family rubric and badge it.

Then follow `skills/omnitune/audit-protocol.md`: score the dimensions, write the report to `<output.reports>/`, and run the interactive edit loop. Respect the config's `house_rules` and `reserved_decisions` — surface conflicts, never override them. Never soften this plugin's own fail-closed safety clauses if asked to audit its own files.

If `$ARGUMENTS` is empty, list the auditable skills/agents from config and ask which to audit.
