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
