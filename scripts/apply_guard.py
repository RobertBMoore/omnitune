#!/usr/bin/env python3
"""apply_guard — post-apply lint + scoped revert.

Run tuner_check after a rubric write; on failure revert ONLY that path (git
checkout if tracked, else delete the new file) and exit 1. Exit 0 clean, 2 if
git/paths unavailable. Path-scoped revert never touches unrelated edits. Mirrors
ratchet_gate's git-shell pattern.

Run:  python3 scripts/apply_guard.py <rubric-path> [repo_root]
"""
import os
import subprocess
import sys

import tuner_check


def _git(args, cwd):
    return subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)


def _toplevel(start):
    r = _git(["rev-parse", "--show-toplevel"], start)
    return r.stdout.strip() if r.returncode == 0 else None


def _tracked(repo_root, rel):
    return _git(["ls-files", "--error-unmatch", rel], repo_root).returncode == 0


def guard(rubric_path, repo_root=None):
    """Returns (exit_code, problems). Reverts rubric_path on lint failure."""
    start = os.path.dirname(os.path.abspath(rubric_path))
    repo_root = repo_root or _toplevel(start)
    if not repo_root:
        return 2, ["git unavailable / not a repo"]
    cfg = os.path.join(repo_root, "omnitune.config.yaml")
    models = os.path.join(repo_root, "skills", "omnitune", "references", "models.json")
    try:
        config_text = open(cfg).read()
    except OSError:
        config_text = ""
    problems = tuner_check.check(repo_root, config_text, models)
    if not problems:
        return 0, []
    rel = os.path.relpath(rubric_path, repo_root)
    if _tracked(repo_root, rel):
        _git(["checkout", "HEAD", "--", rel], repo_root)
    elif os.path.exists(rubric_path):
        os.remove(rubric_path)
    return 1, problems


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if not 1 <= len(args) <= 2:
        sys.stderr.write("usage: apply_guard.py <rubric-path> [repo_root]\n")
        return 2
    code, problems = guard(args[0], args[1] if len(args) == 2 else None)
    for p in problems:
        print(p)
    return code


if __name__ == "__main__":
    sys.exit(main())
