import json, os, tempfile, unittest
from validate_plugin import validate

GOOD_MKT = {
    "name": "omnitune",
    "owner": {"name": "Robert Moore"},
    "plugins": [{"name": "omnitune", "source": "./", "description": "x"}],
}
GOOD_PLUGIN = {"name": "omnitune", "description": "x"}


def build(tmp, mkt=GOOD_MKT, plugin=GOOD_PLUGIN, write_mkt=True, write_plugin=True):
    cp = os.path.join(tmp, ".claude-plugin")
    os.makedirs(cp, exist_ok=True)
    if write_mkt:
        with open(os.path.join(cp, "marketplace.json"), "w") as f:
            json.dump(mkt, f)
    if write_plugin:
        with open(os.path.join(cp, "plugin.json"), "w") as f:
            json.dump(plugin, f)
    return tmp


class TestValidatePlugin(unittest.TestCase):
    def test_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            build(tmp)
            self.assertEqual(validate(tmp), [])

    def test_missing_marketplace(self):
        with tempfile.TemporaryDirectory() as tmp:
            build(tmp, write_mkt=False)
            self.assertTrue(any("marketplace.json is missing" in p for p in validate(tmp)))

    def test_plugin_version_pinned_is_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            build(tmp, plugin={"name": "omnitune", "version": "0.1.0"})
            probs = validate(tmp)
            self.assertTrue(any("must NOT pin 'version'" in p for p in probs), probs)

    def test_marketplace_entry_version_pinned_is_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            mkt = {"name": "omnitune", "owner": {"name": "R"},
                   "plugins": [{"name": "omnitune", "source": "./", "version": "0.1.0"}]}
            build(tmp, mkt=mkt)
            self.assertTrue(any("must NOT pin 'version'" in p for p in validate(tmp)))

    def test_wrong_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            mkt = {"name": "omnitune", "owner": {"name": "R"},
                   "plugins": [{"name": "omnitune", "source": "./plugins/x"}]}
            build(tmp, mkt=mkt)
            self.assertTrue(any("source must be './'" in p for p in validate(tmp)))

    def test_missing_owner(self):
        with tempfile.TemporaryDirectory() as tmp:
            mkt = {"name": "omnitune", "plugins": [{"name": "omnitune", "source": "./"}]}
            build(tmp, mkt=mkt)
            self.assertTrue(any("owner.name" in p for p in validate(tmp)))

    def test_no_prompt_tuner_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            mkt = {"name": "omnitune", "owner": {"name": "R"},
                   "plugins": [{"name": "other", "source": "./"}]}
            build(tmp, mkt=mkt)
            self.assertTrue(any("no plugin entry named 'omnitune'" in p for p in validate(tmp)))

    def test_missing_plugin(self):
        with tempfile.TemporaryDirectory() as tmp:
            build(tmp, write_plugin=False)
            self.assertTrue(any("plugin.json is missing" in p for p in validate(tmp)))

    def test_wrong_plugin_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            build(tmp, plugin={"name": "other-plugin"})
            self.assertTrue(any("'name' must be 'omnitune'" in p for p in validate(tmp)))

    def test_invalid_marketplace_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            build(tmp)
            cp = os.path.join(tmp, ".claude-plugin")
            with open(os.path.join(cp, "marketplace.json"), "w") as f:
                f.write("{ not json")
            probs = validate(tmp)
            self.assertTrue(any("marketplace: invalid JSON" in p for p in probs), probs)

    def test_invalid_plugin_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            build(tmp)
            cp = os.path.join(tmp, ".claude-plugin")
            with open(os.path.join(cp, "plugin.json"), "w") as f:
                f.write("{ not json")
            probs = validate(tmp)
            self.assertTrue(any("plugin: invalid JSON" in p for p in probs), probs)


if __name__ == "__main__":
    unittest.main()
