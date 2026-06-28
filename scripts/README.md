# omnitune scripts

Dependency-free Python (3.9+) helpers used by the plugin's skills and CI. No third-party packages (a tiny `miniyaml` is vendored so the lint runs anywhere).

| Script | Purpose | Used by |
|---|---|---|
| `tuner_check.py` | CI lint: validates `omnitune.config.yaml` (required fields, routing skills exist, pointer/house-rules paths resolve, valid channel) + the manifest (every GA model has a resolvable rubric). Exit 1 on problems. | CI / `/omnitune:install --check` |
| `rubric_ratchet.py` | Tighten-only gate: BLOCKs a rubric patch that loosens (removed section, fewer hard directives, severity downgrade) unless `--approve-loosening`. | `/omnitune:sync` gated self-apply (v0.2) |
| `sync_state.py` | Atomic, per-session, corruption-tolerant `tuner/.sync-state.json` for the model-sync interrupt channel. | `/omnitune:sync` interrupt channel |
| `miniyaml.py` | Vendored YAML-subset parser (no PyYAML dependency). | `tuner_check.py` |
| `validate_plugin.py` | Lint: `.claude-plugin/marketplace.json` + `plugin.json` structural invariants (incl. "no pinned version"). Exit 1 on problems. | CI |
| `check_public_clean.py` | Pre-publish gate: fails if the tree contains client/company-sensitive content (generic secret/PII patterns + an optional gitignored `.public-denylist.txt`). Exit 1 on hits. | CI / pre-publish |

## Run the tests
```sh
cd omnitune/scripts
python3 -m unittest test_tuner_check test_rubric_ratchet test_sync_state test_validate_plugin test_check_public_clean
```

## CLI examples
```sh
# Lint a host repo (exit 1 on problems):
python3 tuner_check.py /path/to/repo --models ../skills/omnitune/references/models.json

# Block a loosening rubric patch:
python3 rubric_ratchet.py current_rubric.md proposed_rubric.md           # exit 1 if it loosens
python3 rubric_ratchet.py current_rubric.md proposed_rubric.md --approve-loosening
```

`omnitune.config.yaml` must stay within the documented YAML subset (no anchors, multiline scalars, or flow maps) so the lint runs with zero dependencies.
