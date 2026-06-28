import os, tempfile, json, unittest
import miniyaml
from tuner_check import check

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
    rub_rel = "references/rubrics/claude-opus-4-8.md"
    os.makedirs(os.path.join(tmp, "references", "rubrics"), exist_ok=True)
    if ga_rubric_exists:
        with open(os.path.join(tmp, rub_rel), "w") as f:
            f.write("rubric")
    models = [
        {"id": "claude-opus-4-8", "status": "ga", "rubric": rub_rel},
        {"id": "claude-opus-4-7", "status": "deprecated", "rubric": None},
    ]
    if add_pending_ga:
        models.append({"id": "claude-fable-5", "status": "ga", "rubric": None})
    p = os.path.join(tmp, "references", "models.json")
    with open(p, "w") as f:
        json.dump({"models": models}, f)
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


if __name__ == "__main__":
    unittest.main()
