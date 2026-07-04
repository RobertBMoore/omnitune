import os
import tempfile
import unittest

import corpus_check as cc


class Floor(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.corpus = os.path.join(self.d, "regression")
        os.makedirs(self.corpus)

    def _add(self, *names):
        for n in names:
            open(os.path.join(self.corpus, n), "w").close()

    def test_under_floor(self):
        self._add("a.md", "b.md")
        r = cc.floor(self.corpus, min_items=5)
        self.assertFalse(r["ok"])
        self.assertEqual(r["count"], 2)
        self.assertEqual(r["reason"], cc.UNDER_FLOOR_REASON)

    def test_exactly_at_floor(self):
        self._add("a.md", "b.md", "c.md", "d.md", "e.md")
        r = cc.floor(self.corpus, min_items=5)
        self.assertTrue(r["ok"])
        self.assertEqual(r["reason"], "")

    def test_readme_excluded(self):
        self._add("README.md", "a.md")
        self.assertEqual(cc.floor(self.corpus, min_items=1)["count"], 1)

    def test_seed_candidates_listed(self):
        self._add("a.md")
        prompts = os.path.join(self.d, "prompts")
        os.makedirs(prompts)
        open(os.path.join(prompts, "p1.md"), "w").close()
        r = cc.floor(self.corpus, min_items=5, prompts_dir=prompts)
        self.assertIn("p1.md", r["seed_candidates"])

    def test_seed_writes_and_skips_existing(self):
        prompts = os.path.join(self.d, "prompts")
        os.makedirs(prompts)
        for n in ("p1.md", "p2.md", "p3.md"):
            open(os.path.join(prompts, n), "w").close()
        self._add("p1.md")  # already in corpus -> skipped
        written = cc.seed(self.corpus, prompts, 5)
        self.assertEqual(written, ["p2.md", "p3.md"])
        self.assertEqual(cc.floor(self.corpus, min_items=1)["count"], 3)

    def test_main_exit_codes(self):
        self._add("a.md")
        self.assertEqual(cc.main([self.corpus, "--floor", "5"]), 1)
        self._add("b.md", "c.md", "d.md", "e.md")
        self.assertEqual(cc.main([self.corpus, "--floor", "5"]), 0)


if __name__ == "__main__":
    unittest.main()
