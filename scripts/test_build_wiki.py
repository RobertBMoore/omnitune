import json
import os
import tempfile
import unittest

import build_wiki_html as bw


def _files(tmp, models, entries):
    mp = os.path.join(tmp, "models.json")
    lp = os.path.join(tmp, "version-log.json")
    with open(mp, "w") as f:
        json.dump({"models": models}, f)
    with open(lp, "w") as f:
        json.dump({"schema": 1, "entries": entries}, f)
    return mp, lp


class TestPageRegistry(unittest.TestCase):
    def test_tune_goal_page_is_in_navigation(self):
        self.assertIn(("Tune-Goal.md", "tune-goal", "Tune Goal"), bw.PAGES)


class TestModelsSection(unittest.TestCase):
    def test_renders_row_per_model(self):
        with tempfile.TemporaryDirectory() as t:
            mp, lp = _files(
                t,
                [{"id": "gpt-5.5", "provider": "openai", "status": "ga"},
                 {"id": "claude-opus-4-8", "provider": "anthropic", "status": "ga"}],
                [{"date": "2026-06-29", "model_id": "gpt-5.5", "action": "add",
                  "last_synced": "2026-04-23", "source_urls": ["u1", "u2"]}])
            out = bw._models_section(mp, lp)
            self.assertIn("gpt-5.5", out)
            self.assertIn("openai", out)
            self.assertIn("2026-04-23", out)        # last_synced pulled from the log
            self.assertEqual(out.count("<tr>"), 3)  # header + 2 model rows

    def test_empty_log_does_not_raise(self):
        with tempfile.TemporaryDirectory() as t:
            mp, lp = _files(t, [{"id": "gpt-5.5", "provider": "openai", "status": "ga"}], [])
            self.assertIn("gpt-5.5", bw._models_section(mp, lp))

    def test_missing_files_no_raise(self):
        out = bw._models_section("/no/models.json", "/no/log.json")
        self.assertIn("<table>", out)  # empty table, no crash


class TestCheckMode(unittest.TestCase):
    """--check compares a fresh build against wiki/index.html (CI freshness gate)."""

    FRESH = "<html>fresh</html>"

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._wiki, self._build = bw.WIKI, bw.build
        bw.WIKI = self._tmp.name
        bw.build = lambda: self.FRESH  # build() has its own tests; isolate the CLI logic
        self.out = os.path.join(self._tmp.name, "index.html")

    def tearDown(self):
        bw.WIKI, bw.build = self._wiki, self._build
        self._tmp.cleanup()

    def test_check_ok_when_committed_html_is_fresh(self):
        with open(self.out, "w", encoding="utf-8") as f:
            f.write(self.FRESH)
        self.assertEqual(bw.main(["--check"]), 0)

    def test_check_fails_when_committed_html_is_stale(self):
        with open(self.out, "w", encoding="utf-8") as f:
            f.write("<html>old</html>")
        self.assertEqual(bw.main(["--check"]), 1)

    def test_check_fails_when_html_missing(self):
        self.assertEqual(bw.main(["--check"]), 1)

    def test_check_does_not_write(self):
        with open(self.out, "w", encoding="utf-8") as f:
            f.write("<html>old</html>")
        bw.main(["--check"])
        with open(self.out, encoding="utf-8") as f:
            self.assertEqual(f.read(), "<html>old</html>")

    def test_default_mode_writes_file(self):
        self.assertEqual(bw.main([]), 0)
        with open(self.out, encoding="utf-8") as f:
            self.assertEqual(f.read(), self.FRESH)

    def test_unknown_flag_fails_instead_of_writing(self):
        self.assertEqual(bw.main(["--help"]), 2)
        self.assertFalse(os.path.exists(self.out))


if __name__ == "__main__":
    unittest.main()
