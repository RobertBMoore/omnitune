#!/usr/bin/env python3
"""sync_sources — derivation source plan + fetch fence for /omnitune:sync.

Given a raw session/target model id and models.json, produce the deterministic
derivation plan: which allowlisted docs to fetch (provider entrypoints by role +
the model's source_urls), the closest existing rubric to diff against, and a
hardened per-provider fetch fence. Provider specifics (roles, allowlists,
entrypoints) live entirely in models.json — this module holds no provider or
model nouns. Reuses resolve_model for normalization/provider/baseline. Pure,
dependency-free; plan()/allowed() never raise. Mirrors resolve_model.py.
"""
import json
from urllib.parse import urlsplit

import resolve_model

DISCOVERY_ROLE = "discovery"


def _load(models_json_path):
    with open(models_json_path) as f:
        return json.load(f)


def _host(url):
    """Lowercased, IDNA-normalized hostname (userinfo + port discarded), https-only.
    Returns '' for a non-https URL or an unparseable host."""
    try:
        parts = urlsplit(url)
        if parts.scheme != "https":
            return ""
        host = (parts.hostname or "").strip().lower().rstrip(".")
        if not host:
            return ""
        try:
            host = host.encode("idna").decode("ascii")
        except Exception:  # noqa: BLE001 - a non-encodable host is simply not allowlisted
            pass
        return host
    except Exception:  # noqa: BLE001
        return ""


def _provider_block(provider, mj):
    return (mj.get("providers", {}) or {}).get(provider, {}) or {}


def _domains(provider, mj):
    return _provider_block(provider, mj).get("allowlist_domains") or []


def _host_allowed(host, domains):
    if not host:
        return False
    for d in domains:
        d = (d or "").strip().lower().rstrip(".")
        if d and (host == d or host.endswith("." + d)):
            return True
    return False


def allowed(provider, url, models_json_path):
    """True iff url is https and its host equals (or is a subdomain of) one of the
    provider's allowlist_domains. Never raises."""
    try:
        return _host_allowed(_host(url), _domains(provider, _load(models_json_path)))
    except Exception:  # noqa: BLE001
        return False


def _entrypoints(provider, mj):
    """Yield (key, url, role) for url-valued entrypoints only (skip annotations)."""
    block = _provider_block(provider, mj).get("sync_entrypoints") or {}
    for key, val in block.items():
        if isinstance(val, dict) and isinstance(val.get("url"), str):
            yield key, val["url"], (val.get("role") or "")


def plan(raw_id, models_json_path):
    """Build the derivation plan for raw_id. Never raises."""
    sel = resolve_model.resolve(raw_id, models_json_path)
    provider = sel.get("provider")
    out = {
        "selection": sel,
        "provider": provider,
        "normalized_id": sel.get("normalized_id"),
        "baseline_rubric": sel.get("rubric_path"),
        "baseline_tier": sel.get("fallback_tier"),
        "baseline_is_self": sel.get("fallback_tier") == "exact",
        "model_listing_url": None,
        "fetch_urls": [],
        "discovery_urls": [],
        "dropped": [],
        "badge_reason": "",
    }
    try:
        mj = _load(models_json_path)
    except Exception as e:  # noqa: BLE001
        out["badge_reason"] = "could not load models.json: %s" % e
        return out

    domains = _domains(provider, mj)
    norm = out["normalized_id"]
    src_urls = []
    for m in mj.get("models", []):
        if resolve_model.normalize(m.get("id", "")) == norm:
            src_urls = list(m.get("source_urls") or [])
            break

    seen = set()

    def _add_content(url, role, source):
        h = _host(url)
        if not _host_allowed(h, domains):
            out["dropped"].append(
                {"url": url, "reason": "off-allowlist or non-https for provider '%s'" % provider})
            return
        key = (h, urlsplit(url).path.rstrip("/"))
        if key in seen:
            return
        seen.add(key)
        out["fetch_urls"].append({"url": url, "role": role, "source": source})

    for key, url, role in _entrypoints(provider, mj):
        if role == "model-listing" and out["model_listing_url"] is None:
            out["model_listing_url"] = url
        if role == DISCOVERY_ROLE:
            out["discovery_urls"].append({"url": url, "role": role})
            continue
        _add_content(url, role or "prompting", "entrypoint:%s" % key)

    for url in src_urls:
        _add_content(url, "model", "source_urls")

    if not out["fetch_urls"]:
        if provider in (None, "unknown") or not domains:
            out["badge_reason"] = "cannot derive: no allowlisted docs for provider '%s'" % provider
        else:
            out["badge_reason"] = "cannot derive: all sources off-allowlist — fall back to propose-only"
    return out


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        sys.stderr.write("usage: sync_sources.py RAW_ID PATH_TO_models.json\n")
        sys.exit(2)
    print(json.dumps(plan(sys.argv[1], sys.argv[2]), indent=2))
