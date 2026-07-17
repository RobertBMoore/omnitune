#!/usr/bin/env python3
"""record_check — blocking record-discipline gate for an orchestration pack.

Run before every integration merge and every milestone tag. Compares the
recorded state (the progress file, verification/, audits/, git tags) against
git reality and fails when the record has decayed. A red gate halts the loop
step that invoked it: the merge or tag does not proceed until every FAIL line
carries a committed one-line disposition (product defect / stale harness /
fixture gap).

Checks (any FAIL -> exit 1):
  C1  uncommitted files under verification/ or audits/
  C2  a milestone tag without a filed per-auditor audit report (proportional to
      the scale tier: program = every tag; squad = user-facing milestones only;
      solo-pair = none, satisfied by the gate battery)
  C3  CURRENT-block HEAD SHA missing or != git HEAD
  C4  MILESTONES table disagrees with git tags
  C5  a closed milestone with no LOG entry
  C6  CURRENT block over its line cap
  C7  any state-file line over the line-length cap
Warnings (reported, never block):
  W1  unpushed main or tags
  W2  undeleted merged milestone branches

Stdlib-only. Adapt to the repo via CONFIG below.
Usage: python3 record_check.py [REPO_ROOT]
"""
import os
import re
import subprocess
import sys

CONFIG = {
    "progress_file": "PROGRESS.md",
    "state_files": ["PROGRESS.md", "DECISIONS.md", "BACKLOG.md"],
    "evidence_dirs": ["verification", "audits"],
    "audits_dir": "audits",
    "tag_prefix": "milestone/",
    # Auditor names required per milestone tag (audits/<M>-<auditor>.md each).
    # Empty list = require at least one audits/<M>-*.md per tag.
    "auditors": [],
    # Scale tier — makes C2 (audit-per-tag) proportional to team scale:
    #   "program"   every tag requires an audit report (the current contract);
    #   "squad"     only tags whose milestone id is in user_facing_milestones;
    #   "solo-pair" no tag requires an audit — the gate battery (lint/test/e2e
    #               green at HEAD) satisfies the requirement when no auditor role
    #               exists. Absent/unknown value behaves as "program".
    "tier": "program",
    "user_facing_milestones": [],  # milestone ids (e.g. ["M2", "M4"]) — squad tier
    "closed_statuses": {"done", "closed", "complete", "merged", "shipped", "tagged"},
    "current_heading": "## CURRENT",
    "milestones_heading": "## MILESTONES",
    "log_heading": "## LOG",
    "current_max_lines": 25,
    "line_max_chars": 500,
    "main_branch": "main",
    "milestone_branch_re": r"^m\d+(\.\d+)?-",
}


def _git(root, *args):
    try:
        p = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
        return p.returncode, p.stdout.strip()
    except OSError as e:
        return 1, str(e)


def _section(text, heading):
    """Body of a '## X' section: lines after `heading` up to the next '## '."""
    lines = text.splitlines()
    out, active = [], False
    for ln in lines:
        if ln.strip().lower() == heading.strip().lower() or \
           ln.strip().lower().startswith(heading.strip().lower() + " "):
            active = True
            continue
        if active and ln.startswith("## "):
            break
        if active:
            out.append(ln)
    return out if active else None


def _milestone_rows(section_lines):
    """Parse `| M | Status | Tag | Evidence |` rows -> [(m, status, tag)]."""
    rows = []
    for ln in section_lines or []:
        s = ln.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 3 or not cells[0] or cells[0].lower() in ("m", "milestone") \
           or set(cells[0]) <= {"-", ":", " "}:
            continue
        tag = cells[2] if cells[2] not in ("-", "") else ""
        rows.append((cells[0], cells[1].lower(), tag))
    return rows


def run_checks(root):
    fails, warns = [], []
    cfg = CONFIG

    rc, head = _git(root, "rev-parse", "HEAD")
    if rc != 0:
        return ["C3: not a git repository (or git unavailable): %s" % head], warns

    # C1 — uncommitted evidence
    rc, status = _git(root, "status", "--porcelain", "--", *cfg["evidence_dirs"])
    for ln in (status.splitlines() if rc == 0 else []):
        fails.append("C1: uncommitted evidence: %s" % ln.strip())

    # Milestone tags
    rc, tag_out = _git(root, "tag", "--list", cfg["tag_prefix"] + "*")
    tags = [t for t in tag_out.splitlines() if t.strip()] if rc == 0 else []

    # C2 — per-auditor audit report per milestone tag, proportional to tier
    tier = str(cfg.get("tier", "program")).lower()
    user_facing = {m.lower() for m in cfg.get("user_facing_milestones", [])}
    audits_dir = os.path.join(root, cfg["audits_dir"])
    filed = ([f for f in os.listdir(audits_dir)
              if os.path.isfile(os.path.join(audits_dir, f))]
             if os.path.isdir(audits_dir) else [])
    for tag in tags:
        mid = tag[len(cfg["tag_prefix"]):]
        # solo-pair: the gate battery satisfies the audit requirement — no file
        # is gated. squad: only user-facing/risky milestones require an audit.
        if tier == "solo-pair":
            continue
        if tier == "squad" and mid.lower() not in user_facing:
            continue
        if cfg["auditors"]:
            for auditor in cfg["auditors"]:
                want = "%s-%s.md" % (mid, auditor)
                if not any(f.lower() == want.lower() for f in filed):
                    fails.append("C2: tag %s has no filed report %s/%s" %
                                 (tag, cfg["audits_dir"], want))
        else:
            pat = re.compile(re.escape(mid) + r"-.+\.md$", re.I)
            if not any(pat.match(f) for f in filed):
                fails.append("C2: tag %s has no filed audit report %s/%s-<auditor>.md" %
                             (tag, cfg["audits_dir"], mid))

    # Progress-file checks (C3-C6)
    progress_path = os.path.join(root, cfg["progress_file"])
    if not os.path.exists(progress_path):
        fails.append("C3: %s not found — no recorded state to check" % cfg["progress_file"])
        rows = []
    else:
        with open(progress_path, encoding="utf-8") as f:
            text = f.read()
        current = _section(text, cfg["current_heading"])
        milestones = _section(text, cfg["milestones_heading"])
        log = _section(text, cfg["log_heading"])
        rows = _milestone_rows(milestones)

        # C3 — CURRENT HEAD SHA matches git HEAD
        if current is None:
            fails.append("C3: no %s section in %s" % (cfg["current_heading"], cfg["progress_file"]))
        else:
            m = re.search(r"HEAD\b[:\s|]*([0-9a-fA-F]{7,40})", "\n".join(current))
            if not m:
                fails.append("C3: CURRENT block carries no HEAD SHA")
            elif not head.lower().startswith(m.group(1).lower()):
                fails.append("C3: CURRENT HEAD %s != git HEAD %s" % (m.group(1), head[:12]))

        # C4 — MILESTONES table vs git tags
        if milestones is None:
            fails.append("C4: no %s section in %s" % (cfg["milestones_heading"], cfg["progress_file"]))
        else:
            for mid, status, tag in rows:
                closed = status in cfg["closed_statuses"]
                if closed and not tag:
                    fails.append("C4: milestone %s is '%s' but its row lists no tag" % (mid, status))
                if tag and tag not in tags:
                    fails.append("C4: milestone %s lists tag %s which does not exist in git" % (mid, tag))
            by_id = {mid.lower(): status for mid, status, _ in rows}
            for tag in tags:
                mid = tag[len(cfg["tag_prefix"]):]
                status = by_id.get(mid.lower())
                if status is None:
                    fails.append("C4: git tag %s has no MILESTONES row" % tag)
                elif status not in cfg["closed_statuses"]:
                    fails.append("C4: git tag %s exists but row %s says '%s'" % (tag, mid, status))

        # C5 — closed milestone has a LOG entry
        if log is None:
            fails.append("C5: no %s section in %s" % (cfg["log_heading"], cfg["progress_file"]))
        else:
            log_text = "\n".join(log).lower()
            for mid, status, _ in rows:
                if status in cfg["closed_statuses"] and \
                   not re.search(r"\b%s\b" % re.escape(mid.lower()), log_text):
                    fails.append("C5: closed milestone %s has no LOG entry" % mid)

        # C6 — CURRENT line cap
        if current is not None:
            n = len([ln for ln in current if ln.strip()])
            if n > cfg["current_max_lines"]:
                fails.append("C6: CURRENT block is %d lines (cap %d)" % (n, cfg["current_max_lines"]))

    # C7 — state-file line-length cap
    for name in cfg["state_files"]:
        path = os.path.join(root, name)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            for i, ln in enumerate(f, 1):
                if len(ln.rstrip("\n")) > cfg["line_max_chars"]:
                    fails.append("C7: %s:%d is %d chars (cap %d)" %
                                 (name, i, len(ln.rstrip("\n")), cfg["line_max_chars"]))

    # W1 — unpushed main / tags
    main = cfg["main_branch"]
    rc, _ = _git(root, "rev-parse", "--verify", "origin/%s" % main)
    if rc != 0:
        warns.append("W1: no origin/%s ref — cannot verify push state" % main)
    else:
        rc, count = _git(root, "rev-list", "--count", "origin/%s..%s" % (main, main))
        if rc == 0 and count.isdigit() and int(count) > 0:
            warns.append("W1: %s commit(s) on %s not pushed to origin/%s" % (count, main, main))
        for tag in tags:
            rc, _ = _git(root, "merge-base", "--is-ancestor", tag, "origin/%s" % main)
            if rc != 0:
                warns.append("W1: tag %s not reachable from origin/%s (push tags)" % (tag, main))

    # W2 — undeleted merged milestone branches
    rc, merged = _git(root, "branch", "--merged", main, "--format=%(refname:short)")
    if rc == 0:
        pat = re.compile(cfg["milestone_branch_re"])
        for br in merged.splitlines():
            if pat.match(br.strip()):
                warns.append("W2: merged milestone branch not deleted: %s" % br.strip())

    return fails, warns


def main(argv):
    if any(a in ("-h", "--help") for a in argv[1:]):
        print(__doc__)
        return 0
    root = os.path.abspath(argv[1]) if len(argv) > 1 else os.getcwd()
    fails, warns = run_checks(root)
    for w in warns:
        print("WARN %s" % w)
    for f in fails:
        print("FAIL %s" % f)
    print("record_check: %d fail(s), %d warning(s)" % (len(fails), len(warns)))
    if fails:
        print("red gate: do not merge or tag until every FAIL line carries a committed "
              "one-line disposition (product defect / stale harness / fixture gap)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
