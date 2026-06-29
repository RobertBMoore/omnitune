#!/usr/bin/env python3
"""detect_model — read the active model id from a Codex config.toml.

omnitune detects the session model from the host harness. Claude Code / Nimbalyst
state it in the system prompt; Codex sets it in config.toml and exposes no env var
for it. This helper resolves the durable Codex model using Codex's precedence:
the closest-to-cwd project `.codex/config.toml` wins, else the global config at
`$CODEX_HOME/config.toml` (or `~/.codex/config.toml`). Only the top-level `model`
key is read (a `[profiles.*]` model is ignored). Never raises; returns None when
no model is configured. Dependency-free.
"""
import os
import re

_MODEL_RE = re.compile(r"""^\s*model\s*=\s*["']([^"']+)["']""")


def _top_level_model(path):
    """Return the top-level `model` value from a TOML file, or None.
    Reads only the section before the first [table] header."""
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.lstrip().startswith("["):   # entered a [table]; top-level done
                    break
                m = _MODEL_RE.match(line)
                if m:
                    return m.group(1).strip()
    except Exception:  # noqa: BLE001 - a missing/garbage config must never raise
        return None
    return None


def detect_codex_model(start_dir=None, codex_home=None):
    """Resolve the durable Codex model id, or None. Closest-to-cwd project
    .codex/config.toml wins; else the global $CODEX_HOME/~/.codex config."""
    d = os.path.abspath(start_dir or os.getcwd())
    while True:
        model = _top_level_model(os.path.join(d, ".codex", "config.toml"))
        if model:
            return model
        parent = os.path.dirname(d)
        if parent == d:            # reached filesystem root
            break
        d = parent
    home = (codex_home or os.environ.get("CODEX_HOME")
            or os.path.join(os.path.expanduser("~"), ".codex"))
    return _top_level_model(os.path.join(home, "config.toml"))


if __name__ == "__main__":
    _m = detect_codex_model()
    if _m:
        print(_m)
