# Contributing to Omnitune

Thanks for helping keep prompting in tune! Omnitune is open-sourced by Digital Research Group under MIT.

## Workflow
1. Fork or branch (`feature/<short-name>`).
2. Make your change. Keep the core **model-agnostic and repo-agnostic** — domain specifics belong in a host's `omnitune.config.yaml`, never hardcoded.
3. Run the checks locally:
   ```sh
   cd scripts && python3 -m unittest test_tuner_check test_rubric_ratchet test_sync_state test_validate_plugin test_check_public_clean
   python3 ../scripts/validate_plugin.py ..
   python3 ../scripts/check_public_clean.py ..
   ```
4. Open a PR to `main`. CI (`.github/workflows/validate.yml`) must pass.

`main` is the single stable channel: merged commits are what users install. Keep it green.

## Dogfooding
Run Omnitune on itself: `claude --plugin-dir .` then `/omnitune:tune-skill omnitune`.

## Rubrics
Per-model rubrics live in `skills/omnitune/references/rubrics/`. New models get a rubric via `/omnitune:sync` (propose-only) — see `wiki/Auto-Sync.md`.

## Code style
Scripts are dependency-free Python 3.9+ (stdlib + vendored `miniyaml`). No third-party packages.
