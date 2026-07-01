import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # scripts/ -> repo root
STUB = "skills/omnitune/references/codex-tools.md"


def _read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


class TestExists(unittest.TestCase):
    def test_agents_md_at_root(self):
        self.assertTrue(os.path.exists(os.path.join(ROOT, "AGENTS.md")), "AGENTS.md missing at repo root")


class TestReferentialIntegrity(unittest.TestCase):
    def test_referenced_paths_resolve(self):
        text = _read("AGENTS.md")
        toks = set(re.findall(r"[\w./-]+\.(?:py|md|json|yml)", text))
        prefixes = ("scripts/", "skills/", ".github/")
        paths = sorted(t for t in toks if t.startswith(prefixes))
        missing = [t for t in paths if not os.path.exists(os.path.join(ROOT, t))]
        self.assertEqual(missing, [], "AGENTS.md references missing paths: %s" % missing)


class TestSafetyPhrases(unittest.TestCase):
    def test_operative_phrases_present(self):
        low = _read("AGENTS.md").lower()
        for p in ["never self-commit", "propose-only", "multi_agent", "author_id", "skills/sync/skill.md"]:
            self.assertIn(p, low, "AGENTS.md missing operative safety phrase: %s" % p)

    def test_per_hop_fence_phrase(self):
        low = _read("AGENTS.md").lower()
        self.assertTrue("off-allowlist hop" in low or "redirect hop" in low,
                        "AGENTS.md missing a per-hop fence phrase")


class TestToolMappingCompleteness(unittest.TestCase):
    def test_canonical_tool_names_present(self):
        text = _read("AGENTS.md")
        for name in ["Bash", "Read", "Write", "Edit", "Glob", "spawn_agent", "update_plan", "WebFetch"]:
            self.assertIn(name, text, "AGENTS.md tool mapping missing: %s" % name)


class TestScopeNote(unittest.TestCase):
    def test_consumer_repo_scope_sentence(self):
        low = _read("AGENTS.md").lower()
        self.assertIn("consumer", low)
        self.assertTrue("d2b-2" in low or "not omnitune" in low,
                        "AGENTS.md missing the consumer-repo scope caveat")


class TestStubIntegrity(unittest.TestCase):
    def test_stub_short_and_points_to_agents(self):
        text = _read(STUB)
        nonblank = [ln for ln in text.splitlines() if ln.strip()]
        self.assertLessEqual(len(nonblank), 5, "codex-tools.md stub should be <=5 non-blank lines")
        self.assertIn("AGENTS.md", text, "stub must point to AGENTS.md")

    def test_stub_has_no_operative_content(self):
        text = _read(STUB)
        for op in ["sync_sources.allowed", "spawn_agent"]:
            self.assertNotIn(op, text, "stub retains operative content: %s" % op)


class TestCiRegistration(unittest.TestCase):
    def test_registered_in_validate_yml(self):
        self.assertIn("test_agents_md", _read(".github/workflows/validate.yml"))


if __name__ == "__main__":
    unittest.main()
