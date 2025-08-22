# Delta v0.8.2 — Additive Endpoints (No Overwrites)

This overlay adds missing v2 API modules as **APIRouters**, auto-loaded via `orchestrator/__init__.py`.
No existing files are overwritten.

**Included endpoints**:
- Quotas: `POST /v2/quotas`, `GET /v2/quotas/{tenant_id}`
- Approvals: `POST /v2/approvals`, `POST /v2/approvals/{id}/decide`, `GET /v2/approvals`
- Findings: `POST/GET /v2/runs/{run_id}/findings`
- Artifacts: `POST /v2/runs/{run_id}/artifacts`
- Reports: `GET /v2/reports/run/{run_id}.{json|md|html}`
- Agents bus: `POST /v2/agent_tokens`, `POST /v2/agents/register`, `POST /v2/agents/heartbeat`, `POST /v2/agents/lease`, `POST /v2/jobs/{job_id}/{events|complete}`, `GET /v2/agents`
- Brain: `POST /v2/engagements/{id}/plan/auto`, `POST /v2/brain/feedback`, `GET /v2/brain/providers`
- Listings: `GET /v2/runs/recent`

> No changes to compose or app entrypoint required. Import is automatic via package `__init__`.
