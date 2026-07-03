#!/usr/bin/env python3
"""sync_propose — deterministic proposal scaffold for a rubric derivation run.

Closes the sync-automation gap where an agent hand-assembles proposal metadata
across five mental buckets (selection, fetch plan, frontmatter, version-log
entry, open questions). This script produces ONE machine-checkable proposal
artifact; the agent fills only the judgment fields (`rubric_draft_preview`,
`behavioral_diff_summary`) and asks the operator the generated questions.

The script never fetches, writes rubrics, or touches the manifest — it is
propose-only scaffolding. Dependency-free.

Run:  python3 scripts/sync_propose.py <model-id> <models.json> [--date YYYY-MM-DD]
Out:  a JSON proposal on stdout
"""
import datetime
import json
import sys

import resolve_model
import sync_sources


def _manifest_entry(normalized_id, models_json_path):
    try:
        with open(models_json_path) as f:
            mj = json.load(f)
        for m in mj.get("models", []):
            if m.get("id") == normalized_id:
                return m
    except Exception:  # noqa: BLE001 - a broken manifest yields an empty entry
        pass
    return None


def propose(raw_id, models_json_path, date=None):
    """Assemble the deterministic proposal scaffold for `raw_id`."""
    date = date or datetime.date.today().isoformat()
    sel = resolve_model.resolve(raw_id, models_json_path)
    plan = sync_sources.plan(raw_id, models_json_path)
    entry = _manifest_entry(plan["normalized_id"], models_json_path)

    action = "update" if sel.get("fallback_tier") == "exact" else "add"
    plan_urls = [u["url"] for u in plan.get("fetch_urls", [])]
    roles = {u.get("role") for u in plan.get("fetch_urls", [])}

    questions = []
    if entry is None:
        questions.append({
            "q": "Model id '%s' is not in the manifest — confirm it appears on the "
                 "provider's model-listing page before any apply (two-key confirmation)."
                 % plan["normalized_id"],
            "context": plan.get("model_listing_url") or "no model-listing entrypoint",
        })
    if not plan_urls:
        questions.append({
            "q": "The fetch plan is empty — derivation must fall back to propose-only. Proceed?",
            "context": plan.get("badge_reason") or "no fetchable entrypoints",
        })
    if "prompting" not in roles:
        questions.append({
            "q": "No prompting-role source is in the fetch plan — the rubric will be "
                 "derived-tier (provider core + tier knowledge, version claims marked "
                 "(verify)). Acceptable?",
            "context": "providers.%s.sync_entrypoints in models.json" % plan["provider"],
        })

    frontmatter = {
        "model": plan["normalized_id"],
        "provider": plan["provider"],
        "family": (entry or {}).get("family") or resolve_model._family_guess(plan["normalized_id"]),
        "status": (entry or {}).get("status") or "ga",
        "source_status": "synced-from-docs" if "prompting" in roles else "derived-tier",
        "lastSynced": date,
        "sources": plan_urls,
        "extends": "_core.md",
    }
    version_log_entry = {
        "date": date,
        "model_id": plan["normalized_id"],
        "provider": plan["provider"],
        "action": action,
        "last_synced": date,
        "source_urls": plan_urls,
        "outcome": "proposed; awaiting approval",
    }
    return {
        "model_id": raw_id,
        "normalized_id": plan["normalized_id"],
        "provider": plan["provider"],
        "action": action,
        "selection": sel,
        "fetch_plan": plan,
        "frontmatter_template": frontmatter,
        "version_log_template": version_log_entry,
        "open_questions": questions,
        "rubric_draft_preview": "",
        "behavioral_diff_summary": "",
    }


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    date = None
    if "--date" in args:
        i = args.index("--date")
        try:
            date = args[i + 1]
        except IndexError:
            args = None  # fall through to usage
        else:
            del args[i:i + 2]
    if not args or len(args) != 2:
        sys.stderr.write("usage: sync_propose.py <model-id> <models.json> [--date YYYY-MM-DD]\n")
        return 2
    print(json.dumps(propose(args[0], args[1], date=date), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
