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

    def test_missing_author_id_never_complete(self):
        with tempfile.TemporaryDirectory() as t:
            p = _ledger(t)
            al.record_round(p, 1, [_review("a", "x", []), _review("b", "y", [])])  # no author_id
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
            al.record_round(p, 1, self._two([]), author_id="author")
            al.record_round(p, 2, self._two([]), author_id="author")
            r = al.convergence(p)
            self.assertEqual(r["verdict"], "CONVERGED")
            self.assertEqual(r["trailing_clean"], 2)

    def test_one_reconcile_converges_at_round_3(self):
        with tempfile.TemporaryDirectory() as t:
            p = _ledger(t)
            al.record_round(p, 1, self._two([], [_f("safety:audit-floor", "critical")]),
                            author_id="author")
            al.set_status(p, "safety:audit-floor", "reconciled", "restored floor-rule")
            al.record_round(p, 2, self._two([]), author_id="author")
            self.assertEqual(al.convergence(p)["verdict"], "NOT_CONVERGED")
            al.record_round(p, 3, self._two([]), author_id="author")
            r = al.convergence(p)
            self.assertEqual(r["verdict"], "CONVERGED")
            self.assertEqual(r["open_material"], [])

    def test_persistent_open_never_converges_hits_cap(self):
        with tempfile.TemporaryDirectory() as t:
            p = _ledger(t)
            for n in (1, 2, 3):
                al.record_round(p, n, self._two([], [_f("safety:hole", "critical")]),
                                author_id="author")
            r = al.convergence(p)
            self.assertEqual(r["verdict"], "CAP_EXCEEDED")
            self.assertIn("safety:hole", r["open_material"])

    def test_open_material_blocks_convergence(self):
        with tempfile.TemporaryDirectory() as t:
            p = _ledger(t)
            al.record_round(p, 1, self._two([], [_f("safety:hole", "high")]), author_id="author")
            al.record_round(p, 2, self._two([]), author_id="author")
            al.record_round(p, 3, self._two([]), author_id="author")
            # never reconciled -> open_material non-empty -> CAP_EXCEEDED, not CONVERGED
            self.assertEqual(al.convergence(p)["verdict"], "CAP_EXCEEDED")

    def test_declined_counts_resolved_and_surfaced(self):
        with tempfile.TemporaryDirectory() as t:
            p = _ledger(t)
            al.record_round(p, 1, self._two([], [_f("domain:nit", "high")]), author_id="author")
            al.set_status(p, "domain:nit", "declined", "not applicable to gpt-5.5")
            al.record_round(p, 2, self._two([]), author_id="author")
            al.record_round(p, 3, self._two([]), author_id="author")
            r = al.convergence(p)
            self.assertEqual(r["verdict"], "CONVERGED")
            self.assertIn("domain:nit", r["declined_material"])

    def test_low_medium_ignored_for_material_high(self):
        with tempfile.TemporaryDirectory() as t:
            p = _ledger(t)
            al.record_round(p, 1, self._two([_f("structure:x", "medium")]), author_id="author")
            al.record_round(p, 2, self._two([_f("structure:y", "low")]), author_id="author")
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
