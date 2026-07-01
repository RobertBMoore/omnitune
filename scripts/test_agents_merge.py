import os
import re
import tempfile
import unittest

import agents_merge as am

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestMerge(unittest.TestCase):
    def test_append_when_no_markers(self):
        out = am.merge("# Mine\n\nkeep me\n", "BLOCK")
        self.assertIn("# Mine", out)
        self.assertIn("keep me", out)
        self.assertIn(am.MARK_BEGIN, out)
        self.assertIn("BLOCK", out)
        self.assertIn(am.MARK_END, out)

    def test_create_from_empty(self):
        out = am.merge("", "BLOCK")
        self.assertTrue(out.startswith(am.MARK_BEGIN))
        self.assertIn("BLOCK", out)

    def test_idempotent(self):
        x = "# Mine\n\nkeep me\n"
        once = am.merge(x, "BLOCK")
        twice = am.merge(once, "BLOCK")
        self.assertEqual(once, twice)

    def test_updates_between_markers(self):
        once = am.merge("# Top\n", "OLD")
        updated = am.merge(once, "NEW")
        self.assertIn("NEW", updated)
        self.assertNotIn("OLD", updated)
        self.assertEqual(updated.count(am.MARK_BEGIN), 1)
        self.assertEqual(updated.count(am.MARK_END), 1)

    def test_preserves_out_of_marker_content(self):
        existing = am.merge("# Top matter\n", "BLOCK") + "\n## My own footer\n"
        updated = am.merge(existing, "BLOCK2")
        self.assertIn("# Top matter", updated)
        self.assertIn("## My own footer", updated)

    def test_install_creates_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as t:
            p = os.path.join(t, "AGENTS.md")
            am.install(p, "BLOCK")
            first = open(p, encoding="utf-8").read()
            am.install(p, "BLOCK")
            second = open(p, encoding="utf-8").read()
            self.assertEqual(first, second)
            self.assertIn("BLOCK", second)


class TestTemplate(unittest.TestCase):
    TPL = "deploy/codex/AGENTS.omnitune.md"

    def _text(self):
        with open(os.path.join(ROOT, self.TPL), encoding="utf-8") as f:
            return f.read()

    def test_operative_safety_phrases(self):
        low = self._text().lower()
        for p in ["never self-commit", "propose-only", "off-allowlist hop",
                  "multi_agent", "author_id", ".omnitune/skills/sync/skill.md"]:
            self.assertIn(p, low, "template missing operative phrase: %s" % p)

    def test_omnitune_paths_resolve_after_prefix_strip(self):
        text = self._text()
        toks = set(re.findall(r"\.omnitune/[\w./-]+\.(?:py|md|json)", text))
        missing = []
        for t in sorted(toks):
            rel = t[len(".omnitune/"):]
            if not os.path.exists(os.path.join(ROOT, rel)):
                missing.append(t)
        self.assertEqual(missing, [], "template names omnitune paths that don't exist: %s" % missing)


if __name__ == "__main__":
    unittest.main()
