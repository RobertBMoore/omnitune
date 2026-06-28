#!/usr/bin/env python3
"""sync_state — atomic, concurrency-safe handling for omnitune/.sync-state.json.

Hardens the model-sync decision state for repos that run parallel Claude
sessions (a documented hazard): atomic writes (temp + os.replace), per-session
keying into a map (no last-writer-wins clobber), and tolerate-and-reset on a
corrupt file so a half-written state never blocks a run. Snooze deadlines are
ISO-8601 instants compared as normalized strings; a malformed or missing
deadline is treated as expired (re-offer), never as "snoozed forever".
Dependency-free.
"""
import json
import os
import tempfile


def load_state(path):
    """Return the state map, or {} if missing/corrupt (tolerate-and-reset)."""
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path) as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:  # noqa: BLE001 - a corrupt state file must never crash a run
        return {}


def _atomic_write(path, data):
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".sync-state.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2, sort_keys=True)
        os.replace(tmp, path)  # atomic on POSIX + Windows
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def record(path, session_id, decision, model_seen=None, snooze_until=None):
    """Record a session's sync decision into the per-session map, atomically."""
    state = load_state(path)
    state[session_id] = {
        "decision": decision,
        "model_seen": model_seen,
        "snooze_until": snooze_until,
    }
    _atomic_write(path, state)
    return state


def _norm(ts):
    # Normalize an ISO-8601 instant for lexicographic comparison.
    if not isinstance(ts, str) or not ts:
        return None
    t = ts.strip().rstrip("Z")
    # Minimal validity check: must start YYYY-MM-DDTHH (fixed-width, comparable).
    if len(t) < 13 or t[4] != "-" or t[7] != "-" or t[10] != "T":
        return None
    return t


def is_snoozed(state, session_id, now_iso):
    """True iff the session has a valid future snooze deadline."""
    entry = state.get(session_id) if isinstance(state, dict) else None
    if not entry:
        return False
    deadline = _norm(entry.get("snooze_until"))
    now = _norm(now_iso)
    if deadline is None or now is None:
        return False
    return now < deadline


if __name__ == "__main__":
    import sys
    # tiny CLI: sync_state.py PATH SESSION DECISION [snooze_until]
    a = sys.argv
    if len(a) < 4:
        sys.stderr.write("usage: sync_state.py PATH SESSION DECISION [snooze_until_iso]\n")
        sys.exit(2)
    record(a[1], a[2], a[3], snooze_until=a[4] if len(a) > 4 else None)
    sys.stdout.write("recorded %s -> %s\n" % (a[2], a[3]))
