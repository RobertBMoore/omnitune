import unittest
from rubric_ratchet import ratchet, analyze

OLD = """# Rubric — X
## Safety
You must not soften this. Never silently self-commit. Destructive actions are prohibited.
## Severity
This is a HIGH severity finding. Do not skip it.
## Calibration
Required: read the file first.
"""


class TestAnalyze(unittest.TestCase):
    def test_identical_no_findings(self):
        self.assertEqual(analyze(OLD, OLD), [])

    def test_added_rule_is_tightening(self):
        new = OLD + "\n## Extra\nYou must not do Y. Never do Z.\n"
        self.assertEqual(analyze(OLD, new), [])  # more hard rules, no removals

    def test_removed_section_flagged(self):
        new = OLD.replace("## Severity\nThis is a HIGH severity finding. Do not skip it.\n", "")
        f = analyze(OLD, new)
        self.assertTrue(any("removed section" in x and "severity" in x.lower() for x in f), f)

    def test_weakened_hard_token_flagged(self):
        new = OLD.replace("Never silently self-commit. ", "")
        f = analyze(OLD, new)
        self.assertTrue(any("never" in x.lower() for x in f), f)

    def test_severity_downgrade_flagged(self):
        new = OLD.replace("HIGH severity", "low severity")
        f = analyze(OLD, new)
        self.assertTrue(any("severity" in x.lower() for x in f), f)


class TestRatchet(unittest.TestCase):
    def test_identical_allows(self):
        self.assertEqual(ratchet(OLD, OLD)[0], "ALLOW")

    def test_tightening_allows(self):
        new = OLD + "\nNever do the bad thing.\n"
        self.assertEqual(ratchet(OLD, new)[0], "ALLOW")

    def test_loosening_blocks(self):
        new = OLD.replace("Destructive actions are prohibited.", "")
        verdict, findings = ratchet(OLD, new)
        self.assertEqual(verdict, "BLOCK")
        self.assertTrue(findings)

    def test_loosening_with_approval_allows_but_reports(self):
        new = OLD.replace("Destructive actions are prohibited.", "")
        verdict, findings = ratchet(OLD, new, approved=True)
        self.assertEqual(verdict, "ALLOW")
        self.assertTrue(findings)  # the loosening is still reported


if __name__ == "__main__":
    unittest.main()
