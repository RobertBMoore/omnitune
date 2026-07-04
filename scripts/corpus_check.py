#!/usr/bin/env python3
"""corpus_check — regression-corpus floor gate for gated self-apply.

Counts fixtures in the corpus dir; fails closed (exit 1) below the floor with the
verbatim SKILL reason so the verify path falls back to propose-only. --seed
optionally materializes fixtures from the saved-prompts dir. Dependency-free.

Run:  python3 scripts/corpus_check.py <regression_dir> [--floor N] [--prompts DIR] [--seed N]
"""
import json
import os
import shutil
import sys

FLOOR_DEFAULT = 5
UNDER_FLOOR_REASON = "cannot verify no-drift — manual review required"


def _fixtures(regression_dir):
    if not os.path.isdir(regression_dir):
        return []
    return sorted(f for f in os.listdir(regression_dir)
                  if f.endswith(".md") and f != "README.md")


def _candidates(prompts_dir, existing):
    if not prompts_dir or not os.path.isdir(prompts_dir):
        return []
    have = {os.path.splitext(f)[0] for f in existing}
    return sorted(f for f in os.listdir(prompts_dir)
                  if f.endswith(".md") and os.path.splitext(f)[0] not in have)


def floor(regression_dir, min_items=FLOOR_DEFAULT, prompts_dir=None):
    fx = _fixtures(regression_dir)
    ok = len(fx) >= min_items
    return {"count": len(fx), "floor": min_items, "ok": ok,
            "reason": "" if ok else UNDER_FLOOR_REASON,
            "seed_candidates": _candidates(prompts_dir, fx)}


def seed(regression_dir, prompts_dir, n):
    os.makedirs(regression_dir, exist_ok=True)
    written = []
    for name in _candidates(prompts_dir, _fixtures(regression_dir)):
        if len(written) >= n:
            break
        shutil.copyfile(os.path.join(prompts_dir, name),
                        os.path.join(regression_dir, name))
        written.append(name)
    return written


def _take(args, flag):
    if flag in args:
        i = args.index(flag)
        val = args[i + 1]
        del args[i:i + 2]
        return val
    return None


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    v = _take(args, "--floor")
    min_items = int(v) if v is not None else FLOOR_DEFAULT
    v = _take(args, "--prompts")
    prompts_dir = v if v is not None else "docs/prompts/"
    v = _take(args, "--seed")
    seed_n = int(v) if v is not None else 0
    if len(args) != 1:
        sys.stderr.write("usage: corpus_check.py <regression_dir> "
                         "[--floor N] [--prompts DIR] [--seed N]\n")
        return 2
    regression_dir = args[0]
    if seed_n:
        seed(regression_dir, prompts_dir, seed_n)
    res = floor(regression_dir, min_items=min_items, prompts_dir=prompts_dir)
    print(json.dumps(res, indent=2, sort_keys=True))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
