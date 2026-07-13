import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS = os.path.join(ROOT, "tuner", "regression")
FLOOR = 5
CLASSES = {"command", "code", "factual-terse", "creative-brief", "adversarial-eval",
           "skill-audit", "goal-pack"}
MODES = {"A", "B", "C"}


def _fixtures():
    if not os.path.isdir(CORPUS):
        return []
    return [f for f in sorted(os.listdir(CORPUS))
            if f.endswith(".md") and f != "README.md"]


def _frontmatter(path):
    """Return {key: value} from a leading --- ... --- block, or {}."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


class TestRegressionCorpus(unittest.TestCase):
    def test_corpus_meets_floor(self):
        n = len(_fixtures())
        self.assertGreaterEqual(n, FLOOR,
                                "regression corpus has %d fixtures; floor is %d" % (n, FLOOR))

    def test_each_fixture_has_valid_frontmatter(self):
        for f in _fixtures():
            fm = _frontmatter(os.path.join(CORPUS, f))
            self.assertIn(fm.get("class"), CLASSES, "%s: bad/missing class" % f)
            self.assertIn(fm.get("mode"), MODES, "%s: bad/missing mode" % f)

    def test_covers_all_classes(self):
        seen = {_frontmatter(os.path.join(CORPUS, f)).get("class") for f in _fixtures()}
        missing = sorted(CLASSES - seen)
        self.assertEqual(missing, [], "regression corpus missing classes: %s" % missing)


if __name__ == "__main__":
    unittest.main()
