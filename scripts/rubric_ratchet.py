#!/usr/bin/env python3
"""rubric-ratchet — the tighten-only safety gate for omnitune self-apply.

Given an OLD rubric and a NEW (proposed) rubric, detect LOOSENING — changes that
weaken the standard: removed sections, fewer hard directives, severity
downgrades. A rubric patch may tighten unattended; any loosening is BLOCKED
unless a human explicitly approves it (--approve-loosening). This keeps the tool
from quietly grading itself easier. Dependency-free.

The gate is deliberately CONSERVATIVE: a flagged change is not necessarily a
true loosening (a reworded heading or consolidated rule can trip it), but a flag
means a human must confirm it isn't — exactly the bias a self-modifying rubric
needs.

Usage:
  python3 rubric_ratchet.py OLD.md NEW.md [--approve-loosening]
Exit 0 = ALLOW, 1 = BLOCK.
"""
import re
import sys

# Single-word hard directives (matched on word boundaries).
HARD_WORD_TOKENS = ["never", "prohibited", "required", "cannot"]
# Multi-word hard directives (substring counts).
HARD_PHRASE_TOKENS = ["must not", "do not", "fail-closed", "fail closed", "shall not"]
# Severity markers; a drop in count is a downgrade signal.
SEVERITY_TOKENS = ["critical", "high severity", "high-severity"]


def _count_word(text, token):
    return len(re.findall(r"\b" + re.escape(token) + r"\b", text.lower()))


def _count_sub(text, token):
    return text.lower().count(token)


def _headings(text):
    out = []
    for line in text.split("\n"):
        s = line.strip()
        if s.startswith("#"):
            out.append(s.lstrip("#").strip().lower())
    return out


def analyze(old_text, new_text):
    """Return a list of loosening findings (empty == no loosening detected)."""
    findings = []

    new_headings = set(_headings(new_text))
    for h in _headings(old_text):
        if h and h not in new_headings:
            findings.append("removed section: '%s'" % h)

    for tok in HARD_WORD_TOKENS:
        o, n = _count_word(old_text, tok), _count_word(new_text, tok)
        if n < o:
            findings.append("weakened: hard directive '%s' %d -> %d" % (tok, o, n))

    for tok in HARD_PHRASE_TOKENS:
        o, n = _count_sub(old_text, tok), _count_sub(new_text, tok)
        if n < o:
            findings.append("weakened: hard directive '%s' %d -> %d" % (tok, o, n))

    for tok in SEVERITY_TOKENS:
        o, n = _count_sub(old_text, tok), _count_sub(new_text, tok)
        if n < o:
            findings.append("severity downgrade: '%s' %d -> %d" % (tok, o, n))

    return findings


def ratchet(old_text, new_text, approved=False):
    """Return (verdict, findings). verdict in {ALLOW, BLOCK}."""
    findings = analyze(old_text, new_text)
    if not findings:
        return ("ALLOW", [])
    if approved:
        return ("ALLOW", findings)
    return ("BLOCK", findings)


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    if len(args) < 2:
        sys.stderr.write("usage: rubric_ratchet.py OLD.md NEW.md [--approve-loosening]\n")
        return 2
    approved = "--approve-loosening" in argv
    with open(args[0]) as f:
        old = f.read()
    with open(args[1]) as f:
        new = f.read()
    verdict, findings = ratchet(old, new, approved=approved)
    for x in findings:
        sys.stderr.write("  loosening: %s\n" % x)
    if verdict == "BLOCK":
        sys.stderr.write("rubric-ratchet: BLOCK — %d loosening(s); re-run with --approve-loosening after human review\n" % len(findings))
        return 1
    if findings:
        sys.stdout.write("rubric-ratchet: ALLOW (loosening approved by human; %d change(s) noted)\n" % len(findings))
    else:
        sys.stdout.write("rubric-ratchet: ALLOW (tighten-only; no loosening)\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
