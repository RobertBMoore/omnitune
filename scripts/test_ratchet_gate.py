import os
import subprocess
import tempfile
import unittest

import ratchet_gate

RUBRIC = "skills/omnitune/references/rubrics/anthropic/x.md"
TIGHT = ("# R\n\n## Fail-closed\n\nNever soften a fail-closed directive. "
         "Critical caps the verdict. `[omnitune]`\n")
LOOSE = "# R\n\nSometimes soften things.\n"  # section + hard tokens removed


def _git(args, root):
    return subprocess.run(["git", "-C", root] + args, capture_output=True, text=True)


def _init_repo(tmp):
    _git(["init", "-q"], tmp)
    _git(["config", "user.email", "t@t.t"], tmp)
    _git(["config", "user.name", "t"], tmp)
    os.makedirs(os.path.join(tmp, os.path.dirname(RUBRIC)), exist_ok=True)


def _commit(tmp, msg):
    _git(["add", "-A"], tmp)
    _git(["commit", "-q", "-m", msg], tmp)


def _write(tmp, rel, text):
    with open(os.path.join(tmp, rel), "w") as f:
        f.write(text)


class TestRatchetGate(unittest.TestCase):
    def test_no_changes_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            _init_repo(tmp)
            _write(tmp, RUBRIC, TIGHT)
            _commit(tmp, "base")
            code, lines = ratchet_gate.gate("HEAD", tmp)
            self.assertEqual(code, 0, lines)

    def test_new_rubric_is_skipped_not_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            _init_repo(tmp)
            _write(tmp, "README.md", "seed\n")
            _commit(tmp, "base")  # RUBRIC absent at base
            _write(tmp, RUBRIC, TIGHT)
            _git(["add", "-A"], tmp)  # staged add, as a PR branch would show vs base
            code, lines = ratchet_gate.gate("HEAD", tmp)
            self.assertEqual(code, 0, lines)
            self.assertTrue(any("new rubric" in x for x in lines), lines)

    def test_tightening_edit_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            _init_repo(tmp)
            _write(tmp, RUBRIC, TIGHT)
            _commit(tmp, "base")
            _write(tmp, RUBRIC, TIGHT + "\n## Extra\n\nNever do the bad thing. `[omnitune]`\n")
            code, lines = ratchet_gate.gate("HEAD", tmp)
            self.assertEqual(code, 0, lines)

    def test_loosening_edit_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            _init_repo(tmp)
            _write(tmp, RUBRIC, TIGHT)
            _commit(tmp, "base")
            _write(tmp, RUBRIC, LOOSE)  # section + directives removed
            code, lines = ratchet_gate.gate("HEAD", tmp)
            self.assertEqual(code, 1, lines)
            self.assertTrue(any("BLOCK" in x for x in lines), lines)

    def test_loosening_allowed_with_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            _init_repo(tmp)
            _write(tmp, RUBRIC, TIGHT)
            _commit(tmp, "base")
            _write(tmp, RUBRIC, LOOSE)
            code, lines = ratchet_gate.gate("HEAD", tmp, approved=True)
            self.assertEqual(code, 0, lines)


if __name__ == "__main__":
    unittest.main()
