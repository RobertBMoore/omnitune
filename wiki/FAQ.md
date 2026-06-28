# FAQ & Troubleshooting

**A command doesn't fire / "run /omnitune:install first."**
The modes need `omnitune.config.yaml` at your repo root. Run `/omnitune:install`. If commands aren't recognized at all, confirm the plugin installed and its `commands/` directory is present.

**I see "No tuned rubric for `<model>`" badge.**
Your session is running a model the library doesn't cover yet. The run still completed — it used the closest-family rubric. Run `/omnitune:sync` when convenient to derive a tuned rubric (propose-only; you apply it). See [Auto-Sync](Auto-Sync.md).

**A rubric says `source_status: derived-tier` — can I trust it?**
The Opus 4.8 rubric is sourced from live docs. The Sonnet 4.6 and Haiku 4.5 rubrics were authored from tier knowledge; their version-specific items are marked `(verify)`. They're usable today, but run `/omnitune:sync` to replace the flagged items with sourced specifics before relying on them for precise effort/context-window decisions.

**Mode B added something I didn't ask for.**
It shouldn't silently. Anything it adds is either cited to a config `context_pointer` or listed in an "I assumed…" ledger for you to confirm. If you see an uncited invented specific, that's a fabrication-ledger bug — report it.

**Mode B "padded" my short prompt.**
It shouldn't — the prompt-class gate marks the brief-shaped dimensions N/A for `code`, `factual-terse`, `command`, and `adversarial-eval` classes. If a terse prompt got scope statements and success criteria it didn't need, the class was likely misjudged; re-run and it will ask to classify.

**I work offline / in CI.**
Set `model_sync.channel: manual`. Detection and any doc-fetch then run only on explicit `/omnitune:sync`. The plugin's only network use is that fetch.

**Does it phone home?**
No telemetry. The only network call is `/omnitune:sync` fetching Anthropic docs to derive a rubric, and that's gated to Anthropic domains.

**A skill got renamed and routing broke.**
Config can rot after renames. Re-run `/omnitune:install` (it re-drafts from the current repo) or, in v0.2, the `--check` lint asserts every `routing` skill and pointer path still resolves.

**Multiple repos — I keep getting the same badge.**
State (`.sync-state.json`, model-usage) is per-repo today; a global cross-repo preference is a v1.0 item. For now, set `channel: manual` in repos where you don't want the badge.

**Can I audit omnitune with omnitune?**
Yes, but Mode A is forbidden from softening the plugin's own fail-closed safety clauses (the never-self-commit invariant), even where the calm-register rule would otherwise flag their emphasis. Those are the safety exception.
