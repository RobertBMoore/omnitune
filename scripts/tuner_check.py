#!/usr/bin/env python3
"""tuner-check — CI-friendly lint for a omnitune host repo.

Validates that omnitune.config.yaml is internally consistent and that the plugin's
model manifest is intact, so silent config rot (a renamed skill, a moved voice
file, a GA model with no rubric) fails a build instead of degrading Mode A/B at
runtime. Dependency-free (uses the bundled miniyaml).

Usage:
  python3 tuner_check.py [REPO_ROOT] [--models PATH_TO_models.json]
Exit code 0 = clean, 1 = problems found (printed to stderr).
"""
import os
import sys
import json
import re

import miniyaml

VALID_CHANNELS = {"badge", "interrupt", "manual"}
REQUIRED = ["project.name", "project.domain", "skills.root",
            "output.reports", "output.prompts", "model_sync.channel"]


def _get(cfg, dotted):
    cur = cfg
    for k in dotted.split("."):
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur


ALLOWED_PROVIDERS = {"anthropic", "openai"}


def _normalize_id(raw):
    # Mirror resolve_model.normalize for the filename<->id check (kept local so
    # tuner_check stays dependency-free even if run standalone).
    s = (raw or "").strip().lower()
    if s.startswith("ft:"):
        s = s[3:].split(":", 1)[0]
    if "/" in s:
        s = s.split("/")[-1]
    s = re.sub(r"\[.*?\]", "", s)
    s = re.sub(r"-\d{4}-\d{2}-\d{2}$", "", s)
    s = re.sub(r"-\d{8}$", "", s)
    return s.strip()


def _citation_problems(rubric_full, model_id):
    """For a rubric whose frontmatter sets `citation_gate: strict`, every bullet
    rule line must carry a citation token: a [tag], a URL, 'Core §', or '(verify)'."""
    out = []
    try:
        with open(rubric_full, encoding="utf-8") as f:
            text = f.read()
    except Exception:  # noqa: BLE001
        return out
    fm = ""                                  # only honor the gate from the YAML frontmatter
    if text.startswith("---"):
        end = text.find("\n---", 3)
        fm = text if end == -1 else text[:end]
    if "citation_gate: strict" not in fm:
        return out
    cited = re.compile(r"\[[^\]]+\]|https?://|Core §|\(verify\)")
    for ln in text.split("\n"):
        st = ln.strip()
        if st.startswith("- ") and len(st) > 8 and not cited.search(st):
            out.append("citation: model '%s' rubric has an uncited rule: %s" % (model_id, st[:60]))
    return out


def _extends_problems(skill_dir, rb, provider, mid):
    """A rubric's frontmatter `extends:` must resolve to its same-provider _core.md."""
    out = []
    full = os.path.join(skill_dir, rb)
    try:
        with open(full, encoding="utf-8") as f:
            text = f.read()
    except Exception:  # noqa: BLE001
        return out
    m = re.search(r"^extends:\s*(\S+)", text, re.M)
    if not m:
        return out  # extends is optional (a _core file itself has none)
    target = m.group(1).strip()
    target_full = os.path.normpath(os.path.join(os.path.dirname(full), target))
    rel = target_full.replace(os.sep, "/")
    if not os.path.exists(target_full):
        out.append("manifest: model '%s' extends '%s' which does not exist" % (mid, target))
    elif os.path.basename(target_full) != "_core.md" or ("rubrics/%s/_core.md" % provider) not in rel:
        out.append("manifest: model '%s' extends '%s' (not the %s provider _core.md)"
                   % (mid, target, provider))
    return out


def _provider_core_problems(skill_dir, provider):
    """A provider with shipped rubrics must have a _core.md carrying the shared safety floor."""
    out = []
    core_rel = "references/rubrics/%s/_core.md" % provider
    full = os.path.join(skill_dir, core_rel)
    if not os.path.exists(full):
        out.append("manifest: provider '%s' has no %s" % (provider, core_rel))
        return out
    try:
        with open(full, encoding="utf-8") as f:
            text = f.read().lower()
    except Exception:  # noqa: BLE001
        return out
    if "floor rule" not in text and "floor-rule" not in text:
        out.append("manifest: provider '%s' _core.md missing the audit floor-rule" % provider)
    if "fail-closed" not in text and "fail closed" not in text:
        out.append("manifest: provider '%s' _core.md missing the fail-closed clause" % provider)
    return out


def manifest_problems(models_json_path):
    """Provider validation matrix for models.json. Returns problem strings."""
    problems = []
    if not (models_json_path and os.path.exists(models_json_path)):
        return problems
    try:
        with open(models_json_path) as f:
            mj = json.load(f)
    except Exception as e:  # noqa: BLE001
        return ["manifest: failed to read models.json: %s" % e]
    skill_dir = os.path.dirname(os.path.dirname(models_json_path))
    providers = mj.get("providers", {})
    cores_to_check = set()
    for m in mj.get("models", []):
        mid = m.get("id")
        prov = m.get("provider")
        if not prov:
            problems.append("manifest: model '%s' has no provider" % mid)
            continue
        if prov not in ALLOWED_PROVIDERS:
            problems.append("manifest: model '%s' provider '%s' not in %s"
                            % (mid, prov, sorted(ALLOWED_PROVIDERS)))
        if not (providers.get(prov, {}).get("allowlist_domains")):
            problems.append("manifest: provider '%s' has no providers[].allowlist_domains" % prov)
        rb = m.get("rubric")
        if rb:
            expect_dir = "references/rubrics/%s/" % prov
            if not rb.startswith(expect_dir):
                problems.append("manifest: model '%s' rubric not under provider dir %s: %s"
                                % (mid, expect_dir, rb))
            else:
                expect_name = _normalize_id(mid).replace(".", "-") + ".md"
                if os.path.basename(rb) != expect_name:
                    problems.append("manifest: model '%s' rubric filename should be %s, got %s"
                                    % (mid, expect_name, os.path.basename(rb)))
                full = os.path.join(skill_dir, rb)
                problems.extend(_citation_problems(full, mid))
                problems.extend(_extends_problems(skill_dir, rb, prov, mid))
                cores_to_check.add(prov)
    for prov in sorted(cores_to_check):
        problems.extend(_provider_core_problems(skill_dir, prov))
    return problems


def check(repo_root, config_text, models_json_path):
    """Return a list of human-readable problem strings (empty == clean)."""
    problems = []
    try:
        cfg = miniyaml.load(config_text)
    except Exception as e:  # noqa: BLE001 - lint must never crash a build opaquely
        return ["config: failed to parse omnitune.config.yaml: %s" % e]

    for req in REQUIRED:
        if not _get(cfg, req):
            problems.append("config: missing required field '%s'" % req)

    skills_root = _get(cfg, "skills.root") or ""

    for r in (cfg.get("routing") or []):
        name = r.get("skill") if isinstance(r, dict) else None
        if name and not os.path.exists(os.path.join(repo_root, skills_root, name, "SKILL.md")):
            problems.append("routing: skill '%s' has no %s%s/SKILL.md" % (name, skills_root, name))

    for cp in (cfg.get("context_pointers") or []):
        for p in (cp.get("point_to") or []) if isinstance(cp, dict) else []:
            if p and not os.path.exists(os.path.join(repo_root, p)):
                problems.append("context_pointers: path '%s' does not exist" % p)

    for key in ("house_rules", "reserved_decisions"):
        v = cfg.get(key)
        if v and not os.path.exists(os.path.join(repo_root, v)):
            problems.append("%s: path '%s' does not exist" % (key, v))

    ch = _get(cfg, "model_sync.channel")
    if ch and ch not in VALID_CHANNELS:
        problems.append("model_sync.channel: '%s' not in %s" % (ch, sorted(VALID_CHANNELS)))

    if models_json_path and os.path.exists(models_json_path):
        try:
            with open(models_json_path) as f:
                mj = json.load(f)
            skill_dir = os.path.dirname(os.path.dirname(models_json_path))
            for m in mj.get("models", []):
                # A GA model with rubric: null is the expected derive-on-demand
                # state (a just-shipped model) — a warning, not a failure (see
                # manifest_warnings). A NON-null rubric path that doesn't resolve
                # is a real integrity failure.
                rb = m.get("rubric")
                if rb and not os.path.exists(os.path.join(skill_dir, rb)):
                    problems.append("manifest: model '%s' rubric path missing: %s" % (m.get("id"), rb))
            problems.extend(manifest_problems(models_json_path))
        except Exception as e:  # noqa: BLE001
            problems.append("manifest: failed to read models.json: %s" % e)

    return problems


def manifest_warnings(models_json_path):
    """Soft advisories that do NOT fail a build — e.g. a GA model with no shipped
    rubric (the expected derive-on-demand state)."""
    warns = []
    if models_json_path and os.path.exists(models_json_path):
        try:
            with open(models_json_path) as f:
                mj = json.load(f)
            for m in mj.get("models", []):
                if m.get("status") == "ga" and not m.get("rubric"):
                    warns.append("GA model '%s' has no shipped rubric — run /omnitune:sync to derive one" % m.get("id"))
        except Exception:  # noqa: BLE001
            pass
    return warns


def _default_models_path():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "..", "skills", "omnitune", "references", "models.json")


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    repo_root = args[0] if args else os.getcwd()
    models = _default_models_path()
    if "--models" in argv:
        models = argv[argv.index("--models") + 1]
    cfg_path = os.path.join(repo_root, "omnitune.config.yaml")
    if not os.path.exists(cfg_path):
        sys.stderr.write("tuner-check: no omnitune.config.yaml at %s (run /omnitune:install)\n" % repo_root)
        return 1
    with open(cfg_path) as f:
        config_text = f.read()
    problems = check(repo_root, config_text, models)
    for w in manifest_warnings(models):
        sys.stderr.write("tuner-check: warning: %s\n" % w)
    if problems:
        sys.stderr.write("tuner-check: %d problem(s):\n" % len(problems))
        for p in problems:
            sys.stderr.write("  - %s\n" % p)
        return 1
    sys.stdout.write("tuner-check: OK (config + manifest consistent)\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
