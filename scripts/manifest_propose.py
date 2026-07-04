#!/usr/bin/env python3
"""manifest_propose — emit + validate models.json entries.

  entry <id> <models.json>   -> a ready-to-merge model row (never fabricates dates)
  validate <models.json>     -> semantic check of every entry; exit 1 on any problem

Complements hook_guard's structural integrity with schema/semantic validation.
Dependency-free (stdlib + resolve_model/sync_sources).
"""
import json
import sys
from urllib.parse import urlparse

import resolve_model
import sync_sources

VALID_STATUS = {"ga", "limited", "deprecated", "retired"}


def _load(models_json_path):
    with open(models_json_path) as f:
        return json.load(f)


def _existing(mj, normalized_id):
    for m in mj.get("models", []):
        if m.get("id") == normalized_id:
            return m
    return None


def _rubric_path(provider, model_id):
    """Canonical rubric path: the filename stem is the normalized id with dots
    slugified to dashes (e.g. gpt-5.5 -> gpt-5-5.md). Mirrors tuner_check's
    expect_name rule so entry() emits exactly what validate() accepts and both
    agree with the live manifest."""
    stem = resolve_model.normalize(model_id).replace(".", "-")
    return "references/rubrics/%s/%s.md" % (provider, stem)


def entry(raw_id, models_json_path):
    plan = sync_sources.plan(raw_id, models_json_path)
    mj = _load(models_json_path)
    nid = plan["normalized_id"]
    prov = plan["provider"]
    ex = _existing(mj, nid) or {}
    return {
        "id": nid,
        "provider": prov,
        "family": ex.get("family") or resolve_model._family_guess(nid),
        "status": ex.get("status") or "ga",
        "ga_date": ex.get("ga_date"),
        "deprecated_date": ex.get("deprecated_date"),
        "rubric": _rubric_path(prov, nid),
        "source_urls": [u["url"] for u in plan.get("fetch_urls", [])],
    }


def _hosts(mj, provider):
    return (mj.get("providers", {}).get(provider, {}) or {}).get("allowlist_domains", []) or []


def _iso_or_null(d):
    if d is None:
        return True
    if not isinstance(d, str) or len(d) != 10 or d[4] != "-" or d[7] != "-":
        return False
    return (d[:4] + d[5:7] + d[8:10]).isdigit()


def validate(models_json_path):
    mj = _load(models_json_path)
    problems = []
    for m in mj.get("models", []):
        mid = m.get("id", "<no-id>")
        prov = m.get("provider")
        if m.get("status") not in VALID_STATUS:
            problems.append("%s: status %r not in %s"
                            % (mid, m.get("status"), sorted(VALID_STATUS)))
        rub = m.get("rubric")
        if rub is not None:
            want = _rubric_path(prov, mid)
            if rub != want:
                problems.append("%s: rubric path %r != %r" % (mid, rub, want))
        hosts = _hosts(mj, prov)
        for u in m.get("source_urls", []) or []:
            host = urlparse(u).hostname or ""
            if not any(host == h or host.endswith("." + h) for h in hosts):
                problems.append("%s: source host %r not in allowlist %s"
                                % (mid, host, hosts))
        for key in ("ga_date", "deprecated_date"):
            if not _iso_or_null(m.get(key)):
                problems.append("%s: %s %r is not null or ISO YYYY-MM-DD"
                                % (mid, key, m.get(key)))
    return problems


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) == 3 and args[0] == "entry":
        print(json.dumps(entry(args[1], args[2]), indent=2, sort_keys=True))
        return 0
    if len(args) == 2 and args[0] == "validate":
        problems = validate(args[1])
        for p in problems:
            print(p)
        return 1 if problems else 0
    sys.stderr.write("usage: manifest_propose.py entry <id> <models.json>\n"
                     "       manifest_propose.py validate <models.json>\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
