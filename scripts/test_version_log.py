import os
import tempfile
import unittest

import version_log as vl


def _p(t):
    return os.path.join(t, "skills", "omnitune", "references", "version-log.json")


def _entry(**kw):
    base = {"date": "2026-06-29", "model_id": "gpt-5.5", "action": "add"}
    base.update(kw)
    return base


class TestRecord(unittest.TestCase):
    def test_requires_date_model_action(self):
        with tempfile.TemporaryDirectory() as t:
            p = _p(t)
            for missing in ("date", "model_id", "action"):
                e = _entry()
                del e[missing]
                with self.assertRaises(ValueError):
                    vl.record(p, e)

    def test_bad_action_raises(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ValueError):
                vl.record(_p(t), _entry(action="bogus"))

    def test_append_never_mutates(self):
        with tempfile.TemporaryDirectory() as t:
            p = _p(t)
            vl.record(p, _entry(model_id="a"))
            vl.record(p, _entry(model_id="b", action="update"))
            self.assertEqual([e["model_id"] for e in vl.entries(p)], ["a", "b"])

    def test_latest_returns_newest(self):
        with tempfile.TemporaryDirectory() as t:
            p = _p(t)
            vl.record(p, _entry(model_id="a", date="2026-01-01"))
            vl.record(p, _entry(model_id="a", action="update", date="2026-06-29"))
            self.assertEqual(vl.latest(p, "a")["date"], "2026-06-29")
            self.assertIsNone(vl.latest(p, "nope"))

    def test_tolerate_corrupt(self):
        with tempfile.TemporaryDirectory() as t:
            p = _p(t)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w") as f:
                f.write("{bad")
            self.assertEqual(vl.entries(p), [])
            self.assertIsNone(vl.latest(p, "x"))


if __name__ == "__main__":
    unittest.main()
