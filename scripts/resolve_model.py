#!/usr/bin/env python3
"""resolve_model — the single source of truth for model-id -> rubric selection.

Pure, dependency-free. Given a raw session model id and the path to models.json,
return (provider, normalized id, rubric path, fallback tier, badge reason). Every
SKILL/command that selects a rubric MUST call this instead of re-describing
normalization. Tiers: exact | family | core | cross-provider | none.
"""
import json
import re

PROVIDER_PREFIXES = [
    (re.compile(r"^claude[-_]"), "anthropic"),
    (re.compile(r"^(gpt[-_]|chatgpt[-_]|o\d)"), "openai"),
]


def normalize(raw):
    """Lowercase + strip wrappers, without mangling dotted minors or role suffixes."""
    if not raw:
        return ""
    s = raw.strip().lower()
    if s.startswith("ft:"):                 # ft:<base>:<org>::<id> -> <base>
        s = s[3:].split(":", 1)[0]
    if "/" in s:                            # vendor/<id> -> <id>
        s = s.split("/")[-1]
    prev = None                             # drop [1m] etc.; loop also clears [[nested]]
    while prev != s:
        prev = s
        s = re.sub(r"\[.*?\]", "", s)
    s = re.sub(r"-\d{4}-\d{2}-\d{2}$", "", s)   # -YYYY-MM-DD
    s = re.sub(r"-\d{8}$", "", s)               # -YYYYMMDD
    return s.strip()


def infer_provider(normalized):
    """Provider from an id prefix. Used ONLY to route ids absent from the manifest."""
    for rx, prov in PROVIDER_PREFIXES:
        if rx.match(normalized):
            return prov
    return "unknown"


def _family_guess(normalized):
    """Coarse family token: everything before the first dot ('gpt-5.4' -> 'gpt-5')."""
    return normalized.split(".")[0]


def _version_key(m):
    """Sort key for family fallback: ga first, then highest numeric version
    (so gpt-5.10 outranks gpt-5.9, which alphabetical order gets wrong), id as tiebreak."""
    parts = re.split(r"[.\-]", m.get("id", ""))
    nums = [int(p) for p in parts if p.isdigit()]
    return (m.get("status") != "ga", [-n for n in nums], m.get("id", ""))


def _newest_ga_rubric(models):
    # Cross-provider terminal default = the first GA model with a rubric in manifest
    # order; keep the intended default (Anthropic) listed first among GA entries.
    for m in models:
        if m.get("status") == "ga" and m.get("rubric"):
            return m
    return None


def _result(provider, norm, rubric, tier, why):
    return {"provider": provider, "normalized_id": norm,
            "rubric_path": rubric, "fallback_tier": tier, "badge_reason": why}


def _fallback(provider, norm, family, models):
    same = [m for m in models if m.get("provider") == provider and m.get("rubric")]
    fam = [m for m in same if m.get("family") == family]
    fam.sort(key=_version_key)
    if fam:
        win = fam[0]
        why = "no tuned rubric for '%s' yet; running on '%s' (same family)" % (norm, win["id"])
        return _result(provider, norm, win["rubric"], "family", why)
    core = "references/rubrics/%s/_core.md" % provider
    why = "no model rubric for '%s'; running on the %s core only" % (norm, provider)
    return _result(provider, norm, core, "core", why)


def _cross_provider(norm, models):
    win = _newest_ga_rubric(models)
    if win:
        why = ("model '%s' not recognized; running on '%s' (cross-provider) — verify the result"
               % (norm, win["id"]))
        return _result("unknown", norm, win["rubric"], "cross-provider", why)
    return _result("unknown", norm, None, "none", "no rubric available for '%s'" % norm)


def resolve(raw_id, models_json_path):
    """Resolve a raw session model id to a rubric selection. Never raises."""
    norm = normalize(raw_id)
    try:
        with open(models_json_path) as f:
            mj = json.load(f)
    except Exception as e:  # noqa: BLE001 - a bad/missing manifest must not crash a run
        return _result("unknown", norm, None, "none",
                       "could not load models.json (%s): %s" % (models_json_path, e))
    models = mj.get("models", [])

    by_id = {normalize(m.get("id", "")): m for m in models}
    entry = by_id.get(norm)

    if entry:
        provider = entry.get("provider") or infer_provider(norm)
        if entry.get("rubric"):
            return _result(provider, norm, entry["rubric"], "exact", "")
        family = entry.get("family") or _family_guess(norm)
        return _fallback(provider, norm, family, models)

    provider = infer_provider(norm)
    if provider == "unknown":
        return _cross_provider(norm, models)
    return _fallback(provider, norm, _family_guess(norm), models)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        sys.stderr.write("usage: resolve_model.py RAW_ID PATH_TO_models.json\n")
        sys.exit(2)
    print(json.dumps(resolve(sys.argv[1], sys.argv[2]), indent=2))
