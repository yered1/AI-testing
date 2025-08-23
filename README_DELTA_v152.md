# Delta v1.5.2 — CI fix: run migrations before API + OPA image compat + health wait

**Why CI failed:** orchestrator attempted to start before the DB schema existed, then crashed; `/health` never came up.

**What changed:** 
- New GitHub Actions workflow `ci_v2.yml` that:
  1) Builds the orchestrator image
  2) Starts **db+opa** only (with OPA compat override)
  3) Waits for DB ready
  4) Runs migrations with an **ephemeral orchestrator container**
  5) Starts the full stack with CI overrides (+health)
  6) Waits for `/health` and runs the Python smoke
- Compose overrides:
  - `infra/docker-compose.opa.compat.yml` – uses a valid OPA tag (default `openpolicyagent/opa:0.65.0`)
  - `infra/docker-compose.health.yml` – DB healthcheck + orchestrator depends_on DB healthy
- Scripts:
  - `scripts/wait_for_api_v152.sh` – curl `/health` with timeout
  - `scripts/print_logs_on_fail_v152.sh` – dump service logs on failures
  - `scripts/ci_patch_v152.sh` – optional in-place patch of existing `.github/workflows/ci.yml`

**Local mirror of CI:** `bash scripts/ci_local_up_v152.sh` (starts DB+OPA, migrates, starts API, waits for `/health`).
