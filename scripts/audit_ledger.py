#!/usr/bin/env python3
"""audit_ledger — deterministic convergence tracker for omnitune's iterated rubric audit.

Append-only event log (round events + status events). The agent supplies judgment
(which findings exist, their severity, their resolution); this helper computes when
the iterated panel has CONVERGED, so the agent cannot declare its own audit finished.
Mirrors sync_state.py: atomic write, tolerate-and-reset on a corrupt file.
convergence() never raises. Dependency-free.
"""
import json
import os
import re
import tempfile

SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}
VALID_STATUS = {"open", "reconciled", "declined"}


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").strip().lower()).strip("-") or "x"


def fingerprint(category, location):
    """Deterministic, parent-computed key so the same defect always collides."""
    return "%s:%s" % (_slug(category), _slug(location))


def _load(path):
    if not path or not os.path.exists(path):
        return {"events": []}
    try:
        with open(path) as f:
            d = json.load(f)
        if isinstance(d, dict) and isinstance(d.get("events"), list):
            return d
    except Exception:  # noqa: BLE001 - a corrupt ledger must never block a run
        pass
    return {"events": []}


def _atomic_write(path, data):
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".audit-ledger.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2, sort_keys=True)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def reset(path):
    """Start a fresh ledger for a derivation run."""
    state = {"events": []}
    _atomic_write(path, state)
    return state


def _append(path, event):
    state = _load(path)
    event["seq"] = len(state["events"])
    state["events"].append(event)
    _atomic_write(path, state)
    return state


def _round_events(state):
    return [e for e in state["events"] if e.get("type") == "round"]


def record_round(path, round_no, reviews, author_id=None, min_reviews=2):
    """Append a round event. round_no must strictly increase (raises otherwise).
    `complete` iff >= min_reviews distinct reviewers and the author is not among them.
    Unknown severities coerce to 'low'."""
    state = _load(path)
    prev = max((r.get("round_no", 0) for r in _round_events(state)), default=0)
    if not isinstance(round_no, int) or round_no <= prev:
        raise ValueError("round_no must be an int greater than %d" % prev)
    norm, ids = [], []
    for rv in reviews or []:
        rid = rv.get("reviewer_id")
        ids.append(rid)
        findings = []
        for fnd in rv.get("findings") or []:
            sev = str(fnd.get("severity", "low")).strip().lower()
            if sev not in SEVERITY_RANK:
                sev = "low"
            findings.append({"fingerprint": fnd.get("fingerprint"),
                             "severity": sev, "summary": fnd.get("summary", "")})
        norm.append({"reviewer_id": rid, "lens": rv.get("lens"), "findings": findings})
    distinct = set(i for i in ids if i)
    complete = len(distinct) >= min_reviews and author_id not in distinct
    return _append(path, {"type": "round", "round_no": round_no,
                          "complete": bool(complete), "reviews": norm})


def set_status(path, fp, status, reason=""):
    """Append a status event. reconciled/declined require a non-empty reason."""
    status = str(status).strip().lower()
    if status not in VALID_STATUS:
        raise ValueError("status must be one of %s" % sorted(VALID_STATUS))
    if status in ("reconciled", "declined") and not (reason or "").strip():
        raise ValueError("%s requires a written reason" % status)
    return _append(path, {"type": "status", "fingerprint": fp,
                          "status": status, "reason": reason or ""})


def _rank(sev):
    return SEVERITY_RANK.get(str(sev).strip().lower(), 0)


def convergence(path, clean_rounds=2, cap=3, material="high"):
    """Compute the audit verdict. Never raises."""
    try:
        clean_rounds = max(1, int(clean_rounds))
        cap = max(clean_rounds, int(cap))
        mrank = SEVERITY_RANK.get(str(material).strip().lower(), 2)
        events = _load(path)["events"]
        rounds = [e for e in events if e.get("type") == "round"]

        first_material_round, ever_material = {}, set()
        for e in rounds:
            rno = e.get("round_no")
            for rv in e.get("reviews") or []:
                for f in rv.get("findings") or []:
                    fp = f.get("fingerprint")
                    if fp is None or _rank(f.get("severity")) < mrank:
                        continue
                    ever_material.add(fp)
                    first_material_round.setdefault(fp, rno)

        current_status = {}
        for e in events:
            if e.get("type") == "status":
                current_status[e.get("fingerprint")] = e.get("status")

        open_material = sorted(fp for fp in ever_material
                               if current_status.get(fp, "open") == "open")
        declined_material = sorted(fp for fp in ever_material
                                   if current_status.get(fp) == "declined")

        trailing = 0
        for e in reversed(rounds):
            new_material = sum(1 for fp, r in first_material_round.items()
                               if r == e.get("round_no"))
            if e.get("complete") and new_material == 0:
                trailing += 1
            else:
                break

        total = len(rounds)
        if total == 0:
            verdict = "NOT_CONVERGED"
        elif trailing >= clean_rounds and not open_material:
            verdict = "CONVERGED"
        elif total >= cap:
            verdict = "CAP_EXCEEDED"
        else:
            verdict = "NOT_CONVERGED"
        return {"verdict": verdict, "trailing_clean": trailing, "rounds": total,
                "open_material": open_material, "declined_material": declined_material}
    except Exception as e:  # noqa: BLE001 - convergence must never raise
        return {"verdict": "NOT_CONVERGED", "trailing_clean": 0, "rounds": 0,
                "open_material": [], "declined_material": [], "error": str(e)}
