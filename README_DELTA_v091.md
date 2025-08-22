# Delta v0.9.1 — CI + Makefile + CI-friendly smoke (additive)

Adds:
- **GitHub Actions CI** workflow `.github/workflows/ci.yml` (docker-compose up, migrate, Python smoke against API).
- **Compose CI override** `infra/docker-compose.ci.yml` enabling `SIMULATE_PROGRESS=true` for predictable runs.
- **Makefile** with `up`, `down`, `migrate`, `logs`, `ui-up`, `smoke`, `agent-devext`, `clean`.
- **Python smoke** `scripts/ci_smoke.py` (no jq dependency).

## Local quickstart
```bash
make up
make migrate
python scripts/ci_smoke.py
```

## CI on GitHub
Push any branch and the workflow runs automatically. On failures, logs from `orchestrator`, `db`, and `opa` are printed.
