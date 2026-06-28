#!/usr/bin/env python3
"""check-public-clean — fail if a tree contains client/company-sensitive content.

Generic patterns (secrets/PII) ship in this file. Real client terms are read from
an OPTIONAL gitignored denylist (scripts/.public-denylist.txt, one term per line,
'#' comments allowed) so they never appear in any public file.

Usage:
  python3 check_public_clean.py [ROOT] [--denylist PATH]
Exit 0 = clean, 1 = hits (printed to stderr).
"""
import os
import re
import sys

EXCLUDE_DIRS = {".git", "node_modules", "__pycache__"}
EXCLUDE_REL = {
    "docs/superpowers",                      # internal, not published
    "scripts/check_public_clean.py",         # this file (carries patterns)
    "scripts/test_check_public_clean.py",    # its test (carries fixtures)
    "scripts/.public-denylist.txt",          # private denylist (gitignored; carries the terms)
}
# Generic, always-on patterns (no client names hardcoded here).
GENERIC = [
    r"[A-Za-z0-9._%+-]+@digitalresearchgroup\.com",   # internal email addresses
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",            # private keys
    r"\bAKIA[0-9A-Z]{16}\b",                          # AWS access key id
    r"\bgh[pousr]_[A-Za-z0-9]{20,}\b",               # GitHub tokens
]
TEXT_EXT = {".md", ".markdown", ".txt", ".json", ".yaml", ".yml", ".py", ".html",
            ".js", ".ts", ".sh", ".toml", ".cfg", ".ini", ""}


def _excluded(rel):
    if any(part in EXCLUDE_DIRS for part in rel.split(os.sep)):
        return True
    return any(rel == e or rel.startswith(e + os.sep) for e in EXCLUDE_REL)


def load_denylist(path):
    terms = []
    if path and os.path.exists(path):
        with open(path) as f:
            for line in f:
                s = line.strip()
                if s and not s.startswith("#"):
                    terms.append(s)
    return terms


def scan(root, denylist):
    pats = [re.compile(p, re.I) for p in GENERIC]
    pats += [re.compile(re.escape(t), re.I) for t in denylist]
    hits = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root)
            if _excluded(rel):
                continue
            if os.path.splitext(fn)[1].lower() not in TEXT_EXT:
                continue
            try:
                with open(full, encoding="utf-8", errors="ignore") as f:
                    for i, line in enumerate(f, 1):
                        for p in pats:
                            m = p.search(line)
                            if m:
                                hits.append("%s:%d: %s" % (rel, i, m.group(0)))
            except OSError:
                continue
    return hits


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    root = args[0] if args else os.getcwd()
    dl = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".public-denylist.txt")
    if "--denylist" in argv:
        dl = argv[argv.index("--denylist") + 1]
    hits = scan(root, load_denylist(dl))
    if hits:
        sys.stderr.write("check-public-clean: %d sensitive hit(s):\n" % len(hits))
        for h in hits:
            sys.stderr.write("  - %s\n" % h)
        return 1
    sys.stdout.write("check-public-clean: OK (no sensitive content)\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
