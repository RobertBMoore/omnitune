import os
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


if __name__ == "__main__":
    unittest.main()
