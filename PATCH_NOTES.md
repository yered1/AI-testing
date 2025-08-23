
# Patch Notes — 2025-08-23T03:48:38.067885Z

This patch continues the work to solidify the v2 API and agent orchestration. It targets three high‑impact gaps:

1) **Reliable job leasing + agent matching (`lease2`)**
2) **Run lifecycle correctness (mark runs `failed` vs `completed`; mark jobs `running`)**
3) **Artifact discovery endpoint for agents (index)**

It also standardizes agent defaults and enables basic structured logging.

## What changed

### Backend (FastAPI)

- **NEW:** `orchestrator/routers/v2_artifacts_index.py`
  - Implements `GET /v2/runs/{run_id}/artifacts/index.json` returning a simple index of artifacts for a run (id, label, kind, path, created_at).
  - Enforced tenant isolation via PostgreSQL RLS and `X-Tenant-Id`/Principal.
  - Hooked into app through `bootstrap_extras.py`.

- **IMPROVED:** `orchestrator/routers/v2_agents_bus_lease2.py`
  - Rewritten to **atomically** lease jobs using `FOR UPDATE SKIP LOCKED`, preventing double‑leasing under load.
  - Accepts optional JSON body: `{ "kinds": ["semgrep", "zap", ...] }` to match jobs by adapter kind.
  - Updates agent `last_seen` and sets job `lease_expires_at` (10m).

- **FIXED:** `orchestrator/app_v2.py`
  - **/v2/jobs/{job_id}/events**: marks job `running` when it receives a `"job.started" | "job.running" | "adapter.started"` event.
  - **/v2/jobs/{job_id}/complete**: when the last job finishes, the run now ends as:
    - `failed` if **any** job in the run finished with `failed`
    - otherwise `completed`
  - Emits `run.failed` or `run.completed` events.

- **NEW:** `orchestrator/logging_setup.py` and auto‑import from `bootstrap_extras.py`
  - Minimal logging setup honoring `LOG_LEVEL` (defaults to `INFO`).

- **UPDATED:** `orchestrator/bootstrap_extras.py`
  - Includes the new `v2_artifacts_index` router.

### Agents

- **Standardized ORCH_URL default** to `http://localhost:8080` for consistency:
  - `agents/semgrep_agent/agent.py`
  - `agents/mobile_apk_agent/agent.py`

- **Lease2 with kinds:**
  - `agents/nuclei_agent_v2/agent.py` now calls `/v2/agents/lease2` with `{ "kinds": ["nuclei"] }`.
  - `agents/zap_agent_v2/agent.py` now calls `/v2/agents/lease2` with `{ "kinds": ["zap"] }`.

> Note: All agents still respect `ORCH_URL`, `TENANT_ID`, and `AGENT_TOKEN` environment variables. When running in Docker Compose, set `ORCH_URL=http://orchestrator:8080`.

## How to apply

1. **Back up** your working tree.
2. Copy the modified files from this patch into your repo:

```
orchestrator/logging_setup.py
orchestrator/bootstrap_extras.py
orchestrator/app_v2.py
orchestrator/routers/v2_artifacts_index.py
orchestrator/routers/v2_agents_bus_lease2.py
agents/semgrep_agent/agent.py
agents/mobile_apk_agent/agent.py
agents/nuclei_agent_v2/agent.py
agents/zap_agent_v2/agent.py
PATCH_NOTES.md
```

3. **Rebuild & migrate** (if using Docker Compose v2 manifests in `infra/`):

```bash
make up
make migrate
make logs
```

No new tables were introduced in this patch, so only a restart is typically required.

4. **Smoke test**:
   - Create an agent token: `POST /v2/agent_tokens` (via UI or API).
   - Start an agent (e.g., Semgrep): set `AGENT_TOKEN`, `TENANT_ID`, and `ORCH_URL`, then run the agent container.
   - Start a run with a plan containing adapters for that agent kind.
   - Observe:
     - Agents successfully lease via `/v2/agents/lease2` and only pick matching jobs.
     - Jobs flip to `running` and then `succeeded/failed`.
     - Run status finalizes as `completed` or `failed` accordingly.
     - `GET /v2/runs/{run_id}/artifacts/index.json` returns artifacts for chaining steps.

## Why these changes

- **Lease reliability:** `FOR UPDATE SKIP LOCKED` is the recommended pattern in Postgres to implement robust, high‑concurrency job queues.
- **Lifecycle correctness:** Downstream automation (reports/approvals) depends on accurate run status.
- **Agent chaining:** Multiple agents already try to pull an artifacts index; providing a first‑class endpoint unblocks that flow.

## Notes / next steps

- If you keep `/v1/*` around for compatibility, consider attaching a `Warning: 299` response header to each v1 endpoint and documenting the v2 equivalent.
- Consider adding an `agent_constraints` column on `jobs` to support richer matching beyond adapter prefixes.
- Add periodic **lease renewal/expired‑lease requeue** (cron/background task) to handle crashed agents.
- Normalize finding payloads across agents (`title`, `severity`, `description`, `assets`, `tags`) and expose a typed schema in `/v2/runs/{run_id}/findings`.

