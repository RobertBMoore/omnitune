#!/usr/bin/env python3
"""ratchet-gate — run the tighten-only ratchet on every changed rubric in a diff.

CI/local wrapper around rubric_ratchet: for each rubric under
skills/omnitune/references/rubrics/**.md that differs from a git BASE ref, diff
the BASE version against the working-tree version and BLOCK on any loosening
(removed section, fewer hard directives, severity downgrade). A brand-new rubric
(absent at BASE) has no OLD to ratchet against and is skipped here — the
citation/floor gates in tuner_check cover a first commit; the ratchet applies to
every FUTURE edit. A loosening is allowed only with --approve-loosening, which
mirrors rubric_ratchet's human-in-the-loop escape hatch.

Usage:
  python3 ratchet_gate.py [--base REF] [--approve-loosening] [REPO_ROOT]
Exit 0 = all changed rubrics tighten-only (or none changed), 1 = a loosening was
blocked, 2 = git unavailable / bad invocation.
"""
import os
import subprocess
import sys

import rubric_ratchet

RUBRIC_PREFIX = "skills/omnitune/references/rubrics/"


def _git(args, root):
    return subprocess.run(["git", "-C", root] + args,
                          capture_output=True, text=True)


def _changed_rubrics(base, root):
    """Rubric paths that differ between BASE and the working tree."""
    r = _git(["diff", "--name-only", base, "--"], root)
    if r.returncode != 0:
        return None
    out = []
    for line in r.stdout.splitlines():
        p = line.strip()
        if p.startswith(RUBRIC_PREFIX) and p.endswith(".md"):
            out.append(p)
    return out


def _base_text(base, path, root):
    """The rubric's content at BASE, or None if it did not exist there."""
    r = _git(["show", "%s:%s" % (base, path)], root)
    return r.stdout if r.returncode == 0 else None


def gate(base, root, approved=False):
    """Return (exit_code, report_lines)."""
    changed = _changed_rubrics(base, root)
    if changed is None:
        return (2, ["ratchet-gate: could not diff against base '%s' (git error)" % base])
    lines, blocked = [], 0
    for path in changed:
        old = _base_text(base, path, root)
        if old is None:
            lines.append("ratchet-gate: new rubric (no base) — skipped: %s" % path)
            continue
        try:
            with open(os.path.join(root, path), encoding="utf-8") as f:
                new = f.read()
        except FileNotFoundError:
            lines.append("ratchet-gate: deleted rubric — %s (review manually)" % path)
            blocked += 1
            continue
        verdict, findings = rubric_ratchet.ratchet(old, new, approved=approved)
        if verdict == "BLOCK":
            blocked += 1
            lines.append("ratchet-gate: BLOCK %s" % path)
            lines.extend("    loosening: %s" % x for x in findings)
        elif findings:
            lines.append("ratchet-gate: ALLOW (loosening approved) %s" % path)
        else:
            lines.append("ratchet-gate: ok (tighten-only) %s" % path)
    if not changed:
        lines.append("ratchet-gate: no rubric changes vs '%s'" % base)
    return (1 if blocked else 0, lines)


def main(argv):
    flags = [a for a in argv[1:] if a.startswith("--")]
    pos = [a for a in argv[1:] if not a.startswith("--")]
    base = "origin/main"
    if "--base" in argv:
        i = argv.index("--base")
        if i + 1 >= len(argv):
            sys.stderr.write("ratchet-gate: --base needs a ref\n")
            return 2
        base = argv[i + 1]
        pos = [a for a in pos if a != base]
    approved = "--approve-loosening" in flags
    root = pos[0] if pos else "."
    code, lines = gate(base, root, approved=approved)
    stream = sys.stderr if code else sys.stdout
    for ln in lines:
        stream.write(ln + "\n")
    if code == 1:
        sys.stderr.write("ratchet-gate: BLOCK — a rubric loosened; re-run with "
                         "--approve-loosening after human review\n")
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
