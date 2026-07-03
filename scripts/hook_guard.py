#!/usr/bin/env python3
"""hook_guard — PreToolUse safety guards for the omnitune plugin.

Two deterministic, fail-closed guards enforcing the propose-only / never-self-commit
invariant MECHANICALLY (prose in the skills is not enough — a hook is the backstop):

  self-commit  (matcher: Bash)         Block a `git commit`/`git add` that stages a
                                       rubric under references/rubrics/** unless the
                                       operator's explicit approval marker is present.
  rubric-write (matcher: Write|Edit)   Block a Write/Edit to a rubric that LOOSENS it
                                       vs the committed version (removed fail-closed
                                       section, fewer hard directives, severity
                                       downgrade), unless approved.

Both read the PreToolUse JSON on stdin and, on a violation, print a reason to
stderr and exit 2 (Claude Code treats exit 2 as a blocking deny). Any parse/HTTP
failure exits 0 (a guard must never wedge a session on its own bug — the CI
ratchet gate and human commit remain the hard backstops). Dependency-free.

The approval marker (either lets a change through, mirroring rubric_ratchet's
--approve-loosening human-in-the-loop escape hatch):
  - env  OMNITUNE_APPROVE_RUBRIC=1, or
  - a file  .omnitune-approve-rubric  at the repo root.

Usage (wired from hooks/hooks.json):
  python3 hook_guard.py self-commit   < preToolUse.json
  python3 hook_guard.py rubric-write  < preToolUse.json
"""
import json
import os
import re
import subprocess
import sys

import rubric_ratchet

RUBRIC_RE = re.compile(r"(^|[\s'\"=/])skills/omnitune/references/rubrics/[^\s'\"]+\.md")
APPROVE_ENV = "OMNITUNE_APPROVE_RUBRIC"
APPROVE_FILE = ".omnitune-approve-rubric"


def _approved(cwd):
    if os.environ.get(APPROVE_ENV, "").strip() in ("1", "true", "yes"):
        return True
    return os.path.exists(os.path.join(cwd or ".", APPROVE_FILE))


def _deny(reason):
    sys.stderr.write("omnitune hook_guard: DENY — %s\n" % reason)
    return 2


def _allow():
    return 0


def _git_show_head(path, cwd):
    """The file's content at HEAD, or None if absent/unavailable."""
    try:
        r = subprocess.run(["git", "-C", cwd or ".", "show", "HEAD:%s" % path],
                           capture_output=True, text=True)
        return r.stdout if r.returncode == 0 else None
    except Exception:  # noqa: BLE001 - git missing must not wedge the session
        return None


def _rel_rubric(path, cwd):
    """Return the repo-relative rubric path if `path` is a rubric, else None."""
    if not path:
        return None
    p = path.replace("\\", "/")
    root = (cwd or ".").replace("\\", "/").rstrip("/")
    if root and p.startswith(root + "/"):
        p = p[len(root) + 1:]
    m = re.search(r"skills/omnitune/references/rubrics/[^\s'\"]+\.md$", p)
    return m.group(0) if m else None


def guard_self_commit(payload):
    """Block a git commit/add that stages a rubric path, absent approval."""
    ti = payload.get("tool_input") or {}
    cmd = ti.get("command") or ""
    cwd = payload.get("cwd") or os.getcwd()
    if not cmd:
        return _allow()
    is_git_write = bool(re.search(r"\bgit\s+(commit|add)\b", cmd))
    if not is_git_write:
        return _allow()
    if not RUBRIC_RE.search(cmd):
        # `git commit` with no rubric path in the command line: could still stage a
        # rubric via `git add .` earlier. Check the staged set as a backstop.
        staged = _staged_rubrics(cwd)
        if not staged:
            return _allow()
        if _approved(cwd):
            return _allow()
        return _deny("git %s would commit a staged rubric (%s) — omnitune rubrics are "
                     "propose-only; set %s=1 or add %s after human review."
                     % ("commit/add", ", ".join(staged), APPROVE_ENV, APPROVE_FILE))
    if _approved(cwd):
        return _allow()
    return _deny("git command stages an omnitune rubric — rubrics are propose-only "
                 "(never self-committed); set %s=1 or add %s at the repo root after "
                 "human review." % (APPROVE_ENV, APPROVE_FILE))


def _staged_rubrics(cwd):
    try:
        r = subprocess.run(["git", "-C", cwd or ".", "diff", "--cached", "--name-only"],
                           capture_output=True, text=True)
        if r.returncode != 0:
            return []
        return [ln.strip() for ln in r.stdout.splitlines()
                if ln.strip().startswith("skills/omnitune/references/rubrics/")
                and ln.strip().endswith(".md")]
    except Exception:  # noqa: BLE001
        return []


def guard_rubric_write(payload):
    """Block a Write/Edit that loosens a rubric vs its committed version."""
    ti = payload.get("tool_input") or {}
    cwd = payload.get("cwd") or os.getcwd()
    rel = _rel_rubric(ti.get("file_path"), cwd)
    if not rel:
        return _allow()
    old = _git_show_head(rel, cwd)
    if old is None:
        return _allow()  # new rubric: no OLD to ratchet; first-commit gates cover it
    new = _new_text_for(payload, cwd, rel, old)
    if new is None:
        return _allow()
    verdict, findings = rubric_ratchet.ratchet(old, new, approved=_approved(cwd))
    if verdict == "BLOCK":
        return _deny("this edit loosens %s (%s). Rubrics are tighten-only; set %s=1 or "
                     "add %s after human review."
                     % (rel, "; ".join(findings[:3]), APPROVE_ENV, APPROVE_FILE))
    return _allow()


def _new_text_for(payload, cwd, rel, old):
    """Reconstruct the post-write text. Write -> content; Edit -> apply the single
    string replacement to OLD. Returns None if it can't be determined (fail-open)."""
    tool = payload.get("tool_name")
    ti = payload.get("tool_input") or {}
    if tool == "Write":
        return ti.get("content")
    if tool == "Edit":
        old_s, new_s = ti.get("old_string"), ti.get("new_string")
        if old_s is None or new_s is None:
            return None
        if ti.get("replace_all"):
            return old.replace(old_s, new_s)
        return old.replace(old_s, new_s, 1)
    return None


DISPATCH = {"self-commit": guard_self_commit, "rubric-write": guard_rubric_write}


def main(argv):
    if len(argv) < 2 or argv[1] not in DISPATCH:
        sys.stderr.write("usage: hook_guard.py {self-commit|rubric-write} < payload.json\n")
        return 0  # never block on our own misinvocation
    try:
        payload = json.load(sys.stdin)
    except Exception:  # noqa: BLE001 - a guard must not wedge a session on bad input
        return 0
    try:
        return DISPATCH[argv[1]](payload)
    except Exception:  # noqa: BLE001
        return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
