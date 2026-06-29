#!/usr/bin/env python3
"""version_log — committed, append-only lineage of omnitune rubric/model changes.

Records one entry per rubric add/update so "is this rubric current / where did it
come from?" is answerable, and (D5) the wiki can render it. Mirrors sync_state.py:
atomic write, tolerate-and-reset on corruption. Dependency-free.
"""
import json
import os
import tempfile

VALID_ACTIONS = {"add", "update", "deprecate"}


def _load(path):
    if not path or not os.path.exists(path):
        return {"schema": 1, "entries": []}
    try:
        with open(path) as f:
            d = json.load(f)
        if isinstance(d, dict) and isinstance(d.get("entries"), list):
            return d
    except Exception:  # noqa: BLE001 - a corrupt log must never block a run
        pass
    return {"schema": 1, "entries": []}


def _atomic_write(path, data):
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".version-log.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2, sort_keys=True)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def record(path, entry):
    """Append a lineage entry. Requires date, model_id, action (raises otherwise).
    Appends — never mutates prior entries."""
    if not isinstance(entry, dict):
        raise ValueError("entry must be a dict")
    for k in ("date", "model_id", "action"):
        if not entry.get(k):
            raise ValueError("entry requires '%s'" % k)
    if entry["action"] not in VALID_ACTIONS:
        raise ValueError("action must be one of %s" % sorted(VALID_ACTIONS))
    norm = {
        "date": str(entry["date"]),
        "model_id": str(entry["model_id"]),
        "provider": entry.get("provider", ""),
        "action": entry["action"],
        "last_synced": entry.get("last_synced", ""),
        "source_urls": list(entry.get("source_urls") or []),
        "outcome": entry.get("outcome", ""),
    }
    state = _load(path)
    state.setdefault("schema", 1)
    state["entries"].append(norm)
    _atomic_write(path, state)
    return state


def entries(path):
    """All lineage entries (oldest first), or [] on missing/corrupt."""
    return _load(path).get("entries", [])


def latest(path, model_id):
    """The most recently appended entry for model_id, or None."""
    found = None
    for e in entries(path):
        if e.get("model_id") == model_id:
            found = e
    return found


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 2:
        for e in entries(sys.argv[1]):
            print("%s  %-22s %-8s %s" % (e.get("date"), e.get("model_id"),
                                         e.get("action"), e.get("outcome")))
