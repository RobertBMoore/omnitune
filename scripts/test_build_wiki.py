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


if __name__ == "__main__":
    unittest.main()
