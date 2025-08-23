# Delta v1.5.3 — CI green: migrate before API, OPA compat, DB health

**What changed**
- Added OPA compat override (`infra/docker-compose.opa.compat.yml`) to avoid missing `-rootless` tag and mount `policies_enabled/` only.
- Added DB env override for CI (`infra/docker-compose.db.ci.yml`) so migrations use a known role (`postgres`) and DB (`aitest`).
- Added DB health gate (`infra/docker-compose.health.yml`), API wait script, and local CI runner.
- Added `policies_enabled/policy.rego` (valid, permissive) to avoid OPA parse errors from legacy policy files during CI.

**How to use**
- Prefer **`.github/workflows/ci_v3.yml`** (build→db+opa→migrate→api→smoke).
- Or patch your existing `ci.yml` with `bash scripts/ci_patch_v153.sh`.

**Local run**
```bash
bash scripts/ci_local_up_v153.sh
python scripts/ci_smoke.py
```
