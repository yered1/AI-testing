# Delta v0.8.4 — Add routers (v2), Catalog, Dev Agent, Evidence (additive)

This drop adds:
- **v2 Routers**: quotas, approvals, findings, artifacts, reports, agents bus, brain (autoplan), listings — mounted automatically.
- **Catalog**: baseline tests + packs.
- **Dev Agent** that speaks the bus (`agents/dev_agent`) + compose extension.
- **Evidence** volume override (`infra/docker-compose.evidence.yml`).
- **.env** extras (`orchestrator/.env.append.example`).
- **Smoke** script `scripts/smoke_v084.sh`.

## Apply
```bash
git checkout -b overlay-v084
unzip -o ~/Downloads/ai-testing-overlay-v084.zip
git add -A
git commit -m "v0.8.4 overlay: v2 routers + catalog + dev agent + evidence"
```

## Run
```bash
docker compose -f infra/docker-compose.v2.yml up --build -d
docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head

# (optional) persist evidence
docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.evidence.yml up -d

# smoke
bash scripts/smoke_v084.sh
```
