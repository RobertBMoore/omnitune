import io
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr

import hook_guard

RUBRIC = "skills/omnitune/references/rubrics/anthropic/x.md"
TIGHT = ("# R\n\n## Fail-closed\n\nNever soften a fail-closed directive. "
         "Critical caps the verdict. `[omnitune]`\n")
LOOSE = "# R\n\nSometimes soften things.\n"


def _git(args, root):
    return subprocess.run(["git", "-C", root] + args, capture_output=True, text=True)


def _repo(tmp):
    _git(["init", "-q"], tmp)
    _git(["config", "user.email", "t@t.t"], tmp)
    _git(["config", "user.name", "t"], tmp)
    os.makedirs(os.path.join(tmp, os.path.dirname(RUBRIC)), exist_ok=True)


def _write(tmp, rel, text):
    full = os.path.join(tmp, rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(text)


def _run(which, payload):
    """Call a guard directly, capturing exit code (stderr suppressed)."""
    fn = hook_guard.DISPATCH[which]
    buf = io.StringIO()
    with redirect_stderr(buf):
        code = fn(payload)
    return code, buf.getvalue()


class TestSelfCommitGuard(unittest.TestCase):
    def test_non_git_bash_allowed(self):
        code, _ = _run("self-commit", {"tool_input": {"command": "ls -la"}, "cwd": "."})
        self.assertEqual(code, 0)

    def test_git_commit_with_rubric_path_blocked(self):
        payload = {"tool_input": {
            "command": "git add skills/omnitune/references/rubrics/anthropic/x.md && git commit -m x"},
            "cwd": "."}
        code, err = _run("self-commit", payload)
        self.assertEqual(code, 2)
        self.assertIn("propose-only", err)

    def test_git_status_allowed(self):
        code, _ = _run("self-commit", {"tool_input": {"command": "git status"}, "cwd": "."})
        self.assertEqual(code, 0)

    def test_env_approval_allows(self):
        payload = {"tool_input": {
            "command": "git add skills/omnitune/references/rubrics/anthropic/x.md"}, "cwd": "."}
        os.environ[hook_guard.APPROVE_ENV] = "1"
        try:
            code, _ = _run("self-commit", payload)
        finally:
            del os.environ[hook_guard.APPROVE_ENV]
        self.assertEqual(code, 0)

    def test_staged_rubric_blocks_bare_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            _repo(tmp)
            _write(tmp, "README.md", "seed\n")
            _git(["add", "-A"], tmp)
            _git(["commit", "-q", "-m", "base"], tmp)
            _write(tmp, RUBRIC, TIGHT)
            _git(["add", RUBRIC], tmp)  # rubric is staged
            code, err = _run("self-commit",
                             {"tool_input": {"command": "git commit -m 'update'"}, "cwd": tmp})
            self.assertEqual(code, 2, err)
            self.assertIn(RUBRIC, err)


class TestRubricWriteGuard(unittest.TestCase):
    def test_non_rubric_write_allowed(self):
        code, _ = _run("rubric-write",
                       {"tool_name": "Write", "tool_input": {"file_path": "/x/README.md",
                                                             "content": "hi"}, "cwd": "."})
        self.assertEqual(code, 0)

    def test_new_rubric_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            _repo(tmp)
            _write(tmp, "README.md", "seed\n")
            _git(["add", "-A"], tmp)
            _git(["commit", "-q", "-m", "base"], tmp)
            # rubric absent at HEAD -> new -> allowed
            code, _ = _run("rubric-write",
                           {"tool_name": "Write",
                            "tool_input": {"file_path": os.path.join(tmp, RUBRIC), "content": TIGHT},
                            "cwd": tmp})
            self.assertEqual(code, 0)

    def test_loosening_write_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            _repo(tmp)
            _write(tmp, RUBRIC, TIGHT)
            _git(["add", "-A"], tmp)
            _git(["commit", "-q", "-m", "base"], tmp)
            code, err = _run("rubric-write",
                             {"tool_name": "Write",
                              "tool_input": {"file_path": os.path.join(tmp, RUBRIC), "content": LOOSE},
                              "cwd": tmp})
            self.assertEqual(code, 2, err)
            self.assertIn("tighten-only", err)

    def test_tightening_write_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            _repo(tmp)
            _write(tmp, RUBRIC, TIGHT)
            _git(["add", "-A"], tmp)
            _git(["commit", "-q", "-m", "base"], tmp)
            code, _ = _run("rubric-write",
                           {"tool_name": "Write",
                            "tool_input": {"file_path": os.path.join(tmp, RUBRIC),
                                           "content": TIGHT + "\n## More\n\nNever regress. `[omnitune]`\n"},
                            "cwd": tmp})
            self.assertEqual(code, 0)

    def test_loosening_edit_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            _repo(tmp)
            _write(tmp, RUBRIC, TIGHT)
            _git(["add", "-A"], tmp)
            _git(["commit", "-q", "-m", "base"], tmp)
            # Edit that deletes the whole fail-closed line
            code, err = _run("rubric-write",
                             {"tool_name": "Edit",
                              "tool_input": {"file_path": os.path.join(tmp, RUBRIC),
                                             "old_string": "Never soften a fail-closed directive. ",
                                             "new_string": ""},
                              "cwd": tmp})
            self.assertEqual(code, 2, err)

    def test_approval_allows_loosening(self):
        with tempfile.TemporaryDirectory() as tmp:
            _repo(tmp)
            _write(tmp, RUBRIC, TIGHT)
            _git(["add", "-A"], tmp)
            _git(["commit", "-q", "-m", "base"], tmp)
            _write(tmp, hook_guard.APPROVE_FILE, "")  # approval marker at repo root
            code, _ = _run("rubric-write",
                           {"tool_name": "Write",
                            "tool_input": {"file_path": os.path.join(tmp, RUBRIC), "content": LOOSE},
                            "cwd": tmp})
            self.assertEqual(code, 0)


class TestFailOpen(unittest.TestCase):
    def test_bad_dispatch_returns_zero(self):
        self.assertEqual(hook_guard.main(["hook_guard.py", "bogus"]), 0)

    def test_missing_command_field_allowed(self):
        code, _ = _run("self-commit", {"tool_input": {}, "cwd": "."})
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
