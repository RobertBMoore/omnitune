import json
import os
import tempfile
import unittest

from resolve_model import normalize, infer_provider, resolve

MANIFEST = {
    "schema": 2,
    "providers": {
        "anthropic": {"allowlist_domains": ["platform.claude.com"]},
        "openai": {"allowlist_domains": ["developers.openai.com"]},
    },
    "models": [
        {"id": "claude-opus-4-8", "provider": "anthropic", "family": "opus",
         "status": "ga", "rubric": "references/rubrics/anthropic/claude-opus-4-8.md"},
        {"id": "claude-haiku-4-5", "provider": "anthropic", "family": "haiku",
         "status": "ga", "rubric": "references/rubrics/anthropic/claude-haiku-4-5.md"},
        {"id": "gpt-5.5", "provider": "openai", "family": "gpt-5",
         "status": "ga", "rubric": "references/rubrics/openai/gpt-5-5.md"},
        {"id": "gpt-5.4", "provider": "openai", "family": "gpt-5",
         "status": "limited", "rubric": None},
        {"id": "gpt-5.2", "provider": "openai", "family": "gpt-5",
         "status": "deprecated", "rubric": None},
    ],
}


def _manifest(tmp):
    p = os.path.join(tmp, "models.json")
    with open(p, "w") as f:
        json.dump(MANIFEST, f)
    return p


class TestNormalize(unittest.TestCase):
    def test_passthrough_keeps_dotted_minor(self):
        self.assertEqual(normalize("gpt-5.5"), "gpt-5.5")

    def test_lowercases(self):
        self.assertEqual(normalize("GPT-5.5"), "gpt-5.5")

    def test_strips_bracket_suffix(self):
        self.assertEqual(normalize("claude-opus-4-8[1m]"), "claude-opus-4-8")

    def test_strips_compact_date(self):
        self.assertEqual(normalize("claude-haiku-4-5-20251001"), "claude-haiku-4-5")

    def test_strips_dashed_date(self):
        self.assertEqual(normalize("gpt-5.5-2026-06-01"), "gpt-5.5")

    def test_strips_vendor_namespace(self):
        self.assertEqual(normalize("openai/gpt-5.5"), "gpt-5.5")

    def test_extracts_finetune_base(self):
        self.assertEqual(normalize("ft:gpt-4o:acme::abc123"), "gpt-4o")

    def test_preserves_role_suffix(self):
        self.assertEqual(normalize("gpt-5.4-mini"), "gpt-5.4-mini")

    def test_empty(self):
        self.assertEqual(normalize(""), "")


class TestInferProvider(unittest.TestCase):
    def test_anthropic(self):
        self.assertEqual(infer_provider("claude-opus-4-8"), "anthropic")

    def test_openai_gpt(self):
        self.assertEqual(infer_provider("gpt-5.5"), "openai")

    def test_openai_o_series(self):
        self.assertEqual(infer_provider("o3"), "openai")

    def test_openai_chatgpt(self):
        self.assertEqual(infer_provider("chatgpt-4o-latest"), "openai")

    def test_xai_grok(self):
        self.assertEqual(infer_provider("grok-build-0.1"), "xai")

    def test_xai_grok_dotted(self):
        self.assertEqual(infer_provider("grok-4.3"), "xai")

    def test_unknown(self):
        self.assertEqual(infer_provider("mistral-large"), "unknown")


class TestResolve(unittest.TestCase):
    def _resolve(self, raw):
        with tempfile.TemporaryDirectory() as tmp:
            return resolve(raw, _manifest(tmp))

    def test_exact_openai(self):
        r = self._resolve("gpt-5.5")
        self.assertEqual(r["provider"], "openai")
        self.assertEqual(r["rubric_path"], "references/rubrics/openai/gpt-5-5.md")
        self.assertEqual(r["fallback_tier"], "exact")

    def test_exact_after_date_strip(self):
        self.assertEqual(self._resolve("gpt-5.5-2026-06-01")["fallback_tier"], "exact")

    def test_exact_after_vendor_strip(self):
        self.assertEqual(self._resolve("openai/gpt-5.5")["rubric_path"],
                         "references/rubrics/openai/gpt-5-5.md")

    def test_known_null_rubric_falls_back_within_family(self):
        r = self._resolve("gpt-5.4")
        self.assertEqual(r["fallback_tier"], "family")
        self.assertEqual(r["rubric_path"], "references/rubrics/openai/gpt-5-5.md")
        self.assertIn("gpt-5.5", r["badge_reason"])

    def test_unknown_openai_id_same_family(self):
        r = self._resolve("gpt-5.4-mini")
        self.assertEqual(r["provider"], "openai")
        self.assertEqual(r["fallback_tier"], "family")
        self.assertEqual(r["rubric_path"], "references/rubrics/openai/gpt-5-5.md")

    def test_unknown_openai_no_family_uses_core(self):
        r = self._resolve("o3")
        self.assertEqual(r["provider"], "openai")
        self.assertEqual(r["fallback_tier"], "core")
        self.assertEqual(r["rubric_path"], "references/rubrics/openai/_core.md")

    def test_finetune_routes_openai(self):
        r = self._resolve("ft:gpt-4o:acme::abc123")
        self.assertEqual(r["provider"], "openai")
        self.assertEqual(r["fallback_tier"], "core")

    def test_claude_unchanged_with_bracket(self):
        r = self._resolve("claude-opus-4-8[1m]")
        self.assertEqual(r["provider"], "anthropic")
        self.assertEqual(r["rubric_path"], "references/rubrics/anthropic/claude-opus-4-8.md")
        self.assertEqual(r["fallback_tier"], "exact")

    def test_unknown_provider_cross_provider_terminal(self):
        r = self._resolve("mistral-large")
        self.assertEqual(r["provider"], "unknown")
        self.assertEqual(r["fallback_tier"], "cross-provider")
        self.assertEqual(r["rubric_path"], "references/rubrics/anthropic/claude-opus-4-8.md")
        self.assertIn("verify", r["badge_reason"].lower())

    def test_never_crashes_on_empty(self):
        r = self._resolve("")
        self.assertEqual(r["fallback_tier"], "cross-provider")

    def test_missing_manifest_returns_none_tier(self):
        r = resolve("gpt-5.5", "/no/such/models.json")
        self.assertEqual(r["fallback_tier"], "none")
        self.assertIsNone(r["rubric_path"])

    def test_result_has_exact_keys(self):
        r = self._resolve("gpt-5.5")
        self.assertEqual(
            set(r.keys()),
            {"provider", "normalized_id", "rubric_path", "fallback_tier", "badge_reason"})

    def test_exact_xai_grok_build(self):
        manifest = {
            "schema": 3,
            "providers": {"xai": {"allowlist_domains": ["docs.x.ai"]}},
            "models": [
                {"id": "grok-build-0.1", "provider": "xai", "family": "grok-build",
                 "status": "ga", "rubric": "references/rubrics/xai/grok-build-0-1.md"},
                {"id": "grok-4.3", "provider": "xai", "family": "grok-4",
                 "status": "ga", "rubric": None},
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "models.json")
            with open(p, "w") as f:
                json.dump(manifest, f)
            r = resolve("grok-build-0.1", p)
            self.assertEqual(r["provider"], "xai")
            self.assertEqual(r["fallback_tier"], "exact")
            self.assertEqual(r["rubric_path"], "references/rubrics/xai/grok-build-0-1.md")
            # grok-4.3 (different family, no rubric) falls to the xai core, not cross-provider.
            r2 = resolve("grok-4.3", p)
            self.assertEqual(r2["provider"], "xai")
            self.assertEqual(r2["fallback_tier"], "core")
            self.assertEqual(r2["rubric_path"], "references/rubrics/xai/_core.md")

    def test_family_fallback_prefers_higher_minor(self):
        manifest = {
            "schema": 2,
            "providers": {"openai": {"allowlist_domains": ["developers.openai.com"]}},
            "models": [
                {"id": "gpt-5.9", "provider": "openai", "family": "gpt-5",
                 "status": "ga", "rubric": "references/rubrics/openai/gpt-5-9.md"},
                {"id": "gpt-5.10", "provider": "openai", "family": "gpt-5",
                 "status": "ga", "rubric": "references/rubrics/openai/gpt-5-10.md"},
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "models.json")
            with open(p, "w") as f:
                json.dump(manifest, f)
            r = resolve("gpt-5.11-mini", p)  # unknown id, family gpt-5
        self.assertEqual(r["fallback_tier"], "family")
        self.assertEqual(r["rubric_path"], "references/rubrics/openai/gpt-5-10.md")


if __name__ == "__main__":
    unittest.main()
