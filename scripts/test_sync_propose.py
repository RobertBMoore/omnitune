import json
import os
import tempfile
import unittest

import sync_propose
import version_log


def _models_json(tmp, models=None):
    """Minimal manifest fixture mirroring test_resolve_model conventions."""
    mj = {
        "schema": 3,
        "providers": {
            "anthropic": {
                "allowlist_domains": ["platform.claude.com"],
                "sync_entrypoints": {
                    "models_overview": {"url": "https://platform.claude.com/docs/overview",
                                        "role": "model-listing"},
                    "prompting": {"url": "https://platform.claude.com/docs/prompting",
                                  "role": "prompting"},
                },
            },
            "xai": {
                "allowlist_domains": ["docs.x.ai"],
                "sync_entrypoints": {
                    "models": {"url": "https://docs.x.ai/developers/models",
                               "role": "model-listing"},
                },
            },
        },
        "models": models if models is not None else [
            {"id": "claude-opus-4-8", "provider": "anthropic", "family": "opus",
             "status": "ga", "rubric": "references/rubrics/anthropic/claude-opus-4-8.md",
             "source_urls": ["https://platform.claude.com/docs/opus"]},
            {"id": "grok-4.3", "provider": "xai", "family": "grok-4",
             "status": "ga", "rubric": None, "source_urls": []},
        ],
    }
    p = os.path.join(tmp, "models.json")
    with open(p, "w") as f:
        json.dump(mj, f)
    return p


class TestProposal(unittest.TestCase):
    def test_existing_rubric_model_is_update(self):
        with tempfile.TemporaryDirectory() as t:
            p = _models_json(t)
            out = sync_propose.propose("claude-opus-4-8", p, date="2026-07-03")
            self.assertEqual(out["action"], "update")
            self.assertEqual(out["provider"], "anthropic")
            self.assertEqual(out["normalized_id"], "claude-opus-4-8")

    def test_known_model_without_rubric_is_add(self):
        with tempfile.TemporaryDirectory() as t:
            p = _models_json(t)
            out = sync_propose.propose("grok-4.3", p, date="2026-07-03")
            self.assertEqual(out["action"], "add")

    def test_frontmatter_template_fields(self):
        with tempfile.TemporaryDirectory() as t:
            p = _models_json(t)
            fm = sync_propose.propose("claude-opus-4-8", p, date="2026-07-03")["frontmatter_template"]
            self.assertEqual(fm["model"], "claude-opus-4-8")
            self.assertEqual(fm["family"], "opus")
            self.assertEqual(fm["status"], "ga")
            self.assertEqual(fm["lastSynced"], "2026-07-03")
            self.assertEqual(fm["extends"], "_core.md")
            self.assertTrue(fm["sources"])  # non-empty, from the fetch plan

    def test_frontmatter_sources_match_fetch_plan(self):
        with tempfile.TemporaryDirectory() as t:
            p = _models_json(t)
            out = sync_propose.propose("claude-opus-4-8", p, date="2026-07-03")
            plan_urls = [u["url"] for u in out["fetch_plan"]["fetch_urls"]]
            self.assertEqual(out["frontmatter_template"]["sources"], plan_urls)

    def test_version_log_template_is_recordable(self):
        with tempfile.TemporaryDirectory() as t:
            p = _models_json(t)
            entry = sync_propose.propose("grok-4.3", p, date="2026-07-03")["version_log_template"]
            log = os.path.join(t, "version-log.json")
            version_log.record(log, entry)  # must not raise
            with open(log) as f:
                self.assertEqual(len(json.load(f)["entries"]), 1)

    def test_unknown_model_asks_two_key_question(self):
        with tempfile.TemporaryDirectory() as t:
            p = _models_json(t)
            out = sync_propose.propose("claude-zephyr-9", p, date="2026-07-03")
            qs = " ".join(q["q"] for q in out["open_questions"])
            self.assertIn("model-listing", qs.lower().replace("model listing", "model-listing"))

    def test_no_prompting_entrypoint_flags_derived_tier(self):
        with tempfile.TemporaryDirectory() as t:
            p = _models_json(t)  # xai has no prompting-role entrypoint
            out = sync_propose.propose("grok-4.3", p, date="2026-07-03")
            qs = " ".join(q["q"] for q in out["open_questions"]).lower()
            self.assertIn("prompting", qs)

    def test_deterministic(self):
        with tempfile.TemporaryDirectory() as t:
            p = _models_json(t)
            a = sync_propose.propose("grok-4.3", p, date="2026-07-03")
            b = sync_propose.propose("grok-4.3", p, date="2026-07-03")
            self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))

    def test_draft_fields_are_placeholders(self):
        with tempfile.TemporaryDirectory() as t:
            p = _models_json(t)
            out = sync_propose.propose("grok-4.3", p, date="2026-07-03")
            self.assertEqual(out["rubric_draft_preview"], "")
            self.assertEqual(out["behavioral_diff_summary"], "")


class TestCli(unittest.TestCase):
    def test_cli_prints_json(self):
        with tempfile.TemporaryDirectory() as t:
            p = _models_json(t)
            import io
            from contextlib import redirect_stdout
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = sync_propose.main(["grok-4.3", p, "--date", "2026-07-03"])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(buf.getvalue())["normalized_id"], "grok-4.3")

    def test_cli_bad_args(self):
        self.assertEqual(sync_propose.main([]), 2)


if __name__ == "__main__":
    unittest.main()
