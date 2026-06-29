# Iterated Independent-Audit Gate — D3 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an iterated, author-independent audit loop on rubric changes whose *termination* is computed by a deterministic, append-only ledger (`audit_ledger.py`) — the agent supplies findings; the helper decides CONVERGED — in front of omnitune's existing ratchet/corpus/human-commit gates.

**Architecture:** A dependency-free `scripts/audit_ledger.py` records an append-only event log (round events + status events) and computes a CONVERGED / NOT_CONVERGED / CAP_EXCEEDED verdict; the agent can add judgment but cannot rewrite it. `tuner_check.py` gains blocking validation of the new `model_sync.audit_*` config keys. The `sync/SKILL.md` protocol gains a change-magnitude cheap-path, a capability probe (no independent dispatch → propose-only), and the iterated panel loop that feeds the ledger.

**Tech Stack:** Python 3 stdlib only (`json`, `os`, `re`, `tempfile`, `unittest`); Markdown skills. Tests are `unittest`, run from `scripts/` via `python3 -m unittest <module>`.

**Spec:** `docs/superpowers/specs/2026-06-29-iterated-audit-gate-design.md`

**Out of scope:** the pre-build plan audit; the version log (D4); doc pages (D5); any change to `rubric_ratchet.py`, the regression corpus, or two-key model confirmation.

---

## Task 0: Branch + baseline

- [ ] **Step 1: Branch**
```bash
cd <repo-root>
git checkout main && git checkout -b feat/iterated-audit-gate
```
Expected: `Switched to a new branch 'feat/iterated-audit-gate'`

- [ ] **Step 2: Green baseline**
```bash
cd <repo-root>/scripts
python3 -m unittest test_tuner_check test_rubric_ratchet test_sync_state test_validate_plugin test_check_public_clean test_resolve_model test_detect_model
```
Expected: `OK` (90 tests). If red, stop.

---

## Task 1: `scripts/audit_ledger.py` + tests

**Files:** Create `scripts/audit_ledger.py`, `scripts/test_audit_ledger.py`; Modify `.github/workflows/validate.yml`.

- [ ] **Step 1: Write the failing tests** — create `scripts/test_audit_ledger.py`:

```python
import json
import os
import tempfile
import unittest

import audit_ledger as al


def _ledger(tmp):
    return os.path.join(tmp, "omnitune", ".audit-ledger-test.json")


def _review(rid, lens, findings):
    return {"reviewer_id": rid, "lens": lens, "findings": findings}


def _f(fp, severity, summary="x"):
    return {"fingerprint": fp, "severity": severity, "summary": summary}


class TestFingerprint(unittest.TestCase):
    def test_deterministic_slug(self):
        self.assertEqual(al.fingerprint("Safety", "Audit Floor"), "safety:audit-floor")

    def test_same_defect_collides(self):
        self.assertEqual(al.fingerprint("safety", "audit-floor"),
                         al.fingerprint("  SAFETY ", "audit_floor"))

    def test_empty_parts(self):
        self.assertEqual(al.fingerprint("", ""), "x:x")


class TestRecordAndStatus(unittest.TestCase):
    def test_round_monotonic_raises(self):
        with tempfile.TemporaryDirectory() as t:
            p = _ledger(t)
            al.record_round(p, 1, [_review("a", "x", []), _review("b", "y", [])])
            with self.assertRaises(ValueError):
                al.record_round(p, 1, [_review("a", "x", []), _review("b", "y", [])])

    def test_incomplete_round_when_too_few_reviewers(self):
        with tempfile.TemporaryDirectory() as t:
            p = _ledger(t)
            al.record_round(p, 1, [_review("a", "x", [])])  # 1 reviewer < min 2
            rounds = [e for e in al._load(p)["events"] if e["type"] == "round"]
            self.assertFalse(rounds[0]["complete"])

    def test_author_as_reviewer_makes_incomplete(self):
        with tempfile.TemporaryDirectory() as t:
            p = _ledger(t)
            al.record_round(p, 1, [_review("author", "x", []), _review("b", "y", [])],
                            author_id="author")
            rounds = [e for e in al._load(p)["events"] if e["type"] == "round"]
            self.assertFalse(rounds[0]["complete"])

    def test_unknown_severity_coerced_low(self):
        with tempfile.TemporaryDirectory() as t:
            p = _ledger(t)
            al.record_round(p, 1, [_review("a", "x", [_f("c:l", "bogus")]),
                                   _review("b", "y", [])])
            ev = [e for e in al._load(p)["events"] if e["type"] == "round"][0]
            self.assertEqual(ev["reviews"][0]["findings"][0]["severity"], "low")

    def test_set_status_requires_reason(self):
        with tempfile.TemporaryDirectory() as t:
            p = _ledger(t)
            with self.assertRaises(ValueError):
                al.set_status(p, "safety:x", "reconciled", "")
            al.set_status(p, "safety:x", "reconciled", "fixed it")  # ok with reason

    def test_set_status_bad_status_raises(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ValueError):
                al.set_status(_ledger(t), "safety:x", "bogus", "r")

    def test_reset_clears(self):
        with tempfile.TemporaryDirectory() as t:
            p = _ledger(t)
            al.record_round(p, 1, [_review("a", "x", []), _review("b", "y", [])])
            al.reset(p)
            self.assertEqual(al._load(p)["events"], [])

    def test_corrupt_ledger_tolerated(self):
        with tempfile.TemporaryDirectory() as t:
            p = _ledger(t)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w") as f:
                f.write("{not json")
            self.assertEqual(al._load(p)["events"], [])  # tolerate-and-reset


class TestConvergence(unittest.TestCase):
    def _two(self, fp_findings_a, fp_findings_b=None):
        return [_review("ra", "correctness", fp_findings_a),
                _review("rb", "safety", fp_findings_b or [])]

    def test_empty_ledger_not_converged(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(al.convergence(_ledger(t))["verdict"], "NOT_CONVERGED")

    def test_clean_from_start_converges_at_round_2(self):
        with tempfile.TemporaryDirectory() as t:
            p = _ledger(t)
            al.record_round(p, 1, self._two([]))
            al.record_round(p, 2, self._two([]))
            r = al.convergence(p)
            self.assertEqual(r["verdict"], "CONVERGED")
            self.assertEqual(r["trailing_clean"], 2)

    def test_one_reconcile_converges_at_round_3(self):
        with tempfile.TemporaryDirectory() as t:
            p = _ledger(t)
            al.record_round(p, 1, self._two([], [_f("safety:audit-floor", "critical")]))
            al.set_status(p, "safety:audit-floor", "reconciled", "restored floor-rule")
            al.record_round(p, 2, self._two([]))
            self.assertEqual(al.convergence(p)["verdict"], "NOT_CONVERGED")
            al.record_round(p, 3, self._two([]))
            r = al.convergence(p)
            self.assertEqual(r["verdict"], "CONVERGED")
            self.assertEqual(r["open_material"], [])

    def test_persistent_open_never_converges_hits_cap(self):
        with tempfile.TemporaryDirectory() as t:
            p = _ledger(t)
            for n in (1, 2, 3):
                al.record_round(p, n, self._two([], [_f("safety:hole", "critical")]))
            r = al.convergence(p)
            self.assertEqual(r["verdict"], "CAP_EXCEEDED")
            self.assertIn("safety:hole", r["open_material"])

    def test_open_material_blocks_convergence(self):
        with tempfile.TemporaryDirectory() as t:
            p = _ledger(t)
            al.record_round(p, 1, self._two([], [_f("safety:hole", "high")]))
            al.record_round(p, 2, self._two([]))
            al.record_round(p, 3, self._two([]))
            # never reconciled -> open_material non-empty -> CAP_EXCEEDED, not CONVERGED
            self.assertEqual(al.convergence(p)["verdict"], "CAP_EXCEEDED")

    def test_declined_counts_resolved_and_surfaced(self):
        with tempfile.TemporaryDirectory() as t:
            p = _ledger(t)
            al.record_round(p, 1, self._two([], [_f("domain:nit", "high")]))
            al.set_status(p, "domain:nit", "declined", "not applicable to gpt-5.5")
            al.record_round(p, 2, self._two([]))
            al.record_round(p, 3, self._two([]))
            r = al.convergence(p)
            self.assertEqual(r["verdict"], "CONVERGED")
            self.assertIn("domain:nit", r["declined_material"])

    def test_low_medium_ignored_for_material_high(self):
        with tempfile.TemporaryDirectory() as t:
            p = _ledger(t)
            al.record_round(p, 1, self._two([_f("structure:x", "medium")]))
            al.record_round(p, 2, self._two([_f("structure:y", "low")]))
            # no material (high+) findings, never reconciled -> still converges
            self.assertEqual(al.convergence(p)["verdict"], "CONVERGED")

    def test_incomplete_round_not_clean(self):
        with tempfile.TemporaryDirectory() as t:
            p = _ledger(t)
            al.record_round(p, 1, [_review("a", "x", [])])  # incomplete
            al.record_round(p, 2, [_review("a", "x", [])])  # incomplete
            self.assertNotEqual(al.convergence(p)["verdict"], "CONVERGED")

    def test_clean_rounds_clamped_to_at_least_one(self):
        with tempfile.TemporaryDirectory() as t:
            # clamp prevents the degenerate "empty ledger converges" verdict
            self.assertEqual(al.convergence(_ledger(t), clean_rounds=0)["verdict"],
                             "NOT_CONVERGED")

    def test_convergence_never_raises_on_garbage(self):
        with tempfile.TemporaryDirectory() as t:
            p = _ledger(t)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w") as f:
                f.write("[]")  # wrong shape
            r = al.convergence(p)
            self.assertEqual(r["verdict"], "NOT_CONVERGED")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run to verify failure**

Run: `cd <repo-root>/scripts && python3 -m unittest test_audit_ledger -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'audit_ledger'`.

- [ ] **Step 3: Create `scripts/audit_ledger.py`:**

```python
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
```

- [ ] **Step 4: Run to verify pass**

Run: `cd <repo-root>/scripts && python3 -m unittest test_audit_ledger -v`
Expected: PASS (all tests).

- [ ] **Step 5: Register in CI** — edit `.github/workflows/validate.yml` line 18, append ` test_audit_ledger`:
```yaml
        run: python3 -m unittest test_tuner_check test_rubric_ratchet test_sync_state test_validate_plugin test_check_public_clean test_resolve_model test_detect_model test_audit_ledger
```

- [ ] **Step 6: Commit**
```bash
cd <repo-root>
git add scripts/audit_ledger.py scripts/test_audit_ledger.py .github/workflows/validate.yml
git commit -m "feat(audit-gate): deterministic append-only convergence ledger"
```

---

## Task 2: Blocking config validation in `tuner_check.py`

**Files:** Modify `scripts/tuner_check.py`, `scripts/test_tuner_check.py`.

- [ ] **Step 1: Write the failing tests** — append to `scripts/test_tuner_check.py` (it already imports `unittest`; add the import + class):

```python
from tuner_check import _audit_config_problems


class TestAuditConfig(unittest.TestCase):
    def test_valid_audit_keys_ok(self):
        cfg = {"model_sync": {"audit_clean_rounds": 2, "audit_round_cap": 3,
                              "audit_material_severity": "high", "audit_panel_threshold": 3}}
        self.assertEqual(_audit_config_problems(cfg), [])

    def test_absent_keys_ok(self):
        self.assertEqual(_audit_config_problems({"model_sync": {"channel": "badge"}}), [])

    def test_clean_rounds_below_one(self):
        probs = _audit_config_problems({"model_sync": {"audit_clean_rounds": 0}})
        self.assertTrue(any("audit_clean_rounds" in p for p in probs), probs)

    def test_cap_below_clean_rounds(self):
        probs = _audit_config_problems({"model_sync": {"audit_clean_rounds": 3,
                                                       "audit_round_cap": 2}})
        self.assertTrue(any("audit_round_cap" in p for p in probs), probs)

    def test_material_too_strict(self):
        probs = _audit_config_problems({"model_sync": {"audit_material_severity": "critical"}})
        self.assertTrue(any("audit_material_severity" in p for p in probs), probs)

    def test_non_integer(self):
        probs = _audit_config_problems({"model_sync": {"audit_round_cap": "three"}})
        self.assertTrue(any("audit_round_cap" in p for p in probs), probs)
```

- [ ] **Step 2: Run to verify failure**

Run: `cd <repo-root>/scripts && python3 -m unittest test_tuner_check -v`
Expected: FAIL — `ImportError: cannot import name '_audit_config_problems'`.

- [ ] **Step 3: Add `_audit_config_problems` to `scripts/tuner_check.py`** (place it above `def check(`), and wire it in:

```python
def _audit_config_problems(cfg):
    """Validate model_sync.audit_* keys (blocking). Returns problem strings."""
    out = []
    ms = cfg.get("model_sync") if isinstance(cfg, dict) else None
    if not isinstance(ms, dict):
        return out

    def _as_int(key):
        v = ms.get(key)
        if v in (None, ""):
            return None
        try:
            return int(str(v).strip())
        except Exception:  # noqa: BLE001
            out.append("model_sync.%s must be an integer" % key)
            return None

    cr = _as_int("audit_clean_rounds")
    cap = _as_int("audit_round_cap")
    th = _as_int("audit_panel_threshold")
    if cr is not None and cr < 1:
        out.append("model_sync.audit_clean_rounds must be >= 1")
    if cap is not None and cap < (cr if cr is not None else 2):
        out.append("model_sync.audit_round_cap must be >= audit_clean_rounds")
    if th is not None and th < 0:
        out.append("model_sync.audit_panel_threshold must be >= 0")
    sev = ms.get("audit_material_severity")
    if sev not in (None, ""):
        ranks = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        s = str(sev).strip().lower()
        if s not in ranks:
            out.append("model_sync.audit_material_severity must be low|medium|high|critical")
        elif ranks[s] > ranks["high"]:
            out.append("model_sync.audit_material_severity must not be stricter than "
                       "'high' (loosening the audit needs explicit human sign-off)")
    return out
```

Then, inside `check(...)`, immediately after the `model_sync.channel` validation block (the `if ch and ch not in VALID_CHANNELS:` lines), add:
```python
    problems.extend(_audit_config_problems(cfg))
```

- [ ] **Step 4: Run to verify pass + real config still clean**
```bash
cd <repo-root>/scripts && python3 -m unittest test_tuner_check -v 2>&1 | tail -3
cd <repo-root> && python3 scripts/tuner_check.py .
```
Expected: tests PASS; `tuner-check: OK` (the real config has no `audit_*` keys, so the new check is a no-op there).

- [ ] **Step 5: Commit**
```bash
cd <repo-root>
git add scripts/tuner_check.py scripts/test_tuner_check.py
git commit -m "feat(audit-gate): blocking validation of model_sync.audit_* config keys"
```

---

## Task 3: Gitignore the ledger

**Files:** Modify `.gitignore`.

- [ ] **Step 1: Confirm the namespace**
```bash
cd <repo-root> && grep -n "sync-state\|model-usage" .gitignore
```
Expected: shows the existing `omnitune/.sync-state.json` / `omnitune/.model-usage.json` ignores (the namespace to match).

- [ ] **Step 2: Add the ledger glob** — append to `.gitignore` (next to the other `omnitune/.*` state files):
```
omnitune/.audit-ledger-*.json
```

- [ ] **Step 3: Verify it ignores a sample ledger**
```bash
cd <repo-root>
mkdir -p omnitune && touch "omnitune/.audit-ledger-sample.json"
git check-ignore "omnitune/.audit-ledger-sample.json" && echo "ignored OK"
rm -f "omnitune/.audit-ledger-sample.json"
```
Expected: prints the path then `ignored OK`.

- [ ] **Step 4: Commit**
```bash
cd <repo-root>
git add .gitignore
git commit -m "chore(audit-gate): gitignore per-run audit ledger"
```

---

## Task 4: Iterated-panel protocol in `skills/sync/SKILL.md`

**Files:** Modify `skills/sync/SKILL.md`.

- [ ] **Step 1: Read the gated-self-apply section**

Open `skills/sync/SKILL.md` and locate the `## Gated self-apply (v0.2)` section and its numbered step that describes the single **no-write audit subagent** (the step beginning "**No-write audit subagent.**"). You will replace *that one step* with the D3 block below, leaving the other steps (two-key confirmation, ratchet, regression corpus, post-apply lint, human commit) intact.

- [ ] **Step 2: Replace the no-write-audit-subagent step** with this verbatim block (renumber the surrounding list if needed so the new block sits where the old step 2 was):

```markdown
2. **Iterated independent-audit gate** (replaces the single no-write audit pass).
   - **Cheap-path.** Diff the proposed rubric against the current one with the ratchet's diff. A **trivial** change (≤ `model_sync.audit_panel_threshold` changed directives, no new sections, no severity changes — e.g. a `(verify)` resolution or a `lastSynced` bump) takes the original **single** no-write audit pass and skips the loop. A **substantial** change (new rubric, new sections, multiple rules) runs the panel loop below.
   - **Capability probe.** If independent subagent dispatch is unavailable (no `Task`; Codex without `multi_agent = true`, see `../omnitune/references/codex-tools.md`), **fall back to propose-only** — never run "reviewers" in your own context (that would be self-review).
   - **Loop.** `python3 scripts/audit_ledger.py` is the ledger API (`reset`, `record_round`, `set_status`, `convergence`). `reset` a per-run ledger at `omnitune/.audit-ledger-<session-id>.json`. Each round: dispatch **2–3 independent no-write reviewers** (tools exclude `Edit`/`Write`/`Bash`; no further dispatch; no network; fresh context; **none is you, the author**) with materially distinct lenses — correctness/fidelity, fail-closed safety + citation discipline, provider-domain accuracy — and, where the harness allows, run at least one lens on a **different provider model**. Pass each reviewer the **carry-forward set** (prior rounds' still-open findings by fingerprint + summary) so the round is a true re-review. Each reviewer returns `(location, category, severity, summary)`; you compute the fingerprint with `audit_ledger.fingerprint(category, location)` (do not let reviewers invent slugs) and `record_round` the panel with reviewer ids.
   - **Reconcile.** For each open material finding, fix the rubric and `set_status(fp, "reconciled", reason)`, or `set_status(fp, "declined", reason)` with a written justification (reasons are surfaced at human sign-off — a decline is auditable, not a rubber stamp).
   - **Terminate on the ledger, not your judgment.** Call `convergence(...)` (defaults `clean_rounds=2`, `cap=3`, `material="high"`, overridable via `model_sync.audit_*`). `NOT_CONVERGED` → run another round. `CAP_EXCEEDED` → stop, surface `open_material` to the operator, **fall back to propose-only**. `CONVERGED` → proceed to the gates below.
```

- [ ] **Step 3: Add one honesty sentence** to the section's safety note (or create one if absent), verbatim:
```markdown
The panel makes the audit's *termination* mechanical and adds *context-independent* reviewers; it does not make thoroughness provable, nor (when all reviewers share one model) remove model-level blind spots. The tighten-only ratchet, the regression-corpus floor, and human commit remain the real backstops and run unchanged after convergence.
```

- [ ] **Step 4: Verify the skill still lints**
```bash
cd <repo-root>
python3 scripts/tuner_check.py . && grep -c "audit_ledger" skills/sync/SKILL.md
```
Expected: `tuner-check: OK`; the grep prints a count ≥ 1.

- [ ] **Step 5: Commit**
```bash
cd <repo-root>
git add skills/sync/SKILL.md
git commit -m "feat(audit-gate): iterated-panel convergence protocol in sync SKILL"
```

---

## Task 5: Integration verification

**Files:** none (verification only)

- [ ] **Step 1: Full CI suite**
```bash
cd <repo-root>/scripts
python3 -m unittest test_tuner_check test_rubric_ratchet test_sync_state test_validate_plugin test_check_public_clean test_resolve_model test_detect_model test_audit_ledger
```
Expected: `OK`.

- [ ] **Step 2: Blocking lints**
```bash
cd <repo-root>
python3 scripts/validate_plugin.py .
python3 scripts/check_public_clean.py .
python3 scripts/tuner_check.py .
```
Expected: each prints OK / exits 0.

- [ ] **Step 3: End-to-end ledger walk (the spec's worked example)**
```bash
cd <repo-root>
python3 -c "
import sys; sys.path.insert(0,'scripts'); import audit_ledger as al
p='/tmp/d3-demo.json'; al.reset(p)
rv=lambda i,l,f:{'reviewer_id':i,'lens':l,'findings':f}
al.record_round(p,1,[rv('ra','correct',[]),rv('rb','safety',[{'fingerprint':al.fingerprint('safety','audit-floor'),'severity':'critical','summary':'floor dropped'}])])
print('after R1:', al.convergence(p)['verdict'])
al.set_status(p, al.fingerprint('safety','audit-floor'),'reconciled','restored floor-rule')
al.record_round(p,2,[rv('ra','correct',[]),rv('rb','safety',[])])
print('after R2:', al.convergence(p)['verdict'])
al.record_round(p,3,[rv('ra','correct',[]),rv('rb','safety',[])])
print('after R3:', al.convergence(p))
"
rm -f /tmp/d3-demo.json
```
Expected: `after R1: NOT_CONVERGED`, `after R2: NOT_CONVERGED`, `after R3: {... 'verdict': 'CONVERGED' ... 'open_material': [] ...}`.

- [ ] **Step 4: Final commit (if any verification fixes were made)**
```bash
cd <repo-root>
git add -A && git commit -m "test(d3): integration verification for iterated audit gate" || echo "nothing to commit"
```

---

## Self-Review (recorded)

- **Spec coverage:** §4.A ledger (fingerprint/reset/record_round/set_status/convergence, append-only, never-raises) → Task 1; §4.B protocol (cheap-path, capability probe, panel loop, reconcile) → Task 4; §4.C config + blocking validation → Task 2; §4.D state/concurrency (per-run gitignored path) → Task 3 + the protocol's reset; §6 worked example → Task 5 Step 3; §8 tests → Task 1 + Task 2. All mapped.
- **Out of scope honored:** no plan-audit, no version log, no doc pages, no edits to `rubric_ratchet.py` / corpus / two-key confirm.
- **Name consistency:** `fingerprint(category, location)`, `reset(path)`, `record_round(path, round_no, reviews, author_id, min_reviews)`, `set_status(path, fp, status, reason)`, `convergence(path, clean_rounds, cap, material)` are identical across the module (Task 1 Step 3), its tests (Task 1 Step 1), and the protocol (Task 4). `_audit_config_problems(cfg)` matches between Task 2 code and tests.
- **Anti-gaming preserved:** incomplete/author-included rounds never count clean (Task 1 tests); `open_material` blocks CONVERGED; `clean_rounds` clamped ≥1 so an empty ledger can't converge; config validation is blocking.
