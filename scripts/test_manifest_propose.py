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
