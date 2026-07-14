#!/usr/bin/env python3
"""tuner-check — CI-friendly lint for a omnitune host repo.

Validates that omnitune.config.yaml is internally consistent and that the plugin's
model manifest is intact, so silent config rot (a renamed skill, a moved voice
file, a GA model with no rubric) fails a build instead of degrading Modes A/B/C at
runtime. Dependency-free (uses the bundled miniyaml).

Usage:
  python3 tuner_check.py [REPO_ROOT] [--models PATH_TO_models.json]
Exit code 0 = clean, 1 = problems found (printed to stderr).
"""
import os
import sys
import json
import re
from urllib.parse import urlsplit

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


ALLOWED_PROVIDERS = {"anthropic", "openai", "xai"}


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


VALID_SOURCE_STATUS = {"synced-from-docs", "derived-tier"}


def _source_status_problems(rubric_full, mid):
    """A rubric's frontmatter `source_status`, if present, must name a known
    provenance: `synced-from-docs` (from live/version docs) or `derived-tier`
    (authored from tier/family knowledge, version-specific items marked (verify))."""
    out = []
    try:
        with open(rubric_full, encoding="utf-8") as f:
            text = f.read()
    except Exception:  # noqa: BLE001
        return out
    m = re.search(r"^source_status:\s*(\S+)", text, re.M)
    if m and m.group(1).strip() not in VALID_SOURCE_STATUS:
        out.append("manifest: model '%s' rubric source_status '%s' not in %s"
                   % (mid, m.group(1).strip(), sorted(VALID_SOURCE_STATUS)))
    return out


def _source_alignment_problems(rubric_full, mid, manifest_urls):
    """Every URL a rubric's frontmatter `sources:` cites must appear in the
    manifest entry's source_urls — otherwise the citation trail breaks at the
    manifest (the drift class two independent panel reviewers hit 2026-07-03)."""
    out = []
    try:
        with open(rubric_full, encoding="utf-8") as f:
            text = f.read()
    except Exception:  # noqa: BLE001
        return out
    if not text.startswith("---"):
        return out
    end = text.find("\n---", 3)
    fm = text if end == -1 else text[:end]
    m = re.search(r"^sources:\s*\n((?:\s+-\s+\S+\n?)+)", fm, re.M)
    if not m:
        return out
    cited = re.findall(r"-\s+(\S+)", m.group(1))
    known = set(manifest_urls or [])
    for url in cited:
        if url not in known:
            out.append("manifest: model '%s' rubric cites a source missing from its "
                       "manifest source_urls: %s" % (mid, url))
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
        # A citation_gate: strict rubric inherits the shared safety floor via its
        # provider _core.md; on a brand-new rubric the ratchet is N/A, so require
        # extends here or the floor could be silently dropped. A _core.md is the
        # floor itself and is exempt.
        is_core = os.path.basename(full) == "_core.md"
        strict = bool(re.search(r"^citation_gate:\s*strict", text, re.M))
        if strict and not is_core:
            out.append("manifest: model '%s' rubric is citation_gate: strict but must declare extends:" % mid)
        return out  # extends is otherwise optional (a _core file itself has none)
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


def _is_url(val):
    """True if val is an http(s) URL string (so annotation strings are skipped)."""
    try:
        return isinstance(val, str) and urlsplit(val).scheme in ("http", "https")
    except Exception:  # noqa: BLE001
        return False


def _host_in_allowlist(url, domains):
    """Local mirror of sync_sources.allowed's host rule (kept local so tuner_check
    imports nothing at runtime): https-only, host == domain or a dotted subdomain."""
    try:
        parts = urlsplit(url)
    except Exception:  # noqa: BLE001
        return False
    if parts.scheme != "https":
        return False
    host = (parts.hostname or "").strip().lower().rstrip(".")
    for d in domains or []:
        d = (d or "").strip().lower().rstrip(".")
        if d and (host == d or host.endswith("." + d)):
            return True
    return False


def _fence_problems(mj):
    """Every entrypoint URL + every model source_url must be within its provider's
    allowlist_domains. Non-URL annotation values are skipped (not flagged)."""
    out = []
    providers = mj.get("providers", {}) or {}
    for prov, block in providers.items():
        domains = (block or {}).get("allowlist_domains") or []
        for key, val in ((block or {}).get("sync_entrypoints") or {}).items():
            url = val.get("url") if isinstance(val, dict) else val
            if not _is_url(url):
                continue
            if not _host_in_allowlist(url, domains):
                out.append("manifest: provider '%s' entrypoint '%s' url off-allowlist: %s"
                           % (prov, key, url))
    for m in mj.get("models", []):
        domains = (providers.get(m.get("provider"), {}) or {}).get("allowlist_domains") or []
        for url in (m.get("source_urls") or []):
            if _is_url(url) and not _host_in_allowlist(url, domains):
                out.append("manifest: model '%s' source_url off-allowlist: %s" % (m.get("id"), url))
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
                problems.extend(_source_status_problems(full, mid))
                problems.extend(_source_alignment_problems(full, mid, m.get("source_urls")))
                cores_to_check.add(prov)
    for prov in sorted(cores_to_check):
        problems.extend(_provider_core_problems(skill_dir, prov))
    problems.extend(_fence_problems(mj))
    return problems


def _audit_config_problems(cfg):
    """Validate model_sync.audit_* keys (blocking). Returns problem strings."""
    out = []
    ms = cfg.get("model_sync") if isinstance(cfg, dict) else None
    if not isinstance(ms, dict):
        return out

    def _as_int(key):
        v = ms.get(key)
        if v in (None, ""):
            return None
        try:
            return int(str(v).strip())
        except Exception:  # noqa: BLE001
            out.append("model_sync.%s must be an integer" % key)
            return None

    cr = _as_int("audit_clean_rounds")
    cap = _as_int("audit_round_cap")
    th = _as_int("audit_panel_threshold")
    if cr is not None and cr < 1:
        out.append("model_sync.audit_clean_rounds must be >= 1")
    if cap is not None and cap < (cr if cr is not None else 2):
        out.append("model_sync.audit_round_cap must be >= audit_clean_rounds")
    if th is not None and th < 0:
        out.append("model_sync.audit_panel_threshold must be >= 0")
    sev = ms.get("audit_material_severity")
    if sev not in (None, ""):
        ranks = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        s = str(sev).strip().lower()
        if s not in ranks:
            out.append("model_sync.audit_material_severity must be low|medium|high|critical")
        elif ranks[s] > ranks["high"]:
            out.append("model_sync.audit_material_severity must not be stricter than "
                       "'high' (loosening the audit needs explicit human sign-off)")
    return out


def _version_log_problems(skill_dir):
    """Referential integrity for references/version-log.json (blocking)."""
    out = []
    log = os.path.join(skill_dir, "references", "version-log.json")
    if not os.path.exists(log):
        return out
    try:
        with open(log) as f:
            d = json.load(f)
    except Exception as e:  # noqa: BLE001
        return ["version-log: failed to read: %s" % e]
    if not isinstance(d.get("schema"), int):
        out.append("version-log: schema must be an integer")
    ids = set()
    try:
        with open(os.path.join(skill_dir, "references", "models.json")) as f:
            for m in json.load(f).get("models", []):
                if m.get("id"):
                    ids.add(m["id"])
    except Exception:  # noqa: BLE001
        pass
    for e in (d.get("entries") or []):
        if not isinstance(e, dict):
            out.append("version-log: an entry is not an object")
            continue
        for k in ("date", "model_id", "action"):
            if not e.get(k):
                out.append("version-log: entry missing '%s'" % k)
        act = e.get("action")
        if act and act not in {"add", "update", "deprecate"}:
            out.append("version-log: entry '%s' bad action '%s'" % (e.get("model_id"), act))
        mid = e.get("model_id")
        if mid and ids and mid not in ids:
            out.append("version-log: entry references unknown model '%s'" % mid)
    return out


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

    problems.extend(_audit_config_problems(cfg))

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
            problems.extend(_version_log_problems(skill_dir))
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
