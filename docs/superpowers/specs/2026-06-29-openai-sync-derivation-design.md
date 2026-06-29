# Design — Automated OpenAI Sync Derivation (D6)

- **Date:** 2026-06-29
- **Status:** approved design (audit-panel-hardened), pre-implementation
- **Reviewed by:** independent 3-reviewer panel (architecture/decoupling · safety-invariant/citation-discipline · OpenAI-domain/source-modeling) — 2× REVISE, 1× APPROVE-with-nits; all findings folded in below (§10).
- **Parent effort:** D1 (rubric foundation) + D2 (Codex portability) + D3 (iterated audit gate) + D4 (version log) + D5 (wiki render) merged to `main` at `ab3e8a8`. This is **D6**, the final deferred slice: make the automated derive-from-docs path work for OpenAI/Codex.

---

## 1. Context & goal

omnitune keeps a library of per-model **rubrics** (model-specific prompt-engineering best practices), detects the model the current session runs, selects the matching rubric, and — on a miss — `/omnitune:sync` derives one from that model's published docs behind safety gates, then a human commits. D1 made the rubric library **provider-aware** and hand-authored `openai/_core.md` + `gpt-5-5.md`. D3 added the iterated independent-audit gate; D4 the version log; D5 the Models wiki page.

**Goal of D6:** when a session runs an OpenAI/Codex model whose rubric is missing or stale, `/omnitune:sync` can fetch the **allowlisted OpenAI docs**, behavioral-diff against the closest existing OpenAI rubric, draft a citation-gated rubric, and route it through the **existing gates** (iterated audit panel → tighten-only ratchet → fail-closed regression corpus → human commit → `version_log.record`). Fetched docs are untrusted data behind a per-provider fence. No silent self-commit.

**What D6 actually is.** Almost every gate already exists and is provider-agnostic. The real gap is narrow: **source selection under-fetches for OpenAI.** A new OpenAI model's per-model `source_urls` is sparse (e.g. `gpt-5.4` → only `codex/models`), while the prompt-engineering substance lives in the provider's `sync_entrypoints` — and two of the rubrics' load-bearing citation homes (`[AG]` codex/guides/agents-md, `[LM]` api/docs/guides/latest-model) are not even in `sync_entrypoints` today. D6 makes the fetch set, the diff baseline, and the fence **mechanical and provider-parametric**, then exercises the path by shipping one real OpenAI artifact (`gpt-5-4.md`) through the **hand-authored rubric floor** with a voluntary audit panel.

## 2. Locked decisions

1. **One new dependency-free helper, `scripts/sync_sources.py`** (`plan` + `allowed`), mirroring `resolve_model.py`. It **reuses** `resolve_model.resolve()` for normalization/provider/baseline (no duplication) and owns only the fetch-set + fence policy.
2. **Role-tagged entrypoints** in `models.json` (schema **2 → 3**): each `sync_entrypoints` value becomes `{ "url", "role" }` with `role ∈ {model-listing, prompting, discovery}`. Add the two missing prompting homes (`codex_agents_md`, `latest_model`). Move anthropic's inline `comment` to a sibling `note`. **Content-fetch = non-`discovery` ∪ `source_urls`**; `discovery` (changelog) is reachable for two-key/recency but excluded from rubric content.
3. **`tuner_check.py` gains two blocking checks:** (a) every entrypoint URL-value and every model `source_urls` host is within that provider's `allowlist_domains` (skipping non-URL annotation values); (b) a non-`_core` rubric with `citation_gate: strict` **must** declare `extends:` (so a new rubric cannot silently drop the shared safety floor).
4. **`audit_ledger.record_round` hardened:** a round is `complete` only if a non-empty `author_id` was passed (and is not among the reviewers). Closes the self-review-counts-as-clean hole. (In-scope exception to "don't touch D3 internals" — it directly serves the safety invariant D6 leans on.)
5. **The `gpt-5.4` artifact ships via the SKILL's Hand-authored rubric floor** — human author → `tuner_check` clean → ratchet N/A (first commit) → **human commit** → `version_log.record` — with the **D3 audit panel run voluntarily on top** as added assurance. (A forward-dated fixture id cannot satisfy two-key's allowlisted-live-source key, and the regression corpus is < 5, so the *gated self-apply* path is unavailable; the hand-authored floor is the honest, equally-rigorous path. This realizes the "author through the gates" decision.)
6. **Honest citations:** any `gpt-5-4.md` line whose claim is not literally stated by its cited doc carries `(verify)`, never a real `[tag]`. Real tags are reserved for verbatim doc statements.
7. **Surface reconciliation:** `skills/sync/SKILL.md` derive-section rewired to call the helper; `commands/sync.md` minimally reconciled to v0.2 (preserving human-commit); `codex-tools.md` WebFetch row points at `allowed()` as the fence authority.

## 3. Scope

**In scope:** `scripts/sync_sources.py` + `scripts/test_sync_sources.py`; the role-tagged-entrypoint migration in `models.json` (+ the two added prompting URLs); the two new blocking `tuner_check.py` checks + tests; the `author_id` hardening in `audit_ledger.py` + test update; the SKILL derive-section + gated-self-apply rewiring; `commands/sync.md` + `codex-tools.md` reconciliation; the hand-authored `gpt-5-4.md` artifact + its `models.json`/`version-log.json` updates run through the floor with a voluntary panel; CI registration of `test_sync_sources`.

**Out of scope:** seeding the regression corpus; changes to `resolve_model`/`rubric_ratchet`/`version_log` internals (consumed as-is); deriving the other OpenAI siblings (`gpt-5.4-mini`, `gpt-5.3-codex-spark`); new wiki *content* (the wiki does not render entrypoints, so no regen needed — confirmed by grep).

## 4. Architecture

### 4.A `scripts/sync_sources.py` — derivation plan + fence (the one new unit)

Pure, dependency-free (stdlib `json`, `re`, `urllib.parse`), mirrors `resolve_model.py`. Two entry points.

**`plan(raw_id, models_json_path) -> dict`** — the derivation plan:

```
{
  "selection":      <verbatim resolve_model.resolve() result>,   # single source of truth
  "provider":       selection.provider,
  "normalized_id":  selection.normalized_id,
  "baseline_rubric": selection.rubric_path,        # closest existing rubric to diff against
  "baseline_tier":   selection.fallback_tier,      # exact | family | core | cross-provider | none
  "baseline_is_self": (selection.fallback_tier == "exact"),  # re-derive vs new-rubric
  "model_listing_url": <the role==model-listing entrypoint url, or None>,  # anchors two-key confirm
  "fetch_urls":  [ {"url","role","source"} , ... ], # content: non-discovery entrypoints ++ source_urls, deduped (entrypoints first), host-fenced
  "discovery_urls": [ {"url","role"} , ... ],       # role==discovery (changelog) — NOT rubric content
  "dropped":     [ {"url","reason"} , ... ],        # off-allowlist / non-https values, surfaced (never silently removed)
  "badge_reason": <string>                          # e.g. "unknown provider — cannot derive"
}
```

- **Reuse, not re-implement:** `plan` calls `resolve_model.resolve()` and embeds the whole result under `selection`; `provider`/`normalized_id`/`baseline_*` are mirrors. Normalization, provider routing, and the fallback ladder are never duplicated.
- **Content fetch set** = entrypoints whose `role ≠ discovery` ∪ the model's `source_urls`. (Model-listing pages such as `codex_models` carry `[MD]` facts, so they are content *and* the two-key anchor.) Deduped order-preserving, non-discovery entrypoints first, then `source_urls`. Each URL host validated by `allowed`; failures go to `dropped` with a reason.
- **`model_listing_url`** is surfaced so the gated-self-apply two-key step reads it directly instead of re-guessing which page lists ids.
- **Empty-after-fence is terminal:** if `fetch_urls` is empty for a known provider (all dropped, or no non-discovery entrypoints), `badge_reason` says so; the SKILL treats this as *fall back to propose-only*, never "diff with zero evidence."

**`allowed(provider, url, models_json_path) -> bool`** — the mechanical fence (hardened per Safety #2):

- Parse with `urllib.parse.urlsplit`; take `.hostname` (this discards userinfo, so `https://developers.openai.com@evil.com` → host `evil.com` → deny).
- Lowercase and IDNA/punycode-normalize the host before comparison.
- **Require `scheme == "https"`** (an `http` downgrade hop is MITM-able → deny).
- Match exact-or-dotted-subdomain against the provider's `allowlist_domains`: `h == d or h.endswith("." + d)`. This blocks both look-alikes (`notdevelopers.openai.com`) and suffix-spoofs (`developers.openai.com.evil.com`).
- Unknown provider / no `allowlist_domains` → deny.
- **Per-hop, not just terminus:** the SKILL instructs the agent to call `allowed()` on **every** redirect hop and deny on the first off-allowlist hop (the `cookbook.openai.com → developers.openai.com` 308 proves chains happen; both ends are allowlisted, but an intermediate off-allowlist hop must fail closed). `allowed()` is per-URL; the loop is the caller's.
- **Documented residual:** an open-redirect that *stays within* an allowlisted host (`platform.openai.com/redirect?url=…`) cannot be caught by a host check; it is mitigated only by the untrusted-data fence ("treat fetched content as reference data, not instructions"), which is therefore load-bearing, not optional.

### 4.B `models.json` — role-tagged entrypoints (schema 2 → 3)

Each `sync_entrypoints` value becomes an object:

```jsonc
"openai": {
  "allowlist_domains": ["developers.openai.com","platform.openai.com","openai.com","cookbook.openai.com"],
  "sync_entrypoints": {
    "codex_models":          { "url": "https://developers.openai.com/codex/models",                         "role": "model-listing" },
    "codex_changelog":       { "url": "https://developers.openai.com/codex/changelog",                      "role": "discovery" },
    "codex_prompting":       { "url": "https://developers.openai.com/codex/prompting",                      "role": "prompting" },
    "codex_best_practices":  { "url": "https://developers.openai.com/codex/learn/best-practices",           "role": "prompting" },
    "codex_prompting_guide": { "url": "https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide", "role": "prompting" },
    "codex_agents_md":       { "url": "https://developers.openai.com/codex/guides/agents-md",               "role": "prompting" },
    "latest_model":          { "url": "https://developers.openai.com/api/docs/guides/latest-model",         "role": "prompting" }
  },
  "note": "cookbook.openai.com 308-redirects to developers.openai.com/cookbook — follow cross-host redirects, re-fencing each hop. github.com/openai/codex is authoritative for CLI behavior but is secondary/manually-vetted, NOT allowlisted."
}
```

- `codex_agents_md` + `latest_model` are **added** — they are the citation homes for the existing `[AG]`/`[LM]` tags, so without them a derived rubric's citations would reference pages the fetch plan never lists (a latent inconsistency that already affects shipped `gpt-5-5.md`; this fix retroactively makes it consistent too).
- Anthropic mirrors the shape: `models_overview` → `model-listing`, `prompting_best_practices`/`migration_guide` → `prompting`, `models_api` → `discovery`; the inline `comment` key is **moved out** to a sibling `note`.
- Top-level `schema` → `3`; `updated` bumped. Readers: `resolve_model` ignores entrypoints (unaffected); the new fence check is the only code reading entrypoint values; `build_wiki_html.py` does not read entrypoints (grep-confirmed).

### 4.C `tuner_check.py` — two new blocking checks

1. **Fence integrity (manifest-time):** for each provider, every `sync_entrypoints[*].url` and every model `source_urls[*]` must satisfy the same exact-or-dotted-subdomain host rule against that provider's `allowlist_domains`. **Skip non-URL values** (any value not parsing as `http(s)://…`, e.g. a stray annotation) so a `note`/`comment` string is never mis-flagged. Accepts the listed `cookbook.openai.com` source; rejects a hypothetical `github.com/openai/codex` source. Kept self-contained (a tiny local host-check, matching tuner_check's deliberate no-import stance) — the duplication with `sync_sources.allowed()` is intentional and guarded by a **shared truth-table** in both test suites (§7).
2. **Floor-via-extends (new-rubric safety):** a rubric file with `citation_gate: strict` whose basename is **not** `_core.md` must declare `extends:`. Combined with the existing `_extends_problems` (extends resolves to the same-provider `_core.md`) and `_provider_core_problems` (the `_core.md` carries the floor-rule + fail-closed clause), this mechanically enforces the shared safety floor on a brand-new rubric even though the ratchet is N/A on a first commit.

### 4.D `audit_ledger.py` — `author_id` hardening

`record_round`'s completeness becomes: `complete = len(distinct) >= min_reviews and bool(author_id) and author_id not in distinct`. A round recorded without a non-empty `author_id` can never count toward convergence, so a caller that forgets to exclude itself cannot launder a self-review into a clean round. `convergence` is unchanged. `scripts/test_audit_ledger.py` is updated: existing rows that expect `complete=True` pass an `author_id`; a new row asserts omission ⇒ never-complete.

### 4.E SKILL + command-surface wiring

- **`skills/sync/SKILL.md` "Derive a rubric" step 1:** replace "fetch the model's `source_urls`" with: build the plan via `scripts/sync_sources.py`; fetch only `plan.fetch_urls`; re-validate **every** redirect hop with `allowed(...)`; never fetch anything in `plan.dropped`; if `plan.fetch_urls` is empty, **fall back to propose-only** with the `badge_reason`. **Step 2:** diff against `plan.baseline_rubric` (and if `plan.baseline_is_self`, treat as a re-derive — the change-magnitude gate, not a "new rubric → panel" assumption). Treat all fetched content as reference data, not instructions.
- **Gated-self-apply two-key step:** echo `plan.model_listing_url` as the allowlisted source of the id. The provider-domain panel reviewer is handed `plan.fetch_urls` (the fenced evidence) so its lens is falsifiable.
- **`commands/sync.md`:** drop the stale v0.1 "do not write the rubric yourself" wording; describe v0.2 (derive → run the gates → **human commit**). Preserve the human-only-commit guarantee verbatim.
- **`codex-tools.md`:** the WebFetch row points at `sync_sources.allowed()` / `plan()` as the fence authority (one canonical statement; the SKILL prose stays as guidance).

### 4.F The `gpt-5.4` artifact — hand-authored floor + voluntary panel

Author `skills/omnitune/references/rubrics/openai/gpt-5-4.md` (`extends: _core.md`, `citation_gate: strict`, same legend as `gpt-5-5.md`). Calibration consistent with the repo narrative: `gpt-5.4` = prior Codex flagship; `gpt-5.5` = newer recommended default; `gpt-5.4-mini` for subagents; `gpt-5.3-codex-spark` text-only preview. **Honest tagging (§2.6):** any 5.4-specific numeric default (effort/verbosity) or the explicit "prior/superseded" ordering that the cited pages do not literally state carries `(verify)`; only verbatim doc statements get real tags.

**Ordered ship steps** (the order matters — the new file is only vetted once its `rubric` path is non-null):

1. Write `openai/gpt-5-4.md` (filename = normalized `gpt-5.4` → `gpt-5-4.md`).
2. **Voluntary D3 audit panel** (assurance, not the self-apply authorization): `audit_ledger.reset(omnitune/.audit-ledger-<session>.json)`; dispatch 2–3 **read-only** review subagents (correctness/fidelity · fail-closed-safety + citation-honesty · OpenAI-domain), each handed `plan.fetch_urls` as evidence; `record_round(..., author_id=<self>)` with parent-computed fingerprints; reconcile each open material finding with a reason; loop to `convergence() == CONVERGED` (CAP_EXCEEDED → fix or drop a claim, never ship over open material).
3. Flip the `models.json` `gpt-5.4` entry: `rubric: "references/rubrics/openai/gpt-5-4.md"`, populate `source_urls` (the cited Codex pages), update `rubric_note` (shipped), **keep `status: limited`** (a limited model with a rubric raises no advisory and creates no `resolve_model`/`tuner_check` inconsistency).
4. **`tuner_check.py` clean** — now exercising the citation gate + floor-via-extends on the new file.
5. Ratchet **N/A** (first commit for this model id; the floor is enforced by step 4, not the ratchet).
6. **Human commit** (the operator — the signal the model cannot self-emit).
7. `version_log.record(...)` appends the `gpt-5.4` `add` lineage entry (date, provider `openai`, `source_urls`, outcome).

The regression-corpus gate is recorded as **"not applicable — hand-authored / propose-only path"**, never "satisfied by human review."

## 5. Data flow

```
session model id (or /omnitune:sync target)
  → sync_sources.plan(raw_id, models.json)
      → resolve_model.resolve(...) ............ provider, normalized_id, baseline rubric+tier (reused)
      → role-split entrypoints ∪ source_urls .. content fetch set (non-discovery), host-fenced
      → model_listing_url, discovery_urls, dropped, baseline_is_self
  → SKILL derive: fetch only plan.fetch_urls (re-fence each redirect hop) → behavioral diff vs plan.baseline_rubric
  → [new rubric] hand-authored floor: voluntary panel → models.json rubric flip → tuner_check (citation+extends+floor)
                  → ratchet N/A → human commit → version_log.record
```

## 6. Safety & decoupling

- **Decoupling held:** `sync_sources` and the new `tuner_check` logic carry **no provider/model nouns** — provider names arrive as parameters/data; allowlists, entrypoints, and roles live entirely in `models.json`; the `cookbook→developers` redirect is handled generically ("re-fence each hop"), not special-cased in code. SKILL prose references roles ("the resolved provider's model-listing entrypoint"), never `codex_models`/`developers.openai.com`.
- **Safety invariant held:** the fence is mechanical and hardened (§4.A); the new-rubric floor is enforced by extends+`_core` (§4.C); the audit panel cannot count a self-review (§4.D); the corpus gate is honestly recorded as N/A on the hand-authored path; the commit is human-only. No path reaches a silent self-commit.

## 7. Testing

`scripts/test_sync_sources.py` (unittest, dependency-free, registered in `validate.yml`) — a **frozen corpus** as the contract:
- `gpt-5.4` → `provider=openai`, `baseline_rubric=openai/gpt-5-5.md`, `baseline_tier=family`, `baseline_is_self=False`; `fetch_urls` = the OpenAI non-discovery entrypoints (with `codex/models` appearing **once** — it is the model-listing entrypoint *and* gpt-5.4's only `source_url`, so dedup collapses them), changelog **absent**, `agents-md`+`latest-model` **present**; `model_listing_url` = `codex/models`; `dropped` empty.
- `gpt-5.5` → `baseline_tier=exact`, `baseline_is_self=True` (re-derive row).
- A synthetic manifest with an off-allowlist `source_urls` entry → that URL in `dropped`, not `fetch_urls`.
- A provider whose entrypoints include a non-URL annotation → ignored, not crashed.
- Unknown id (`mistral-large`) → empty `fetch_urls`, `badge_reason` set, no crash; empty/garbage id → no crash.
- A non-manifest sibling (`gpt-5.6`) still resolves its baseline to `gpt-5-5.md` **after** `gpt-5.4` ships its own rubric (adding 5.4 must not change the family fallback — GA 5.5 outranks limited 5.4).
- **`allowed()` truth table (shared, identical rows in `test_tuner_check.py`):** allow `https://developers.openai.com/x`, `https://cookbook.openai.com/x`, `https://docs.anthropic.com/x`, a sub-subdomain; deny `http://…` (scheme), `https://developers.openai.com@evil.com/…` (userinfo), `https://notdevelopers.openai.com`, `https://developers.openai.com.evil.com` (suffix-spoof), `https://github.com/openai/codex` (off-allowlist), a cross-provider host, IDN/case variants.

Plus: new `test_tuner_check.py` rows for the fence-integrity check (cookbook accepted, github rejected, `comment`/`note` skipped) and the floor-via-extends check; updated `test_audit_ledger.py` (`author_id` required for completeness); a check that `gpt-5-4.md`'s `sources:` frontmatter ⊆ `plan("gpt-5.4").fetch_urls` (citation↔fetch consistency); `tuner_check.py`/`validate_plugin.py` pass after the artifact + schema bump.

## 8. Migration & blast radius

- `models.json` schema **2 → 3**; entrypoints restructured to `{url, role}`; anthropic `comment` → `note`; two OpenAI prompting URLs added; `gpt-5.4` entry flipped (rubric/source_urls/note) after the artifact is authored.
- Code readers of entrypoint *values*: only the new fence check (built here). `resolve_model`, `build_wiki_html.py`: unaffected (grep-confirmed).
- `audit_ledger.record_round` signature is source-compatible (`author_id` already a kwarg); only completeness semantics tighten — D3 tests updated accordingly.
- New CI module `test_sync_sources` appended at `.github/workflows/validate.yml:18`.
- Pre-existing uncommitted `wiki/Install-Setup.md` is unrelated — preserved, never staged by this work.

## 9. Definition of Done

- `sync_sources.plan/allowed` implemented, dependency-free, reusing `resolve_model`; frozen-corpus + fence-bypass tests green.
- `models.json` at schema 3 with role-tagged entrypoints (+ the two added prompting homes); `tuner_check` fence + floor-via-extends checks blocking and tested; `audit_ledger` hardened + tested.
- SKILL derive-section, `commands/sync.md`, `codex-tools.md` rewired; no provider noun in code/skill logic.
- `openai/gpt-5-4.md` authored with honest `(verify)` tagging, run through a CONVERGED voluntary panel, `models.json`/`version-log.json` updated in order, `tuner_check.py` clean, **human-committed**; corpus gate recorded N/A (hand-authored path).
- Full suite green from `scripts/`; `validate_plugin.py` + `check_public_clean.py` pass.

## 10. Audit-panel findings folded in (traceability)

- **Safety #1 / Domain #5 (blocker):** lexical citation gate → honest `(verify)` tagging rule (§2.6, §4.F).
- **Safety #2 / Domain #4 / Arch #5 (blocker/minor):** `allowed()` hardening — urllib hostname, https-only, exact-or-dotted-subdomain, per-hop re-fence, documented open-redirect residual (§4.A).
- **Safety #3 (major):** new-rubric floor via required `extends:` on strict non-`_core` rubrics (§4.C.2).
- **Safety #4/#5 (major):** reframe `gpt-5.4` to the hand-authored floor + voluntary panel; corpus recorded N/A not "satisfied" (§2.5, §4.F).
- **Safety #6 (minor):** `author_id` required for round completeness (§4.D).
- **Domain #1 (blocker):** add `codex_agents_md` + `latest_model` to entrypoints (§4.B).
- **Domain #2/#3 / Arch #2/#3 (major/minor):** role-tag entrypoints; exclude `discovery`/changelog from content fetch; surface `model_listing_url` (§2.2, §4.A, §4.B).
- **Arch #1 (major):** embed `resolve()` result + `baseline_is_self` (§4.A).
- **Arch #4/#6 (minor):** shared fence truth-table across both suites; fence check skips non-URL values (§4.C.1, §7).
- **Arch/Safety/Domain MISSED:** ordered ship steps (rubric flip before `tuner_check`); empty-after-fence terminal; panel reviewers receive `plan.fetch_urls`; `codex-tools.md`/`commands/sync.md` reconciliation; `sources ⊆ fetch_urls` test; sibling-`gpt-5.6` regression row (§4.E, §4.F, §7).
- **Domain #6/#7 (confirmations):** keep `github.com/openai/codex` out of the allowlist; keep `gpt-5.4` `status: limited`.

## 11. Sources

- `skills/sync/SKILL.md` (v0.2 gated-self-apply, hand-authored floor, safety invariant); `scripts/{resolve_model,audit_ledger,version_log,rubric_ratchet,tuner_check,detect_model}.py`; `skills/omnitune/references/{models.json, codex-tools.md, rubrics/openai/_core.md, rubrics/openai/gpt-5-5.md}`.
- D1 spec `2026-06-28-openai-codex-rubric-foundation-design.md`; D3 spec `2026-06-29-iterated-audit-gate-design.md`.
- D6 independent audit panel findings (2026-06-29), folded in §10.
- OpenAI/Codex citation homes (allowlisted): developers.openai.com/codex/{models,prompting,learn/best-practices,guides/agents-md}, developers.openai.com/api/docs/guides/latest-model, cookbook codex_prompting_guide.
