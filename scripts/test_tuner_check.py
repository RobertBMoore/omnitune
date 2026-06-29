import os, tempfile, json, unittest
import miniyaml
from tuner_check import check, manifest_problems, _audit_config_problems

EXAMPLE = '''project:
  name: "TrailGear"
  domain: "Direct-to-consumer outdoor gear"
skills:
  root: "skills/"
  agents: ""
routing:
  - skill: "product-blurb"
    keywords: ["product blurb", "blurb for the"]
  - skill: "spec-sheet"
    keywords: ["spec sheet"]
context_pointers:
  - when: "product-blurb"
    point_to: ["brand/voice.md"]
house_rules: "brand/voice.md"
reserved_decisions: ""
output:
  reports: "reports/"
  prompts: "docs/prompts/"
model_sync:
  channel: "badge"                 # badge | interrupt | manual
  target_model: ""
  snooze_default: "24h"
  regression_corpus: "omnitune/regression/"
'''


class TestMiniYaml(unittest.TestCase):
    def test_scalars_and_nesting(self):
        d = miniyaml.load(EXAMPLE)
        self.assertEqual(d["project"]["name"], "TrailGear")
        self.assertEqual(d["skills"]["root"], "skills/")
        self.assertEqual(d["skills"]["agents"], "")
        self.assertEqual(d["model_sync"]["channel"], "badge")
        self.assertEqual(d["model_sync"]["target_model"], "")
        self.assertEqual(d["output"]["reports"], "reports/")
        self.assertEqual(d["reserved_decisions"], "")
        self.assertEqual(d["house_rules"], "brand/voice.md")

    def test_block_list_of_maps(self):
        d = miniyaml.load(EXAMPLE)
        self.assertEqual(len(d["routing"]), 2)
        self.assertEqual(d["routing"][0]["skill"], "product-blurb")
        self.assertIn("blurb for the", d["routing"][0]["keywords"])
        self.assertEqual(d["routing"][1]["skill"], "spec-sheet")
        self.assertEqual(d["context_pointers"][0]["point_to"], ["brand/voice.md"])

    def test_inline_comment_not_cut_inside_quotes(self):
        d = miniyaml.load('key: "a # b"   # trailing\n')
        self.assertEqual(d["key"], "a # b")

    def test_comments_and_blanks(self):
        d = miniyaml.load("# c\nkey: val\n\n  # comment\nk2: v2\n")
        self.assertEqual(d["key"], "val")
        self.assertEqual(d["k2"], "v2")


def build_repo(tmp, config_text, skills=("product-blurb", "spec-sheet"), make_voice=True):
    for s in skills:
        os.makedirs(os.path.join(tmp, "skills", s), exist_ok=True)
        with open(os.path.join(tmp, "skills", s, "SKILL.md"), "w") as f:
            f.write("---\nname: %s\n---\n" % s)
    if make_voice:
        os.makedirs(os.path.join(tmp, "brand"), exist_ok=True)
        with open(os.path.join(tmp, "brand", "voice.md"), "w") as f:
            f.write("voice")
    with open(os.path.join(tmp, "omnitune.config.yaml"), "w") as f:
        f.write(config_text)
    return tmp


def write_models(tmp, ga_rubric_exists=True, add_pending_ga=False):
    rub_rel = "references/rubrics/anthropic/claude-opus-4-8.md"
    os.makedirs(os.path.join(tmp, "references", "rubrics", "anthropic"), exist_ok=True)
    with open(os.path.join(tmp, "references", "rubrics", "anthropic", "_core.md"), "w") as f:
        f.write("audit floor rule: a Critical caps the verdict. fail-closed clause.\n")
    if ga_rubric_exists:
        with open(os.path.join(tmp, rub_rel), "w") as f:
            f.write("rubric")
    models = [
        {"id": "claude-opus-4-8", "provider": "anthropic", "family": "opus",
         "status": "ga", "rubric": rub_rel},
        {"id": "claude-opus-4-7", "provider": "anthropic", "family": "opus",
         "status": "deprecated", "rubric": None},
    ]
    if add_pending_ga:
        models.append({"id": "claude-fable-5", "provider": "anthropic",
                       "family": "fable", "status": "ga", "rubric": None})
    p = os.path.join(tmp, "references", "models.json")
    with open(p, "w") as f:
        json.dump({"schema": 2,
                   "providers": {"anthropic": {"allowlist_domains": ["x"]}},
                   "models": models}, f)
    return p


class TestCheck(unittest.TestCase):
    def test_clean_repo_no_problems(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_repo(tmp, EXAMPLE)
            mp = write_models(tmp)
            self.assertEqual(check(tmp, EXAMPLE, mp), [])

    def test_missing_routing_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = EXAMPLE.replace('skill: "spec-sheet"', 'skill: "ghost-skill"')
            build_repo(tmp, cfg)  # builds product-blurb + spec-sheet dirs, not ghost-skill
            mp = write_models(tmp)
            probs = check(tmp, cfg, mp)
            self.assertTrue(any("ghost-skill" in p for p in probs), probs)

    def test_missing_pointer_and_house_rules(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_repo(tmp, EXAMPLE, make_voice=False)
            mp = write_models(tmp)
            probs = check(tmp, EXAMPLE, mp)
            self.assertTrue(any("voice.md" in p for p in probs), probs)

    def test_bad_channel(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = EXAMPLE.replace('channel: "badge"', 'channel: "loud"')
            build_repo(tmp, cfg)
            mp = write_models(tmp)
            probs = check(tmp, cfg, mp)
            self.assertTrue(any("channel" in p for p in probs), probs)

    def test_ga_model_broken_rubric_path_is_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_repo(tmp, EXAMPLE)
            mp = write_models(tmp, ga_rubric_exists=False)  # rubric path set but file absent
            probs = check(tmp, EXAMPLE, mp)
            self.assertTrue(any("rubric" in p.lower() for p in probs), probs)

    def test_ga_null_rubric_is_warning_not_problem(self):
        from tuner_check import manifest_warnings
        with tempfile.TemporaryDirectory() as tmp:
            build_repo(tmp, EXAMPLE)
            mp = write_models(tmp, add_pending_ga=True)  # fable-5 GA, rubric=null
            self.assertEqual(check(tmp, EXAMPLE, mp), [])  # not a hard failure
            warns = manifest_warnings(mp)
            self.assertTrue(any("claude-fable-5" in w for w in warns), warns)

    def test_missing_required_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = EXAMPLE.replace('  channel: "badge"                 # badge | interrupt | manual\n', '')
            build_repo(tmp, cfg)
            mp = write_models(tmp)
            probs = check(tmp, cfg, mp)
            self.assertTrue(any("model_sync.channel" in p for p in probs), probs)


def _write_manifest(tmp, models, providers=None):
    refs = os.path.join(tmp, "references")
    os.makedirs(refs, exist_ok=True)
    mj = {"schema": 2, "providers": providers or {
        "anthropic": {"allowlist_domains": ["platform.claude.com"]},
        "openai": {"allowlist_domains": ["developers.openai.com"]},
    }, "models": models}
    p = os.path.join(refs, "models.json")
    with open(p, "w") as f:
        json.dump(mj, f)
    return p


def _touch_rubric(tmp, rel, body="- rule [src]\n"):
    full = os.path.join(tmp, rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(body)


class TestManifestMatrix(unittest.TestCase):
    def test_missing_provider_is_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            mp = _write_manifest(tmp, [{"id": "gpt-5.5", "status": "ga",
                                        "rubric": "references/rubrics/openai/gpt-5-5.md"}])
            _touch_rubric(tmp, "references/rubrics/openai/gpt-5-5.md")
            probs = manifest_problems(mp)
            self.assertTrue(any("provider" in p for p in probs), probs)

    def test_provider_without_providers_entry_is_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            mp = _write_manifest(tmp,
                [{"id": "x", "provider": "acme", "status": "limited", "rubric": None}])
            probs = manifest_problems(mp)
            self.assertTrue(any("acme" in p for p in probs), probs)

    def test_rubric_outside_provider_dir_is_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            mp = _write_manifest(tmp, [{"id": "gpt-5.5", "provider": "openai",
                "status": "ga", "rubric": "references/rubrics/gpt-5-5.md"}])
            _touch_rubric(tmp, "references/rubrics/gpt-5-5.md")
            probs = manifest_problems(mp)
            self.assertTrue(any("provider dir" in p for p in probs), probs)

    def test_filename_must_match_normalized_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            mp = _write_manifest(tmp, [{"id": "gpt-5.5", "provider": "openai",
                "status": "ga", "rubric": "references/rubrics/openai/gpt5.md"}])
            _touch_rubric(tmp, "references/rubrics/openai/gpt5.md")
            probs = manifest_problems(mp)
            self.assertTrue(any("filename" in p for p in probs), probs)

    def test_citation_gate_flags_uncited_rule(self):
        with tempfile.TemporaryDirectory() as tmp:
            mp = _write_manifest(tmp, [{"id": "gpt-5.5", "provider": "openai",
                "status": "ga", "rubric": "references/rubrics/openai/gpt-5-5.md"}])
            _touch_rubric(tmp, "references/rubrics/openai/gpt-5-5.md",
                          body="---\ncitation_gate: strict\n---\n- a load-bearing rule with no source\n")
            probs = manifest_problems(mp)
            self.assertTrue(any("citation" in p for p in probs), probs)

    def test_citation_gate_passes_cited_rule(self):
        with tempfile.TemporaryDirectory() as tmp:
            mp = _write_manifest(tmp, [{"id": "gpt-5.5", "provider": "openai",
                "status": "ga", "rubric": "references/rubrics/openai/gpt-5-5.md"}])
            _touch_rubric(tmp, "references/rubrics/openai/gpt-5-5.md",
                          body="---\ncitation_gate: strict\n---\n- a cited rule [codex]\n")
            _touch_rubric(tmp, "references/rubrics/openai/_core.md",
                          body="floor rule fail-closed\n")
            self.assertEqual(manifest_problems(mp), [])

    def test_clean_manifest_no_problems(self):
        with tempfile.TemporaryDirectory() as tmp:
            mp = _write_manifest(tmp, [{"id": "gpt-5.5", "provider": "openai",
                "status": "ga", "rubric": "references/rubrics/openai/gpt-5-5.md"}])
            _touch_rubric(tmp, "references/rubrics/openai/gpt-5-5.md",
                          body="---\nextends: _core.md\n---\n- a cited rule [x]\n")
            _touch_rubric(tmp, "references/rubrics/openai/_core.md",
                          body="floor rule: a Critical caps the verdict. fail-closed clause.\n")
            self.assertEqual(manifest_problems(mp), [])

    def test_extends_target_missing_is_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            mp = _write_manifest(tmp, [{"id": "gpt-5.5", "provider": "openai",
                "status": "ga", "rubric": "references/rubrics/openai/gpt-5-5.md"}])
            _touch_rubric(tmp, "references/rubrics/openai/gpt-5-5.md",
                          body="---\nextends: _core.md\n---\n- r [x]\n")  # no _core.md created
            probs = manifest_problems(mp)
            self.assertTrue(any("extends" in p for p in probs), probs)

    def test_provider_core_missing_floor_is_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            mp = _write_manifest(tmp, [{"id": "gpt-5.5", "provider": "openai",
                "status": "ga", "rubric": "references/rubrics/openai/gpt-5-5.md"}])
            _touch_rubric(tmp, "references/rubrics/openai/gpt-5-5.md", body="- r [x]\n")
            _touch_rubric(tmp, "references/rubrics/openai/_core.md",
                          body="# core\nno safety content here\n")
            probs = manifest_problems(mp)
            self.assertTrue(any("floor-rule" in p for p in probs), probs)

    def test_valid_provider_missing_from_providers_map(self):
        # openai is an allowed provider but absent from the providers map -> allowlist problem,
        # and NOT a "not in" problem (isolates the allowlist check from the allowed-set check).
        with tempfile.TemporaryDirectory() as tmp:
            mp = _write_manifest(tmp,
                [{"id": "gpt-5.5", "provider": "openai", "status": "limited", "rubric": None}],
                providers={"anthropic": {"allowlist_domains": ["x"]}})
            probs = manifest_problems(mp)
            self.assertTrue(any("allowlist_domains" in p for p in probs), probs)
            self.assertFalse(any("not in" in p for p in probs), probs)


class TestAuditConfig(unittest.TestCase):
    def test_valid_audit_keys_ok(self):
        cfg = {"model_sync": {"audit_clean_rounds": 2, "audit_round_cap": 3,
                              "audit_material_severity": "high", "audit_panel_threshold": 3}}
        self.assertEqual(_audit_config_problems(cfg), [])

    def test_absent_keys_ok(self):
        self.assertEqual(_audit_config_problems({"model_sync": {"channel": "badge"}}), [])

    def test_clean_rounds_below_one(self):
        probs = _audit_config_problems({"model_sync": {"audit_clean_rounds": 0}})
        self.assertTrue(any("audit_clean_rounds" in p for p in probs), probs)

    def test_cap_below_clean_rounds(self):
        probs = _audit_config_problems({"model_sync": {"audit_clean_rounds": 3,
                                                       "audit_round_cap": 2}})
        self.assertTrue(any("audit_round_cap" in p for p in probs), probs)

    def test_material_too_strict(self):
        probs = _audit_config_problems({"model_sync": {"audit_material_severity": "critical"}})
        self.assertTrue(any("audit_material_severity" in p for p in probs), probs)

    def test_non_integer(self):
        probs = _audit_config_problems({"model_sync": {"audit_round_cap": "three"}})
        self.assertTrue(any("audit_round_cap" in p for p in probs), probs)


if __name__ == "__main__":
    unittest.main()
