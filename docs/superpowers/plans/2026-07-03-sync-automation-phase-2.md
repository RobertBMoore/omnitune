# Sync-Automation Phase 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mechanize the four Tier-1 prose-only gates in `skills/sync/SKILL.md` (regression-corpus floor, manifest entry/validate, panel carry-forward, post-apply revert) into focused, tested, CLI-runnable checks — no gate-semantics change.

**Architecture:** Four independent units matching the repo's one-script-per-concern pattern. Three new standalone scripts (`corpus_check.py`, `manifest_propose.py`, `apply_guard.py`) each with `main()`+usage and a paired `test_*.py`; one new function (`carry_forward`) on the existing `audit_ledger.py`. Then `skills/sync/SKILL.md` is rewired to call them. Dependency-free (stdlib; reuses `resolve_model`, `sync_sources`, `tuner_check`).

**Tech Stack:** Python 3 stdlib, `unittest`, `pytest` runner, `git` (subprocess, for `apply_guard`). Design spec: `docs/superpowers/specs/2026-07-03-sync-automation-phase-2-design.md`.

**Execution notes:**
- Commits in this repo go through the Nimbalyst commit-proposal widget; the `git add/commit` lines below show intent — stage exactly the files named.
- The H1 `hook_guard.py` PreToolUse guards fence *rubrics* and *state files* (`models.json`, `version-log.json`, `hooks.json`). New files under `scripts/` and edits to `skills/sync/SKILL.md` are **not** fenced — no approval marker needed.
- Baseline is **234 tests green**; each task adds a suite and keeps the whole suite green.

---

### Task 1: `carry_forward()` on `audit_ledger.py` (G3)

**Files:**
- Modify: `scripts/audit_ledger.py` (add one function after `convergence`)
- Test: `scripts/test_audit_ledger.py` (append a `CarryForward` test class)

- [ ] **Step 1: Write the failing tests**

Append to `scripts/test_audit_ledger.py`:

```python
class CarryForward(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.d = tempfile.mkdtemp()
        self.p = os.path.join(self.d, "ledger.json")
        audit_ledger.reset(self.p)

    def _round(self, n, findings, author="author"):
        reviews = [{"reviewer_id": "rev-a", "findings": findings},
                   {"reviewer_id": "rev-b", "findings": []}]
        audit_ledger.record_round(self.p, n, reviews, author_id=author)

    def test_open_finding_carried(self):
        fp = audit_ledger.fingerprint("wrong-value", "file.md-10")
        self._round(1, [{"fingerprint": fp, "severity": "high", "summary": "bad number"}])
        cf = audit_ledger.carry_forward(self.p)
        self.assertEqual([f["fingerprint"] for f in cf], [fp])
        self.assertEqual(cf[0]["summary"], "bad number")
        self.assertEqual(cf[0]["severity"], "high")

    def test_reconciled_and_declined_excluded(self):
        fp1 = audit_ledger.fingerprint("wrong-value", "f.md-1")
        fp2 = audit_ledger.fingerprint("style", "f.md-2")
        self._round(1, [{"fingerprint": fp1, "severity": "high", "summary": "x"},
                        {"fingerprint": fp2, "severity": "low", "summary": "y"}])
        audit_ledger.set_status(self.p, fp1, "reconciled", "fixed")
        audit_ledger.set_status(self.p, fp2, "declined", "wontfix")
        self.assertEqual(audit_ledger.carry_forward(self.p), [])

    def test_reopened_included(self):
        fp = audit_ledger.fingerprint("wrong-value", "f.md-10")
        self._round(1, [{"fingerprint": fp, "severity": "high", "summary": "x"}])
        audit_ledger.set_status(self.p, fp, "reconciled", "fixed")
        audit_ledger.set_status(self.p, fp, "open")
        self.assertEqual([f["fingerprint"] for f in audit_ledger.carry_forward(self.p)], [fp])

    def test_empty_ledger(self):
        self.assertEqual(audit_ledger.carry_forward(self.p), [])

    def test_includes_low_and_material_subset_matches_convergence(self):
        hi = audit_ledger.fingerprint("wrong-value", "a-1")
        lo = audit_ledger.fingerprint("nit", "b-2")
        self._round(1, [{"fingerprint": hi, "severity": "high", "summary": "h"},
                        {"fingerprint": lo, "severity": "low", "summary": "l"}])
        cf = {f["fingerprint"] for f in audit_ledger.carry_forward(self.p)}
        self.assertEqual(cf, {hi, lo})
        conv = audit_ledger.convergence(self.p)
        mat = {f["fingerprint"] for f in audit_ledger.carry_forward(self.p)
               if audit_ledger._rank(f["severity"]) >= 2}
        self.assertEqual(mat, set(conv["open_material"]))

    def test_latest_round_detail_wins(self):
        fp = audit_ledger.fingerprint("wrong-value", "a-1")
        self._round(1, [{"fingerprint": fp, "severity": "medium", "summary": "first"}])
        self._round(2, [{"fingerprint": fp, "severity": "high", "summary": "second"}])
        cf = audit_ledger.carry_forward(self.p)
        self.assertEqual(cf[0]["summary"], "second")
        self.assertEqual(cf[0]["severity"], "high")
```

(Confirm the test file already has `import os` and `import audit_ledger` at the top — the existing suite does. Add `import tempfile` at top if not present; the `setUp` above imports it locally as a fallback.)

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest scripts/test_audit_ledger.py -k CarryForward -q`
Expected: FAIL — `AttributeError: module 'audit_ledger' has no attribute 'carry_forward'`

- [ ] **Step 3: Implement `carry_forward`**

Add to `scripts/audit_ledger.py` immediately after `convergence` (end of file):

```python
def carry_forward(path):
    """Still-open findings (newest status != reconciled/declined) as the next
    round's re-review set: sorted [{fingerprint, summary, severity}], using each
    fingerprint's most-recent round detail. Reuses the same newest-status-wins
    rule as convergence(), so the two never disagree. Never raises. Includes ALL
    severities (the panel re-reviews everything still open); convergence()'s
    material-only open_material is a subset."""
    try:
        events = _load(path)["events"]
        current_status = {}
        for e in events:
            if e.get("type") == "status":
                current_status[e.get("fingerprint")] = e.get("status")
        detail = {}
        for e in events:
            if e.get("type") != "round":
                continue
            for rv in e.get("reviews") or []:
                for f in rv.get("findings") or []:
                    fp = f.get("fingerprint")
                    if fp is None:
                        continue
                    detail[fp] = {"fingerprint": fp,
                                  "summary": f.get("summary", ""),
                                  "severity": f.get("severity", "low")}
        out = [detail[fp] for fp in detail
               if current_status.get(fp, "open") == "open"]
        return sorted(out, key=lambda d: (-_rank(d["severity"]), d["fingerprint"]))
    except Exception:  # noqa: BLE001 - carry-forward must never block a run
        return []
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest scripts/test_audit_ledger.py -q`
Expected: PASS (existing ledger tests + 6 new)

- [ ] **Step 5: Commit**

```bash
git add scripts/audit_ledger.py scripts/test_audit_ledger.py
git commit -m "feat(sync): audit_ledger.carry_forward — mechanize panel re-review set (G3)"
```

---

### Task 2: `corpus_check.py` — regression-corpus floor gate (G1)

**Files:**
- Create: `scripts/corpus_check.py`
- Test: `scripts/test_corpus_check.py`

- [ ] **Step 1: Write the failing tests**

Create `scripts/test_corpus_check.py`:

```python
import os
import tempfile
import unittest

import corpus_check as cc


class Floor(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.corpus = os.path.join(self.d, "regression")
        os.makedirs(self.corpus)

    def _add(self, *names):
        for n in names:
            open(os.path.join(self.corpus, n), "w").close()

    def test_under_floor(self):
        self._add("a.md", "b.md")
        r = cc.floor(self.corpus, min_items=5)
        self.assertFalse(r["ok"])
        self.assertEqual(r["count"], 2)
        self.assertEqual(r["reason"], cc.UNDER_FLOOR_REASON)

    def test_exactly_at_floor(self):
        self._add("a.md", "b.md", "c.md", "d.md", "e.md")
        r = cc.floor(self.corpus, min_items=5)
        self.assertTrue(r["ok"])
        self.assertEqual(r["reason"], "")

    def test_readme_excluded(self):
        self._add("README.md", "a.md")
        self.assertEqual(cc.floor(self.corpus, min_items=1)["count"], 1)

    def test_seed_candidates_listed(self):
        self._add("a.md")
        prompts = os.path.join(self.d, "prompts")
        os.makedirs(prompts)
        open(os.path.join(prompts, "p1.md"), "w").close()
        r = cc.floor(self.corpus, min_items=5, prompts_dir=prompts)
        self.assertIn("p1.md", r["seed_candidates"])

    def test_seed_writes_and_skips_existing(self):
        prompts = os.path.join(self.d, "prompts")
        os.makedirs(prompts)
        for n in ("p1.md", "p2.md", "p3.md"):
            open(os.path.join(prompts, n), "w").close()
        self._add("p1.md")  # already in corpus -> skipped
        written = cc.seed(self.corpus, prompts, 5)
        self.assertEqual(written, ["p2.md", "p3.md"])
        self.assertEqual(cc.floor(self.corpus, min_items=1)["count"], 3)

    def test_main_exit_codes(self):
        self._add("a.md")
        self.assertEqual(cc.main([self.corpus, "--floor", "5"]), 1)
        self._add("b.md", "c.md", "d.md", "e.md")
        self.assertEqual(cc.main([self.corpus, "--floor", "5"]), 0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest scripts/test_corpus_check.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'corpus_check'`

- [ ] **Step 3: Implement `corpus_check.py`**

Create `scripts/corpus_check.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest scripts/test_corpus_check.py -q`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/corpus_check.py scripts/test_corpus_check.py
git commit -m "feat(sync): corpus_check — mechanize regression-corpus floor gate (G1)"
```

---

### Task 3: `manifest_propose.py` — entry emit + validate (G2)

**Files:**
- Create: `scripts/manifest_propose.py`
- Test: `scripts/test_manifest_propose.py`

- [ ] **Step 1: Write the failing tests**

Create `scripts/test_manifest_propose.py`:

```python
import json
import os
import tempfile
import unittest

import manifest_propose as mp

REAL = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "..", "skills", "omnitune", "references", "models.json")

GOOD = {
    "providers": {"anthropic": {"allowlist_domains":
                                ["platform.claude.com", "www.anthropic.com"]}},
    "models": [
        {"id": "claude-x", "provider": "anthropic", "family": "x", "status": "ga",
         "ga_date": None, "deprecated_date": None,
         "rubric": "references/rubrics/anthropic/claude-x.md",
         "source_urls": ["https://platform.claude.com/docs/x"]},
    ],
}


def _write(obj):
    d = tempfile.mkdtemp()
    p = os.path.join(d, "models.json")
    with open(p, "w") as f:
        json.dump(obj, f)
    return p


class Validate(unittest.TestCase):
    def test_clean_passes(self):
        self.assertEqual(mp.validate(_write(GOOD)), [])

    def test_bad_status(self):
        obj = json.loads(json.dumps(GOOD))
        obj["models"][0]["status"] = "beta"
        self.assertTrue(any("status" in x for x in mp.validate(_write(obj))))

    def test_wrong_rubric_path(self):
        obj = json.loads(json.dumps(GOOD))
        obj["models"][0]["rubric"] = "references/rubrics/anthropic/wrong.md"
        self.assertTrue(any("rubric path" in x for x in mp.validate(_write(obj))))

    def test_off_allowlist_source(self):
        obj = json.loads(json.dumps(GOOD))
        obj["models"][0]["source_urls"] = ["https://evil.example.com/x"]
        self.assertTrue(any("allowlist" in x for x in mp.validate(_write(obj))))

    def test_fabricated_date(self):
        obj = json.loads(json.dumps(GOOD))
        obj["models"][0]["ga_date"] = "soon"
        self.assertTrue(any("ISO" in x for x in mp.validate(_write(obj))))

    def test_real_manifest_is_clean(self):
        self.assertEqual(mp.validate(REAL), [])


class Entry(unittest.TestCase):
    def test_entry_shape_for_known_model(self):
        e = mp.entry("claude-opus-4-8", REAL)
        self.assertEqual(e["id"], "claude-opus-4-8")
        self.assertEqual(e["provider"], "anthropic")
        self.assertEqual(e["rubric"], "references/rubrics/anthropic/claude-opus-4-8.md")
        self.assertIn(e["status"], mp.VALID_STATUS)
        self.assertIsInstance(e["source_urls"], list)
        self.assertTrue(e["ga_date"] is None or isinstance(e["ga_date"], str))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest scripts/test_manifest_propose.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'manifest_propose'`

- [ ] **Step 3: Implement `manifest_propose.py`**

Create `scripts/manifest_propose.py`:

```python
#!/usr/bin/env python3
"""manifest_propose — emit + validate models.json entries.

  entry <id> <models.json>   -> a ready-to-merge model row (never fabricates dates)
  validate <models.json>     -> semantic check of every entry; exit 1 on any problem

Complements hook_guard's structural integrity with schema/semantic validation.
Dependency-free (stdlib + resolve_model/sync_sources).
"""
import json
import sys
from urllib.parse import urlparse

import resolve_model
import sync_sources

VALID_STATUS = {"ga", "limited", "deprecated", "retired"}


def _load(models_json_path):
    with open(models_json_path) as f:
        return json.load(f)


def _existing(mj, normalized_id):
    for m in mj.get("models", []):
        if m.get("id") == normalized_id:
            return m
    return None


def entry(raw_id, models_json_path):
    plan = sync_sources.plan(raw_id, models_json_path)
    mj = _load(models_json_path)
    nid = plan["normalized_id"]
    prov = plan["provider"]
    ex = _existing(mj, nid) or {}
    return {
        "id": nid,
        "provider": prov,
        "family": ex.get("family") or resolve_model._family_guess(nid),
        "status": ex.get("status") or "ga",
        "ga_date": ex.get("ga_date"),
        "deprecated_date": ex.get("deprecated_date"),
        "rubric": "references/rubrics/%s/%s.md" % (prov, nid),
        "source_urls": [u["url"] for u in plan.get("fetch_urls", [])],
    }


def _hosts(mj, provider):
    return (mj.get("providers", {}).get(provider, {}) or {}).get("allowlist_domains", []) or []


def _iso_or_null(d):
    if d is None:
        return True
    if not isinstance(d, str) or len(d) != 10 or d[4] != "-" or d[7] != "-":
        return False
    return (d[:4] + d[5:7] + d[8:10]).isdigit()


def validate(models_json_path):
    mj = _load(models_json_path)
    problems = []
    for m in mj.get("models", []):
        mid = m.get("id", "<no-id>")
        prov = m.get("provider")
        if m.get("status") not in VALID_STATUS:
            problems.append("%s: status %r not in %s"
                            % (mid, m.get("status"), sorted(VALID_STATUS)))
        rub = m.get("rubric")
        if rub is not None:
            want = "references/rubrics/%s/%s.md" % (prov, mid)
            if rub != want:
                problems.append("%s: rubric path %r != %r" % (mid, rub, want))
        hosts = _hosts(mj, prov)
        for u in m.get("source_urls", []) or []:
            host = urlparse(u).hostname or ""
            if not any(host == h or host.endswith("." + h) for h in hosts):
                problems.append("%s: source host %r not in allowlist %s"
                                % (mid, host, hosts))
        for key in ("ga_date", "deprecated_date"):
            if not _iso_or_null(m.get(key)):
                problems.append("%s: %s %r is not null or ISO YYYY-MM-DD"
                                % (mid, key, m.get(key)))
    return problems


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) == 3 and args[0] == "entry":
        print(json.dumps(entry(args[1], args[2]), indent=2, sort_keys=True))
        return 0
    if len(args) == 2 and args[0] == "validate":
        problems = validate(args[1])
        for p in problems:
            print(p)
        return 1 if problems else 0
    sys.stderr.write("usage: manifest_propose.py entry <id> <models.json>\n"
                     "       manifest_propose.py validate <models.json>\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest scripts/test_manifest_propose.py -q`
Expected: PASS (7 tests). If `test_real_manifest_is_clean` fails, the live `models.json` has a real semantic problem — fix the manifest (or, if the rule is wrong, correct the validator) before proceeding; do not weaken the test.

- [ ] **Step 5: Commit**

```bash
git add scripts/manifest_propose.py scripts/test_manifest_propose.py
git commit -m "feat(sync): manifest_propose — entry emit + semantic validate (G2)"
```

---

### Task 4: `apply_guard.py` — post-apply lint + scoped revert (G4)

**Files:**
- Create: `scripts/apply_guard.py`
- Test: `scripts/test_apply_guard.py`

- [ ] **Step 1: Write the failing tests** (revert mechanics, with `tuner_check.check` monkeypatched)

Create `scripts/test_apply_guard.py`:

```python
import os
import subprocess
import tempfile
import unittest

import apply_guard


def _git(args, cwd):
    subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True, check=True)


class Guard(unittest.TestCase):
    def setUp(self):
        self.repo = tempfile.mkdtemp()
        _git(["init"], self.repo)
        _git(["config", "user.email", "t@t"], self.repo)
        _git(["config", "user.name", "t"], self.repo)
        self._orig = apply_guard.tuner_check.check

    def tearDown(self):
        apply_guard.tuner_check.check = self._orig

    def _write(self, rel, text):
        p = os.path.join(self.repo, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            f.write(text)
        return p

    def test_pass_keeps_file(self):
        apply_guard.tuner_check.check = lambda *a, **k: []
        p = self._write("skills/omnitune/references/rubrics/x/m.md", "new")
        code, probs = apply_guard.guard(p, self.repo)
        self.assertEqual(code, 0)
        self.assertTrue(os.path.exists(p))

    def test_fail_new_file_deleted(self):
        apply_guard.tuner_check.check = lambda *a, **k: ["boom"]
        p = self._write("skills/omnitune/references/rubrics/x/m.md", "new")
        code, probs = apply_guard.guard(p, self.repo)
        self.assertEqual(code, 1)
        self.assertFalse(os.path.exists(p))
        self.assertIn("boom", probs)

    def test_fail_tracked_reverted(self):
        rel = "skills/omnitune/references/rubrics/x/m.md"
        p = self._write(rel, "original")
        _git(["add", "-A"], self.repo)
        _git(["commit", "-m", "init"], self.repo)
        with open(p, "w") as f:
            f.write("MODIFIED")
        apply_guard.tuner_check.check = lambda *a, **k: ["boom"]
        code, probs = apply_guard.guard(p, self.repo)
        self.assertEqual(code, 1)
        self.assertEqual(open(p).read(), "original")

    def test_unrelated_edit_untouched(self):
        rel = "skills/omnitune/references/rubrics/x/m.md"
        other = self._write("scripts/other.py", "keep")
        p = self._write(rel, "orig")
        _git(["add", "-A"], self.repo)
        _git(["commit", "-m", "init"], self.repo)
        with open(other, "w") as f:
            f.write("EDITED-UNRELATED")
        with open(p, "w") as f:
            f.write("MODIFIED")
        apply_guard.tuner_check.check = lambda *a, **k: ["boom"]
        apply_guard.guard(p, self.repo)
        self.assertEqual(open(other).read(), "EDITED-UNRELATED")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest scripts/test_apply_guard.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'apply_guard'`

- [ ] **Step 3: Implement `apply_guard.py`**

Create `scripts/apply_guard.py`:

```python
#!/usr/bin/env python3
"""apply_guard — post-apply lint + scoped revert.

Run tuner_check after a rubric write; on failure revert ONLY that path (git
checkout if tracked, else delete the new file) and exit 1. Exit 0 clean, 2 if
git/paths unavailable. Path-scoped revert never touches unrelated edits. Mirrors
ratchet_gate's git-shell pattern.

Run:  python3 scripts/apply_guard.py <rubric-path> [repo_root]
"""
import os
import subprocess
import sys

import tuner_check


def _git(args, cwd):
    return subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)


def _toplevel(start):
    r = _git(["rev-parse", "--show-toplevel"], start)
    return r.stdout.strip() if r.returncode == 0 else None


def _tracked(repo_root, rel):
    return _git(["ls-files", "--error-unmatch", rel], repo_root).returncode == 0


def guard(rubric_path, repo_root=None):
    """Returns (exit_code, problems). Reverts rubric_path on lint failure."""
    start = os.path.dirname(os.path.abspath(rubric_path))
    repo_root = repo_root or _toplevel(start)
    if not repo_root:
        return 2, ["git unavailable / not a repo"]
    cfg = os.path.join(repo_root, "omnitune.config.yaml")
    models = os.path.join(repo_root, "skills", "omnitune", "references", "models.json")
    try:
        config_text = open(cfg).read()
    except OSError:
        config_text = ""
    problems = tuner_check.check(repo_root, config_text, models)
    if not problems:
        return 0, []
    rel = os.path.relpath(rubric_path, repo_root)
    if _tracked(repo_root, rel):
        _git(["checkout", "HEAD", "--", rel], repo_root)
    elif os.path.exists(rubric_path):
        os.remove(rubric_path)
    return 1, problems


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if not 1 <= len(args) <= 2:
        sys.stderr.write("usage: apply_guard.py <rubric-path> [repo_root]\n")
        return 2
    code, problems = guard(args[0], args[1] if len(args) == 2 else None)
    for p in problems:
        print(p)
    return code


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest scripts/test_apply_guard.py -q`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/apply_guard.py scripts/test_apply_guard.py
git commit -m "feat(sync): apply_guard — post-apply lint + scoped revert (G4)"
```

---

### Task 5: Rewire `skills/sync/SKILL.md` to call the four units

**Files:**
- Modify: `skills/sync/SKILL.md` (Detection/derive + Gated self-apply §2/§4/§5 + Definition of Done)

No code, so no unit test — verification is a grep + the full suite. Make these prose edits, each replacing a manual instruction with the script call (do **not** change any gate's meaning):

- [ ] **Step 1: Panel carry-forward (§ "Gated self-apply" → Loop, ~line 57).** After the sentence "Pass each reviewer the **carry-forward set** (prior rounds' still-open findings by fingerprint + summary)…", append: "Assemble that set with `audit_ledger.carry_forward(ledger_path)` — do not hand-collect it; the helper reuses the ledger's newest-status-wins rule so the carry-forward set and `convergence()` never disagree."

- [ ] **Step 2: Regression-corpus floor (§ "Gated self-apply" → step 4, ~line 61).** Replace the prose floor check with: "Run `python3 scripts/corpus_check.py <model_sync.regression_corpus> --prompts <output.prompts>`. Exit 1 (count < 5) returns `cannot verify no-drift — manual review required` → **fall back to propose-only**. Seed with `--seed N` only on explicit operator go-ahead."

- [ ] **Step 3: Manifest entry + validate (§ "Derive a rubric" step 5 and § "Gated self-apply" step 1/7).** Add: "Produce the manifest row with `python3 scripts/manifest_propose.py entry <id> skills/omnitune/references/models.json` (never hand-write the JSON), and gate any manifest edit with `python3 scripts/manifest_propose.py validate skills/omnitune/references/models.json` (exit 1 blocks) before the operator merges it."

- [ ] **Step 4: Post-apply revert (§ "Gated self-apply" → step 5, ~line 62).** Replace "`scripts/tuner_check.py` must pass after writing, or the change is reverted." with: "Run `python3 scripts/apply_guard.py <written-rubric-path>` — it runs `tuner_check` and, on failure, reverts **only** that rubric (checkout-if-tracked / delete-if-new) and exits 1. A nonzero exit means the write did not stick."

- [ ] **Step 5: Definition of Done.** In the "On gated self-apply (v0.2)" bullet, append: "corpus floor enforced via `corpus_check.py`; carry-forward via `audit_ledger.carry_forward`; manifest row via `manifest_propose entry`+`validate`; post-apply via `apply_guard.py`."

- [ ] **Step 6: Verify the wiring references resolve**

Run: `grep -nE 'corpus_check|manifest_propose|carry_forward|apply_guard' skills/sync/SKILL.md`
Expected: at least one hit per script name.
Run: `python3 -m pytest scripts/ -q`
Expected: PASS (full suite still green — SKILL.md is prose, no test impact).

- [ ] **Step 7: Commit**

```bash
git add skills/sync/SKILL.md
git commit -m "docs(sync): wire SKILL.md to the four Phase 2 gate scripts"
```

---

### Task 6: Final verification

- [ ] **Step 1: Run the whole suite**

Run: `python3 -m pytest scripts/ -q`
Expected: PASS — baseline **234** + Task 1 (6) + Task 2 (6) + Task 3 (7) + Task 4 (4) = **257** tests green (exact count may differ if the baseline shifted; the requirement is *all green, no regressions*).

- [ ] **Step 2: Smoke-test each new CLI against the live repo**

```bash
python3 scripts/corpus_check.py tuner/regression --floor 5        # expect ok:true, exit 0 (6 fixtures)
python3 scripts/manifest_propose.py validate skills/omnitune/references/models.json   # expect no output, exit 0
python3 scripts/manifest_propose.py entry claude-opus-4-8 skills/omnitune/references/models.json   # expect a JSON row
```
Expected: corpus_check `ok: true`; validate silent exit 0; entry prints a well-formed row.

- [ ] **Step 3: Confirm no fenced files were touched without approval**

Run: `git status -s`
Expected: clean (all work committed); no changes to `models.json`, `version-log.json`, `hooks.json`, or any rubric (this plan touches none of them).

- [ ] **Step 4: Update session tags** — flip `uncommitted` → `committed` once all six task commits are in.

---

## Self-review notes (author)

- **Spec coverage:** G1→Task 2, G2→Task 3, G3→Task 1, G4→Task 4, SKILL rewiring→Task 5, DoD/verify→Task 6. All four units + wiring + tests covered.
- **Type/name consistency:** `floor()`/`seed()`/`UNDER_FLOOR_REASON` (corpus_check), `entry()`/`validate()`/`VALID_STATUS` (manifest_propose), `carry_forward()` (audit_ledger), `guard()` (apply_guard) — names are used identically in tests and implementations and in the SKILL wiring.
- **No placeholders:** every step has runnable code/commands and expected output.
- **Non-goals** (G5–G9) intentionally excluded — Phase 3.
