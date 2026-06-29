import os
import tempfile
import unittest

from detect_model import detect_codex_model, _top_level_model


def _write(path, body):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(body)


class TestTopLevelModel(unittest.TestCase):
    def test_reads_top_level(self):
        with tempfile.TemporaryDirectory() as t:
            p = os.path.join(t, "config.toml")
            _write(p, 'model = "gpt-5.5"\napproval_policy = "auto"\n')
            self.assertEqual(_top_level_model(p), "gpt-5.5")

    def test_single_quotes(self):
        with tempfile.TemporaryDirectory() as t:
            p = os.path.join(t, "config.toml")
            _write(p, "model = 'gpt-5.5'\n")
            self.assertEqual(_top_level_model(p), "gpt-5.5")

    def test_ignores_profile_model(self):
        with tempfile.TemporaryDirectory() as t:
            p = os.path.join(t, "config.toml")
            _write(p, '[profiles.fast]\nmodel = "gpt-5.4-mini"\n')
            self.assertIsNone(_top_level_model(p))

    def test_missing_file_none(self):
        self.assertIsNone(_top_level_model("/no/such/config.toml"))


class TestDetect(unittest.TestCase):
    def test_project_beats_global(self):
        with tempfile.TemporaryDirectory() as proj, tempfile.TemporaryDirectory() as home:
            _write(os.path.join(proj, ".codex", "config.toml"), 'model = "gpt-5.5"\n')
            _write(os.path.join(home, "config.toml"), 'model = "gpt-5.4"\n')
            self.assertEqual(detect_codex_model(start_dir=proj, codex_home=home), "gpt-5.5")

    def test_closest_to_cwd_wins(self):
        with tempfile.TemporaryDirectory() as root:
            _write(os.path.join(root, ".codex", "config.toml"), 'model = "gpt-5.4"\n')
            sub = os.path.join(root, "a", "b")
            os.makedirs(sub, exist_ok=True)
            _write(os.path.join(sub, ".codex", "config.toml"), 'model = "gpt-5.5"\n')
            self.assertEqual(
                detect_codex_model(start_dir=sub, codex_home=os.path.join(root, "nohome")),
                "gpt-5.5")

    def test_falls_back_to_global(self):
        with tempfile.TemporaryDirectory() as proj, tempfile.TemporaryDirectory() as home:
            _write(os.path.join(home, "config.toml"), 'model = "gpt-5.4"\n')
            self.assertEqual(detect_codex_model(start_dir=proj, codex_home=home), "gpt-5.4")

    def test_codex_home_env(self):
        with tempfile.TemporaryDirectory() as proj, tempfile.TemporaryDirectory() as home:
            _write(os.path.join(home, "config.toml"), 'model = "gpt-5.5"\n')
            old = os.environ.get("CODEX_HOME")
            os.environ["CODEX_HOME"] = home
            try:
                self.assertEqual(detect_codex_model(start_dir=proj), "gpt-5.5")
            finally:
                if old is None:
                    os.environ.pop("CODEX_HOME", None)
                else:
                    os.environ["CODEX_HOME"] = old

    def test_no_config_none(self):
        with tempfile.TemporaryDirectory() as proj, tempfile.TemporaryDirectory() as home:
            self.assertIsNone(detect_codex_model(start_dir=proj, codex_home=home))


if __name__ == "__main__":
    unittest.main()
