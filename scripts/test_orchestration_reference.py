"""Traceability + template integrity for the Mode C orchestration reference.

Fails if any of the 10 audit-finding IDs (P0-1..P3-9) or 15 template-rule IDs
(T1..T15) is missing from the traceability table in
skills/omnitune/references/orchestration-pack.md, or maps to an empty clause
cell. Also asserts the two pack-template files exist and are runnable
(record_check.py py_compiles; staleness_watchdog.sh passes bash -n).
"""
import os
import py_compile
import re
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(ROOT, "skills", "omnitune", "references", "orchestration-pack.md")
TEMPLATES = os.path.join(ROOT, "skills", "omnitune", "references", "pack-templates")
AUDIT_IDS = {"P0-1", "P0-2", "P0-3", "P1-3", "P1-4", "P1-5", "P1-6",
             "P2-7", "P2-8", "P3-9"}
RULE_IDS = {"T%d" % i for i in range(1, 16)}


def _table_rows():
    """Return {ID: clause-cell} for traceability rows `| <ID> | <clause> |`."""
    with open(REF, encoding="utf-8") as f:
        text = f.read()
    rows = {}
    for line in text.splitlines():
        m = re.match(r"^\|\s*(P\d+-\d+|T\d+)\s*\|\s*(.*?)\s*\|\s*$", line)
        if m:
            rows[m.group(1)] = m.group(2)
    return rows


class TestTraceabilityTable(unittest.TestCase):
    def test_reference_exists(self):
        self.assertTrue(os.path.exists(REF), "missing %s" % REF)

    def test_every_audit_finding_mapped(self):
        missing = sorted(AUDIT_IDS - set(_table_rows()))
        self.assertEqual(missing, [], "audit findings missing from traceability table: %s" % missing)

    def test_every_template_rule_mapped(self):
        missing = sorted(RULE_IDS - set(_table_rows()), key=lambda t: int(t[1:]))
        self.assertEqual(missing, [], "template rules missing from traceability table: %s" % missing)

    def test_no_empty_clause_cells(self):
        rows = _table_rows()
        for rid in sorted(AUDIT_IDS | RULE_IDS):
            cell = rows.get(rid, "")
            self.assertTrue(cell and set(cell) - {"-", ":", " "},
                            "traceability row %s has an empty clause cell" % rid)

    def test_full_row_count(self):
        present = set(_table_rows()) & (AUDIT_IDS | RULE_IDS)
        self.assertEqual(len(present), 25,
                         "expected 25 traceability rows, found %d" % len(present))


class TestPackTemplates(unittest.TestCase):
    def test_record_check_compiles(self):
        path = os.path.join(TEMPLATES, "record_check.py")
        self.assertTrue(os.path.exists(path), "missing %s" % path)
        with tempfile.TemporaryDirectory() as td:
            py_compile.compile(path, cfile=os.path.join(td, "record_check.pyc"),
                               doraise=True)

    def test_watchdog_bash_syntax(self):
        path = os.path.join(TEMPLATES, "staleness_watchdog.sh")
        self.assertTrue(os.path.exists(path), "missing %s" % path)
        r = subprocess.run(["bash", "-n", path], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, "bash -n failed: %s" % r.stderr)


if __name__ == "__main__":
    unittest.main()
