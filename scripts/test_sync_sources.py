import json
import os
import tempfile
import unittest

import sync_sources as ss

OPENAI_ENTRYPOINTS = {
    "codex_models":    {"url": "https://developers.openai.com/codex/models", "role": "model-listing"},
    "codex_changelog": {"url": "https://developers.openai.com/codex/changelog", "role": "discovery"},
    "codex_prompting": {"url": "https://developers.openai.com/codex/prompting", "role": "prompting"},
    "codex_agents_md": {"url": "https://developers.openai.com/codex/guides/agents-md", "role": "prompting"},
    "latest_model":    {"url": "https://developers.openai.com/api/docs/guides/latest-model", "role": "prompting"},
}

MANIFEST = {
    "schema": 3,
    "providers": {
        "anthropic": {"allowlist_domains": ["platform.claude.com"],
                      "sync_entrypoints": {
                          "models_overview": {"url": "https://platform.claude.com/x", "role": "model-listing"}}},
        "openai": {"allowlist_domains": ["developers.openai.com", "platform.openai.com",
                                         "openai.com", "cookbook.openai.com"],
                   "note": "annotations are skipped",
                   "sync_entrypoints": OPENAI_ENTRYPOINTS},
    },
    "models": [
        {"id": "gpt-5.5", "provider": "openai", "family": "gpt-5", "status": "ga",
         "rubric": "references/rubrics/openai/gpt-5-5.md",
         "source_urls": ["https://developers.openai.com/codex/models"]},
        {"id": "gpt-5.4", "provider": "openai", "family": "gpt-5", "status": "limited",
         "rubric": None, "source_urls": ["https://developers.openai.com/codex/models"]},
    ],
}


def _manifest(tmp, obj=None):
    p = os.path.join(tmp, "models.json")
    with open(p, "w") as f:
        json.dump(obj or MANIFEST, f)
    return p


def _urls(plan):
    return [e["url"] for e in plan["fetch_urls"]]


class TestPlan(unittest.TestCase):
    def _plan(self, raw, obj=None):
        with tempfile.TemporaryDirectory() as tmp:
            return ss.plan(raw, _manifest(tmp, obj))

    def test_gpt54_family_baseline(self):
        p = self._plan("gpt-5.4")
        self.assertEqual(p["provider"], "openai")
        self.assertEqual(p["baseline_rubric"], "references/rubrics/openai/gpt-5-5.md")
        self.assertEqual(p["baseline_tier"], "family")
        self.assertFalse(p["baseline_is_self"])

    def test_gpt54_fetch_unions_prompting_and_model_listing(self):
        urls = _urls(self._plan("gpt-5.4"))
        self.assertIn("https://developers.openai.com/codex/prompting", urls)
        self.assertIn("https://developers.openai.com/codex/guides/agents-md", urls)
        self.assertIn("https://developers.openai.com/api/docs/guides/latest-model", urls)
        self.assertIn("https://developers.openai.com/codex/models", urls)

    def test_gpt54_excludes_changelog_discovery(self):
        p = self._plan("gpt-5.4")
        self.assertNotIn("https://developers.openai.com/codex/changelog", _urls(p))
        self.assertIn("https://developers.openai.com/codex/changelog",
                      [e["url"] for e in p["discovery_urls"]])

    def test_codex_models_deduped_once(self):
        # codex/models is both the model-listing entrypoint AND gpt-5.4's source_url
        urls = _urls(self._plan("gpt-5.4"))
        self.assertEqual(urls.count("https://developers.openai.com/codex/models"), 1)

    def test_model_listing_url_surfaced(self):
        self.assertEqual(self._plan("gpt-5.4")["model_listing_url"],
                         "https://developers.openai.com/codex/models")

    def test_self_rederive_exact_tier(self):
        p = self._plan("gpt-5.5")
        self.assertEqual(p["baseline_tier"], "exact")
        self.assertTrue(p["baseline_is_self"])

    def test_off_allowlist_source_url_dropped(self):
        obj = json.loads(json.dumps(MANIFEST))
        obj["models"][1]["source_urls"] = ["https://evil.com/x"]
        p = self._plan("gpt-5.4", obj)
        self.assertNotIn("https://evil.com/x", _urls(p))
        self.assertTrue(any(d["url"] == "https://evil.com/x" for d in p["dropped"]))

    def test_non_url_annotation_ignored(self):
        # the openai 'note' key is a string, not a {url,...} entry — must not crash or leak
        p = self._plan("gpt-5.4")
        self.assertTrue(all(u.startswith("https://") for u in _urls(p)))

    def test_unknown_id_empty_fetch_with_badge(self):
        p = self._plan("mistral-large")
        self.assertEqual(p["fetch_urls"], [])
        self.assertTrue(p["badge_reason"])

    def test_empty_id_no_crash(self):
        p = self._plan("")
        self.assertEqual(p["fetch_urls"], [])

    def test_sibling_gpt56_baseline_after_54_ships(self):
        # adding a gpt-5.4 rubric must not change the unknown-sibling family fallback
        obj = json.loads(json.dumps(MANIFEST))
        obj["models"][1]["rubric"] = "references/rubrics/openai/gpt-5-4.md"
        p = self._plan("gpt-5.6", obj)
        self.assertEqual(p["baseline_rubric"], "references/rubrics/openai/gpt-5-5.md")


class TestAllowed(unittest.TestCase):
    def _allowed(self, provider, url, obj=None):
        with tempfile.TemporaryDirectory() as tmp:
            return ss.allowed(provider, url, _manifest(tmp, obj))

    def test_allow_exact_and_subdomains(self):
        self.assertTrue(self._allowed("openai", "https://developers.openai.com/x"))
        self.assertTrue(self._allowed("openai", "https://cookbook.openai.com/x"))
        self.assertTrue(self._allowed("openai", "https://platform.openai.com/x"))      # *.openai.com
        self.assertTrue(self._allowed("openai", "https://a.developers.openai.com/x"))  # sub-subdomain

    def test_deny_scheme_userinfo_lookalike_spoof(self):
        self.assertFalse(self._allowed("openai", "http://developers.openai.com/x"))            # scheme
        self.assertFalse(self._allowed("openai", "https://developers.openai.com@evil.com/x"))  # userinfo
        self.assertFalse(self._allowed("openai", "https://notopenai.com/x"))                   # look-alike
        self.assertFalse(self._allowed("openai", "https://openai.com.evil.com/x"))             # suffix-spoof
        self.assertFalse(self._allowed("openai", "https://github.com/openai/codex"))           # off-allowlist

    def test_deny_cross_provider(self):
        self.assertFalse(self._allowed("anthropic", "https://developers.openai.com/x"))

    def test_case_insensitive_host(self):
        self.assertTrue(self._allowed("openai", "https://Developers.OpenAI.com/x"))

    def test_unknown_provider_denies(self):
        self.assertFalse(self._allowed("unknown", "https://developers.openai.com/x"))


if __name__ == "__main__":
    unittest.main()
