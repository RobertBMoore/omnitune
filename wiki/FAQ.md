# FAQ & Troubleshooting

**A command doesn't fire.**
You do **not** need `omnitune.config.yaml` — all three tune modes select the session model's rubric without it, and Mode C also loads its built-in pack/reflection contracts. If `/omnitune:tune-prompt`, `/omnitune:tune-skill`, or `/omnitune:tune-goal` is not recognized, the plugin is not loaded: confirm it installed (`claude plugin list` shows `omnitune@omnitune`) and reload (`/reload-plugins`, or restart your editor). Config via `/omnitune:install` only adds repo-aware routing, pointers, and saved-output paths — it is never required to make a command fire.

**When should I use `tune-goal` instead of `tune-prompt`?**
Use `tune-prompt` for one focused task. Use `tune-goal` when the work must survive milestones, compaction, parallel agents, deployments, human approvals, or an interrupted orchestrator. Mode C's state contracts, bounded roles, pre-flight checklist, and gates are intentionally heavier than a one-shot rewrite.

**Why did `tune-goal` ask several questions before writing anything?**
A valid pack needs deploy targets, gate commands and required environments, checkpoint ownership/channel, quiet hours, milestone shape, and a target directory. Missing project facts are asked as numbered questions rather than invented. Contract defaults are cited; every other added specific must be cited to the brief/config or labeled in the assumptions block.

**Where does a Mode C pack go?**
A directory named in your brief wins. Otherwise, `output.packs` creates a dated subdirectory under the configured path. With neither, standalone Mode C presents the structure in chat and offers to save it; missing config never blocks the run.

**Does a launch-ready pack launch the project?**
No. “Launch-ready” means the operating pack is ready for operator pre-flight. Mode C does not execute the project, wire the watchdog's scheduler/alert channel, validate the semantics of your shell commands, approve production, or replace CI, security review, product tests, and human judgment.

**What if the Mode C self-check does not pass?**
The pack is not ready. Resolve the named traceability, fabrication-ledger, completeness, or script-syntax issue before launch.

**Does `record_check.py` require Git?**
Yes. Mode C is best for Git-backed work, and the record gate fails closed when it cannot inspect repository state.

**I see "No tuned rubric for `<model>`" badge.**
Your session is running a model the library does not cover yet. The run still completed — it used the closest-family rubric. Run `/omnitune:sync` when convenient to derive a tuned rubric. It falls back to propose-only whenever a safety gate is unavailable or fails, and a human always makes the final commit. See [Auto-Sync](Auto-Sync.md).

**A rubric says `source_status: derived-tier` — can I trust it?**
The Opus 4.8 rubric is sourced from live docs. The Sonnet 4.6 and Haiku 4.5 rubrics were authored from tier knowledge; their version-specific items are marked `(verify)`. They're usable today, but run `/omnitune:sync` to replace the flagged items with sourced specifics before relying on them for precise effort/context-window decisions.

**Mode B added something I didn't ask for.**
It shouldn't silently. Anything it adds is either cited to a config `context_pointer` or listed in an "I assumed…" ledger for you to confirm. If you see an uncited invented specific, that's a fabrication-ledger bug — report it.

**Mode B "padded" my short prompt.**
It shouldn't — the prompt-class gate marks the brief-shaped dimensions N/A for `code`, `factual-terse`, `command`, and `adversarial-eval` classes. If a terse prompt got scope statements and success criteria it didn't need, the class was likely misjudged; re-run and it will ask to classify.

**I work offline / in CI.**
Set `model_sync.channel: manual`. Detection and any documentation fetch then run only on explicit `/omnitune:sync`; the tune modes themselves do not need a network call.

**Does it phone home?**
No telemetry. Apart from host-managed plugin installation/updates, omnitune's runtime network use is rubric sync fetching the resolved provider's allowlisted documentation. Every planned URL and redirect hop is checked against that provider's manifest allowlist; an empty or rejected plan fails closed.

**A skill got renamed and routing broke.**
Config can rot after renames. Re-run `/omnitune:install` (it re-drafts from the current repo) or, in v0.2, the `--check` lint asserts every `routing` skill and pointer path still resolves.

**Multiple repos — I keep getting the same badge.**
State (`.sync-state.json`, model-usage) is per-repo today; a global cross-repo preference is a v1.0 item. For now, set `channel: manual` in repos where you don't want the badge.

**Can I audit omnitune with omnitune?**
Yes, but Mode A is forbidden from softening the plugin's own fail-closed safety clauses (the never-self-commit invariant), even where the calm-register rule would otherwise flag their emphasis. Those are the safety exception.
