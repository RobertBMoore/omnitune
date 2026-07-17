"""Traceability + template integrity for the Mode C orchestration reference.

Fails if any of the 10 audit-finding IDs (P0-1..P3-9) or 15 template-rule IDs
(T1..T15) is missing from the traceability table in
skills/omnitune/references/orchestration-pack.md, or maps to an empty clause
cell. Also asserts the two pack-template files exist and are runnable
(record_check.py py_compiles; staleness_watchdog.sh passes bash -n).

Guards the reflection protocol too: reflection-protocol.md must exist, carry
every reflection-contract point R1..R7 in its contract table with a non-empty
cell, and be pointed at by orchestration-pack.md's reflection clause — so
demoting the local-Dream contract to prose, or dropping a contract point, fails.
"""
import importlib.util
import os
import py_compile
import re
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(ROOT, "skills", "omnitune", "references", "orchestration-pack.md")
REFLECT = os.path.join(ROOT, "skills", "omnitune", "references", "reflection-protocol.md")
TEMPLATES = os.path.join(ROOT, "skills", "omnitune", "references", "pack-templates")
REFERENCES = os.path.join(ROOT, "skills", "omnitune", "references")
DELEGATION_TIERS = os.path.join(REFERENCES, "delegation-tiers.md")
AGENT_TEMPLATE = os.path.join(REFERENCES, "agent-md-template.md")
PROTOCOL = os.path.join(ROOT, "skills", "omnitune", "tune-goal-protocol.md")
RUBRICS = os.path.join(REFERENCES, "rubrics")
AUDIT_IDS = {"P0-1", "P0-2", "P0-3", "P1-3", "P1-4", "P1-5", "P1-6",
             "P2-7", "P2-8", "P3-9"}
RULE_IDS = {"T%d" % i for i in range(1, 16)}
REFLECT_IDS = {"R%d" % i for i in range(1, 8)}
# Topology-contract points (X1..) — the counterpart to the recording contract,
# restored/parameterized from the deleted team-design layer. Grows by phase; the
# count assertion below is the current total.
TOPOLOGY_IDS = {"X%d" % i for i in range(1, 8)}


def _table_rows(path=REF):
    """Return {ID: clause-cell} for table rows `| <ID> | <clause> |`.

    IDs are audit findings (P0-1), template rules (T1), reflection-contract
    points (R1), or topology-contract points (X1) — enough to parse every
    reference file's tables.
    """
    with open(path, encoding="utf-8") as f:
        text = f.read()
    rows = {}
    for line in text.splitlines():
        m = re.match(r"^\|\s*(P\d+-\d+|T\d+|R\d+|X\d+)\s*\|\s*(.*?)\s*\|\s*$", line)
        if m:
            rows[m.group(1)] = m.group(2)
    return rows


def _rubric_files():
    """Every rubric markdown file under references/rubrics/ (core + per-model)."""
    out = []
    for dirpath, _dirs, files in os.walk(RUBRICS):
        for f in files:
            if f.endswith(".md"):
                out.append(os.path.join(dirpath, f))
    return sorted(out)


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


class TestReflectionProtocol(unittest.TestCase):
    def test_reflection_reference_exists(self):
        self.assertTrue(os.path.exists(REFLECT), "missing %s" % REFLECT)

    def test_every_contract_point_present(self):
        missing = sorted(REFLECT_IDS - set(_table_rows(REFLECT)),
                         key=lambda t: int(t[1:]))
        self.assertEqual(missing, [], "reflection-contract points missing: %s" % missing)

    def test_no_empty_contract_cells(self):
        rows = _table_rows(REFLECT)
        for rid in sorted(REFLECT_IDS):
            cell = rows.get(rid, "")
            self.assertTrue(cell and set(cell) - {"-", ":", " "},
                            "reflection-contract row %s has an empty cell" % rid)

    def test_orchestration_pack_points_at_it(self):
        with open(REF, encoding="utf-8") as f:
            text = f.read()
        self.assertIn("reflection-protocol.md", text,
                      "orchestration-pack.md reflection clause must point at reflection-protocol.md")


class TestTopologyContract(unittest.TestCase):
    """The restored team-design layer: a topology contract with its own
    traceability table, a delegation-tier layer, model/effort agent slots, and a
    delegation-defaults block in every rubric. Guards against the F0 regression
    (the model-agnostic refactor deleting the team-design content) recurring."""

    def test_every_topology_point_present(self):
        missing = sorted(TOPOLOGY_IDS - set(_table_rows()),
                         key=lambda t: int(t[1:]))
        self.assertEqual(missing, [], "topology-contract points missing from "
                         "orchestration-pack.md: %s" % missing)

    def test_no_empty_topology_cells(self):
        rows = _table_rows()
        for xid in sorted(TOPOLOGY_IDS):
            cell = rows.get(xid, "")
            self.assertTrue(cell and set(cell) - {"-", ":", " "},
                            "topology-contract row %s has an empty clause cell" % xid)

    def test_topology_row_count(self):
        present = set(_table_rows()) & TOPOLOGY_IDS
        self.assertEqual(len(present), len(TOPOLOGY_IDS),
                         "expected %d topology rows, found %d"
                         % (len(TOPOLOGY_IDS), len(present)))

    def test_delegation_tiers_reference_exists(self):
        self.assertTrue(os.path.exists(DELEGATION_TIERS), "missing %s" % DELEGATION_TIERS)
        with open(DELEGATION_TIERS, encoding="utf-8") as f:
            text = f.read().lower()
        for provider in ("anthropic", "openai", "xai"):
            self.assertIn(provider, text,
                          "delegation-tiers.md must cover provider '%s'" % provider)
        # the three tier roles the 90.2% tiered-team result rests on
        for role in ("orchestrat", "build", "explore"):
            self.assertIn(role, text,
                          "delegation-tiers.md must name the '%s' tier role" % role)

    def test_agent_template_has_model_and_effort_slots(self):
        with open(AGENT_TEMPLATE, encoding="utf-8") as f:
            text = f.read()
        self.assertRegex(text, r"(?m)^model:",
                         "agent-md-template.md frontmatter must expose a model: slot")
        self.assertRegex(text, r"(?m)^effort:",
                         "agent-md-template.md frontmatter must expose an effort: slot")

    def test_every_rubric_has_delegation_defaults(self):
        for path in _rubric_files():
            with open(path, encoding="utf-8") as f:
                text = f.read().lower()
            self.assertIn("delegation defaults", text,
                          "rubric %s missing a Delegation defaults block"
                          % os.path.relpath(path, ROOT))

    def test_protocol_false_promise_removed(self):
        with open(PROTOCOL, encoding="utf-8") as f:
            text = f.read()
        self.assertNotIn("which model orchestrates, what builders/auditors run on", text,
                         "tune-goal-protocol.md still carries the deleted-layer false promise")
        self.assertIn("delegation-tiers.md", text,
                      "tune-goal-protocol.md Step 1 must load the delegation-tier layer")


class TestScaleTiers(unittest.TestCase):
    """The scale-tier layer: Program = the field-validated contract unchanged;
    Solo/Pair and Squad strip apparatus. Both the pack contract and the Step-0
    intake must name the three tiers so a pair build is never handed program
    apparatus marked READY."""

    def test_pack_defines_three_tiers(self):
        with open(REF, encoding="utf-8") as f:
            text = f.read()
        self.assertIn("Scale tiers", text, "orchestration-pack.md must define a Scale tiers section")
        for tier in ("Solo/Pair", "Squad", "Program"):
            self.assertIn(tier, text, "Scale tiers section must name the %s tier" % tier)

    def test_intake_collects_team_design_facts(self):
        with open(PROTOCOL, encoding="utf-8") as f:
            text = f.read()
        for tier in ("Solo/Pair", "Squad", "Program"):
            self.assertIn(tier, text, "Step 0 intake must let the operator pick the %s tier" % tier)
        self.assertIn("Runtime model set", text,
                      "Step 0 intake must ask which model(s) the team runs on")


def _load_record_check():
    """Load a fresh copy of the record_check pack template as a module."""
    path = os.path.join(TEMPLATES, "record_check.py")
    spec = importlib.util.spec_from_file_location("record_check_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _rc_git(root, *args):
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    return subprocess.run(["git", "-C", root, *args], capture_output=True,
                          text=True, env=env)


def _mk_tagged_repo(root, tags):
    """A minimal git repo with one empty commit and the given milestone tags."""
    _rc_git(root, "init", "-q")
    _rc_git(root, "commit", "-q", "--allow-empty", "-m", "root")
    for t in tags:
        _rc_git(root, "tag", t)


class TestRecordCheckTierProportionality(unittest.TestCase):
    """G1-C2 (audit-per-tag) is proportional to the scale tier: program requires
    an audit report per tag (the current contract, unchanged); squad requires one
    only for user-facing milestones; solo-pair is satisfied by the gate battery
    and requires none. Guards against a two-person build being gate-blocked on a
    scaffold audit it never needed."""

    def _c2_fails(self, tier, tags, user_facing=None):
        with tempfile.TemporaryDirectory() as td:
            _mk_tagged_repo(td, tags)
            rc = _load_record_check()
            rc.CONFIG["tier"] = tier
            if user_facing is not None:
                rc.CONFIG["user_facing_milestones"] = user_facing
            fails, _warns = rc.run_checks(td)
            return [f for f in fails if f.startswith("C2")]

    def test_program_tier_requires_audit_per_tag(self):
        c2 = self._c2_fails("program", ["milestone/M0"])
        self.assertTrue(any("M0" in f for f in c2),
                        "program tier must require an audit report for every tag")

    def test_default_tier_is_program(self):
        # No tier key set at all — backward-compatible default is program.
        with tempfile.TemporaryDirectory() as td:
            _mk_tagged_repo(td, ["milestone/M0"])
            rc = _load_record_check()
            rc.CONFIG.pop("tier", None)
            fails, _ = rc.run_checks(td)
            self.assertTrue(any(f.startswith("C2") and "M0" in f for f in fails),
                            "absent tier must behave as program (current contract unchanged)")

    def test_solo_pair_tier_requires_no_audit(self):
        c2 = self._c2_fails("solo-pair", ["milestone/M0", "milestone/M1"])
        self.assertEqual(c2, [],
                         "solo-pair tier must not gate a tag on a missing audit report")

    def test_squad_tier_only_gates_user_facing(self):
        c2 = self._c2_fails("squad", ["milestone/M0", "milestone/M1"],
                            user_facing=["M1"])
        self.assertTrue(any("M1" in f for f in c2),
                        "squad tier must require an audit for a user-facing milestone")
        self.assertFalse(any("M0" in f for f in c2),
                         "squad tier must not require an audit for a non-user-facing milestone")


if __name__ == "__main__":
    unittest.main()
