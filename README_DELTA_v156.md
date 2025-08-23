# v1.5.6 — CI Alembic Path Fix + psycopg2 in CI image + OPA/DB overrides

**What changed**
- Migrations now run from `/app/orchestrator` with `PYTHONPATH=/app` and `-c alembic.ini`.
- Orchestrator CI image extends base to include `psycopg2-binary==2.9.9`.
- OPA uses a valid tag and loads from `policies_enabled/` only for CI.
- DB creds are standardized (postgres/postgres, DB=aitest) and exported to the orchestrator.
- Robust scripts: `ci_migrate_v156.sh`, `ci_stack_up_v156.sh`, `wait_for_api_v156.sh`, `ci_local_up_v156.sh`.
- Optional new workflow: `.github/workflows/ci_v5.yml`.

**Kali OS agent**
- Added safe extra tools: `gobuster_dns_safe`, `ffuf_post_json`, `sqlmap_smart` (merge with `scripts/merge_kali_tools_v156.sh`).

**How to use**
```bash
# CI locally
bash scripts/ci_local_up_v156.sh

# CI on GitHub
git add .github/workflows/ci_v5.yml
git commit -m "ci: add ci_v5 (build→migrate→api→smoke)"
git push
```
