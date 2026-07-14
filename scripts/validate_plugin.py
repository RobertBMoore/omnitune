#!/usr/bin/env python3
"""validate-plugin — dependency-free structural lint for the omnitune plugin
and its self-hosted marketplace manifest.

Guards the distribution invariants (see docs/superpowers/specs/2026-06-20-omnitune-distribution-design.md):
  - .claude-plugin/marketplace.json is well-formed (name, owner.name, a non-empty
    plugins[] with a omnitune entry whose source is "./", no pinned version).
  - .claude-plugin/plugin.json names the plugin and pins NO version (SHA-based
    versioning; a pinned version silently blocks all updates).

Usage:
  python3 validate_plugin.py [REPO_ROOT]
Exit 0 = clean, 1 = problems (printed to stderr).
"""
import json
import os
import sys

PLUGIN_NAME = "omnitune"


def _load_json(path):
    with open(path) as f:
        return json.load(f)


def validate(repo_root):
    """Return a list of human-readable problem strings (empty == clean)."""
    problems = []
    cp_dir = os.path.join(repo_root, ".claude-plugin")

    mkt = None
    mkt_path = os.path.join(cp_dir, "marketplace.json")
    if not os.path.exists(mkt_path):
        problems.append("marketplace: .claude-plugin/marketplace.json is missing")
    else:
        try:
            mkt = _load_json(mkt_path)
        except Exception as e:  # noqa: BLE001 - lint must not crash a build opaquely
            problems.append("marketplace: invalid JSON: %s" % e)
    if mkt is not None:
        if not mkt.get("name"):
            problems.append("marketplace: missing 'name'")
        owner = mkt.get("owner")
        if not isinstance(owner, dict) or not owner.get("name"):
            problems.append("marketplace: missing 'owner.name'")
        plugins = mkt.get("plugins")
        if not isinstance(plugins, list) or not plugins:
            problems.append("marketplace: 'plugins' must be a non-empty array")
        else:
            entry = next((p for p in plugins
                          if isinstance(p, dict) and p.get("name") == PLUGIN_NAME), None)
            if entry is None:
                problems.append("marketplace: no plugin entry named '%s'" % PLUGIN_NAME)
            else:
                if entry.get("source") != "./":
                    problems.append("marketplace: '%s' source must be './' (got %r)"
                                    % (PLUGIN_NAME, entry.get("source")))
                if "version" in entry:
                    problems.append("marketplace: '%s' entry must NOT pin 'version' "
                                    "(SHA-based versioning)" % PLUGIN_NAME)

    plug = None
    plug_path = os.path.join(cp_dir, "plugin.json")
    if not os.path.exists(plug_path):
        problems.append("plugin: .claude-plugin/plugin.json is missing")
    else:
        try:
            plug = _load_json(plug_path)
        except Exception as e:  # noqa: BLE001
            problems.append("plugin: invalid JSON: %s" % e)
    if plug is not None:
        if plug.get("name") != PLUGIN_NAME:
            problems.append("plugin: 'name' must be '%s' (got %r)"
                            % (PLUGIN_NAME, plug.get("name")))
        if "version" in plug:
            problems.append("plugin: plugin.json must NOT pin 'version' — it silently "
                            "blocks updates (see distribution design D2)")
        # The standard hooks/hooks.json is auto-loaded by Claude Code. Naming it
        # again in manifest.hooks double-loads it and fails the whole plugin at
        # load time ("Duplicate hooks file detected"), so its commands/skills
        # never register. manifest.hooks must reference ONLY additional hook files.
        hooks_field = plug.get("hooks")
        hook_refs = hooks_field if isinstance(hooks_field, list) else [hooks_field]
        for ref in hook_refs:
            if not isinstance(ref, str):
                continue
            norm = ref[2:] if ref.startswith("./") else ref
            if norm == "hooks/hooks.json":
                problems.append(
                    "plugin: 'hooks' must NOT reference the standard "
                    "hooks/hooks.json — it is auto-loaded, so a manifest reference "
                    "double-loads it and fails the plugin at load time. Omit 'hooks' "
                    "(the standard file still loads) or point it only at ADDITIONAL "
                    "hook files.")

    return problems


def main(argv):
    repo_root = argv[1] if len(argv) > 1 else os.getcwd()
    problems = validate(repo_root)
    if problems:
        sys.stderr.write("validate-plugin: %d problem(s):\n" % len(problems))
        for p in problems:
            sys.stderr.write("  - %s\n" % p)
        return 1
    sys.stdout.write("validate-plugin: OK (manifest + marketplace consistent)\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
