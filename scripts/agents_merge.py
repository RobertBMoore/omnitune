#!/usr/bin/env python3
"""agents_merge — idempotent managed-block injection into an AGENTS.md.

Injects/updates omnitune's Codex block between fixed markers, never touching
content outside them, so a consumer's existing AGENTS.md is preserved. Pure,
dependency-free; atomic write. Generic — holds no provider/model nouns.
"""
import os
import tempfile

MARK_BEGIN = "<!-- omnitune:codex begin (managed — regenerate via .omnitune/scripts/agents_merge.py) -->"
MARK_END = "<!-- omnitune:codex end -->"


def merge(existing_text, block_text):
    """Return existing_text with the managed block inserted/updated. Pure + idempotent.
    Replaces the span between (and including) the markers if present; else appends."""
    wrapped = "%s\n%s\n%s" % (MARK_BEGIN, block_text.strip(), MARK_END)
    b = existing_text.find(MARK_BEGIN)
    e = existing_text.find(MARK_END)
    if b != -1 and e != -1 and e > b:
        return existing_text[:b] + wrapped + existing_text[e + len(MARK_END):]
    if existing_text.strip() == "":
        return wrapped + "\n"
    sep = "" if existing_text.endswith("\n") else "\n"
    return existing_text + sep + "\n" + wrapped + "\n"


def install(target_path, block_text):
    """Merge block_text into target_path (created if absent). Atomic write. Returns new text."""
    existing = ""
    if os.path.exists(target_path):
        with open(target_path, encoding="utf-8") as f:
            existing = f.read()
    new = merge(existing, block_text)
    d = os.path.dirname(os.path.abspath(target_path))
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".agents-merge.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(new)
        os.replace(tmp, target_path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    return new


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    target = args[args.index("--target") + 1] if "--target" in args else "AGENTS.md"
    block = (args[args.index("--block") + 1] if "--block" in args
             else os.path.join(".omnitune", "deploy", "codex", "AGENTS.omnitune.md"))
    with open(block, encoding="utf-8") as f:
        install(target, f.read())
    sys.stdout.write("agents_merge: updated %s (managed omnitune block)\n" % target)
