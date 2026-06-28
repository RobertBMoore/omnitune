# Design & decision history

How and why omnitune is built the way it is. These are provenance documents from the original build (in a private working repo, 2026-06-14); some absolute file paths in them reference that build location, not this repo.

| Doc | What it is |
|---|---|
| [00-origin-prompt.md](00-origin-prompt.md) | The tuned prompt that kicked off the project (itself a Mode-B rewrite). |
| [01-design.md](01-design.md) | The v0.1 design: package architecture, the config-layer decoupling, the install-time auditor loop, the model-sync interrupt model. |
| [02-audit-synthesis.md](02-audit-synthesis.md) | Synthesis of a 5-auditor review panel (prompt-engineering, portability, safety/HITL, product/UX, adversarial red-team) plus a master-auditor adjudication. The findings here drove most of the safety design. |
| [03-decisions-v0.1.md](03-decisions-v0.1.md) | Locked v0.1 decisions: session-model detection (no live scrape), the multi-model rubric library, propose-only sync, the adaptive install wizard, badge-default model notices. |
| [04-design-v0.2.md](04-design-v0.2.md) | The v0.2 trust layer: gated self-apply (no-write subagent + tighten-only ratchet + fail-closed regression corpus), the CI lint, atomic state, and live model sync. |

## Why the safety design looks the way it does
The single most important constraint, surfaced repeatedly by the audit panel: **the tool grades prompts and skills against a rubric it can rewrite for itself.** Left unchecked, that is a closed loop with no external anchor — it could quietly grade itself easier. Every safety mechanism (propose-only in v0.1; the no-write audit subagent, the tighten-only ratchet, the fail-closed corpus, and the human-commit gate in v0.2) exists to keep a human in the loop on any change to the tool's own brain. See `02-audit-synthesis.md` §A4 and `04-design-v0.2.md` §v0.2.1.
