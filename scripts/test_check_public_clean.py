import os, tempfile, unittest
from check_public_clean import scan

def write(root, rel, text):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        f.write(text)

class TestScan(unittest.TestCase):
    def test_clean_tree_passes(self):
        with tempfile.TemporaryDirectory() as t:
            write(t, "README.md", "# Omnitune\nA model-agnostic tuner.\n")
            self.assertEqual(scan(t, denylist=[]), [])

    def test_denylist_term_flagged(self):
        with tempfile.TemporaryDirectory() as t:
            write(t, "x.yaml", "name: Enchanted Fairies\n")
            hits = scan(t, denylist=["Enchanted Fairies"])
            self.assertTrue(any("x.yaml" in h and "Enchanted Fairies" in h for h in hits), hits)

    def test_denylist_case_insensitive(self):
        with tempfile.TemporaryDirectory() as t:
            write(t, "x.md", "aileen's voice\n")
            self.assertTrue(scan(t, denylist=["AILEEN"]))

    def test_internal_email_flagged_by_default(self):
        with tempfile.TemporaryDirectory() as t:
            write(t, "m.json", '"email": "agent001@digitalresearchgroup.com"\n')
            hits = scan(t, denylist=[])
            self.assertTrue(any("digitalresearchgroup.com" in h for h in hits), hits)

    def test_private_key_flagged(self):
        with tempfile.TemporaryDirectory() as t:
            write(t, "k", "-----BEGIN RSA PRIVATE KEY-----\n")
            self.assertTrue(scan(t, denylist=[]))

    def test_excluded_paths_not_scanned(self):
        with tempfile.TemporaryDirectory() as t:
            write(t, "docs/superpowers/spec.md", "Enchanted Fairies\n")
            write(t, ".git/x", "Enchanted Fairies\n")
            self.assertEqual(scan(t, denylist=["Enchanted Fairies"]), [])

    def test_scanner_files_excluded(self):
        with tempfile.TemporaryDirectory() as t:
            write(t, "scripts/check_public_clean.py", "Enchanted Fairies pattern\n")
            write(t, "scripts/test_check_public_clean.py", "Enchanted Fairies\n")
            self.assertEqual(scan(t, denylist=["Enchanted Fairies"]), [])

    def test_denylist_file_itself_excluded(self):
        with tempfile.TemporaryDirectory() as t:
            write(t, "scripts/.public-denylist.txt", "Enchanted Fairies\n")
            self.assertEqual(scan(t, denylist=["Enchanted Fairies"]), [])

if __name__ == "__main__":
    unittest.main()
