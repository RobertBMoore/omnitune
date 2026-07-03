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


MANIFEST = "skills/omnitune/references/models.json"
VLOG = "skills/omnitune/references/version-log.json"


def _manifest_text(rubric="references/rubrics/anthropic/a.md", dup=False):
    models = [{"id": "m1", "provider": "anthropic", "status": "ga", "rubric": rubric}]
    if dup:
        models.append(dict(models[0]))
    return json.dumps({"schema": 3, "providers": {"anthropic": {}}, "models": models})


class TestStateWriteGuard(unittest.TestCase):
    """H1: models.json integrity; version-log.json + hooks.json append/edit fences."""

    def test_unrelated_file_allowed(self):
        code, _ = _run("state-write", {"tool_name": "Write",
                       "tool_input": {"file_path": "/tmp/x.txt", "content": "hi"}, "cwd": "."})
        self.assertEqual(code, 0)

    def test_manifest_write_valid_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, "skills/omnitune/references/rubrics/anthropic/a.md", "# r\n")
            code, err = _run("state-write", {"tool_name": "Write",
                             "tool_input": {"file_path": os.path.join(tmp, MANIFEST),
                                            "content": _manifest_text()}, "cwd": tmp})
            self.assertEqual(code, 0, err)

    def test_manifest_write_invalid_json_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, err = _run("state-write", {"tool_name": "Write",
                             "tool_input": {"file_path": os.path.join(tmp, MANIFEST),
                                            "content": "{not json"}, "cwd": tmp})
            self.assertEqual(code, 2)
            self.assertIn("JSON", err)

    def test_manifest_duplicate_ids_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, "skills/omnitune/references/rubrics/anthropic/a.md", "# r\n")
            code, err = _run("state-write", {"tool_name": "Write",
                             "tool_input": {"file_path": os.path.join(tmp, MANIFEST),
                                            "content": _manifest_text(dup=True)}, "cwd": tmp})
            self.assertEqual(code, 2)
            self.assertIn("duplicate", err)

    def test_manifest_missing_rubric_file_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:  # rubric file NOT created
            code, err = _run("state-write", {"tool_name": "Write",
                             "tool_input": {"file_path": os.path.join(tmp, MANIFEST),
                                            "content": _manifest_text()}, "cwd": tmp})
            self.assertEqual(code, 2)
            self.assertIn("rubric", err)

    def test_manifest_edit_applies_replacement(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, "skills/omnitune/references/rubrics/anthropic/a.md", "# r\n")
            _write(tmp, MANIFEST, _manifest_text())
            code, _ = _run("state-write", {"tool_name": "Edit",
                           "tool_input": {"file_path": os.path.join(tmp, MANIFEST),
                                          "old_string": '"status": "ga"',
                                          "new_string": '"status": "deprecated"'}, "cwd": tmp})
            self.assertEqual(code, 0)

    def test_version_log_write_blocked_without_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, err = _run("state-write", {"tool_name": "Write",
                             "tool_input": {"file_path": os.path.join(tmp, VLOG),
                                            "content": "{}"}, "cwd": tmp})
            self.assertEqual(code, 2)
            self.assertIn("append-only", err)

    def test_version_log_write_allowed_with_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, hook_guard.APPROVE_FILE, "")
            code, _ = _run("state-write", {"tool_name": "Write",
                           "tool_input": {"file_path": os.path.join(tmp, VLOG),
                                          "content": "{}"}, "cwd": tmp})
            self.assertEqual(code, 0)

    def test_hooks_json_write_blocked_without_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, err = _run("state-write", {"tool_name": "Edit",
                             "tool_input": {"file_path": os.path.join(tmp, "hooks/hooks.json"),
                                            "old_string": "a", "new_string": "b"}, "cwd": tmp})
            self.assertEqual(code, 2)

    def test_marker_bypasses_manifest_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, hook_guard.APPROVE_FILE, "")
            code, _ = _run("state-write", {"tool_name": "Write",
                           "tool_input": {"file_path": os.path.join(tmp, MANIFEST),
                                          "content": "{not json"}, "cwd": tmp})
            self.assertEqual(code, 0)


class TestRubricDeleteGuard(unittest.TestCase):
    """H1: rm / git rm of a rubric file is operator-approved only."""

    def test_plain_rm_of_rubric_blocked(self):
        code, err = _run("rubric-delete", {"tool_input": {
            "command": "rm skills/omnitune/references/rubrics/anthropic/a.md"}, "cwd": "."})
        self.assertEqual(code, 2)
        self.assertIn("delet", err)

    def test_git_rm_of_rubric_blocked(self):
        code, _ = _run("rubric-delete", {"tool_input": {
            "command": "git rm skills/omnitune/references/rubrics/xai/g.md"}, "cwd": "."})
        self.assertEqual(code, 2)

    def test_unrelated_rm_allowed(self):
        code, _ = _run("rubric-delete", {"tool_input": {"command": "rm /tmp/scratch.txt"},
                                         "cwd": "."})
        self.assertEqual(code, 0)

    def test_non_delete_command_allowed(self):
        code, _ = _run("rubric-delete", {"tool_input": {
            "command": "cat skills/omnitune/references/rubrics/anthropic/a.md"}, "cwd": "."})
        self.assertEqual(code, 0)

    def test_marker_allows_delete(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, hook_guard.APPROVE_FILE, "")
            code, _ = _run("rubric-delete", {"tool_input": {
                "command": "git rm skills/omnitune/references/rubrics/anthropic/a.md"},
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
