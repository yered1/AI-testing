# AI-Testing — Updated Development Plan (Replacement)
_Date: 2025-08-23 22:43 UTC_

This document **replaces** the existing `DEVELOPMENT_PLAN.md`. It is based on a full, per-file review of the attached repository and maps what **exists now** vs. what is **missing**, then lays out **specific next steps** with clear owners and acceptance criteria.

## 1) Repository Snapshot

- Project root: `AI-testing/`
- Files (source tree only): **262**
- macOS resource files in ZIP (`__MACOSX`): **326** _(delete; non-source)_
- Python files: **98**  • Routes discovered: **82**
- JSON: **52** (all valid) • YAML: **9** (all valid)
- Quick issues: 1 Python file(s) with syntax errors; 15 Python file(s) contain '...' placeholders (incomplete stubs)

### Notable mismatches / blockers

- infra/docker-compose.agents.enhanced.yml references 'infra/agent.aws.Dockerfile' but file on disk is 'infra/agent.aws.DockerFile' (case-sensitive mismatch)
- Agents and compose use both ORCH_URL and ORCHESTRATOR_URL; standardize to a single env var (e.g., ORCH_URL)
- Auth/tenancy reference models.Membership and Role enums which are not present; add models/membership.py and models/role.py or adjust code.
- orchestrator/reports missing __init__.py
- Two FastAPI apps exist (orchestrator/app.py and orchestrator/routers/app.py). Docker runs app.py (stub/in-memory). Consolidate to a single app and include all routers.

## 2) Feature Matrix (what’s present)

| Capability | Status |
|---|---|
| Agents Register | ✅ Available |
| Agents Lease | ✅ Available |
| Agents Lease2 | ✅ Available |
| Jobs Complete | ✅ Available |
| Artifacts Upload | ✅ Available |
| Artifacts Index | ✅ Available |
| Artifacts Download | ✅ Available |
| Findings Post | ✅ Available |
| Reports Enhanced Html | ✅ Available |
| Reports Bundle | ✅ Available |
| Brain Autoplan V2 | ✅ Available |
| Brain V3 Guarded | ✅ Available |
| Ui Routes | ✅ Available |
| Health | ✅ Available |

**Notes**
- Enhanced PDF reports require `REPORTER_URL` (e.g., a Gotenberg service); compose does not currently include a reporter.
- Artifacts index and downloads are implemented; ensure `EVIDENCE_DIR` is mounted as a volume.

## 3) Architecture as-implemented (today)

- **Orchestrator (FastAPI)** — Both `orchestrator/app.py` (simplified, in-memory pieces) and `orchestrator/routers/app.py` (modular, DB-backed routers). Docker runs `uvicorn app:app`, i.e., the simpler app. Consolidation required.
- **DB layer** — `orchestrator/db.py` provides `Base` and `get_db`. However, ORM models import `Base` from `orchestrator/models/base.py`, which is a stub. Alembic migrations (`orchestrator/alembic/versions/0001..0008`) appear complete but may not load metadata until `Base` is fixed.
- **Routers (v2/v3 + UI)** — Rich set of v2 endpoints (agents bus, artifacts, findings, reports) plus v3 brain (`v3_brain.py`, `v3_brain_guarded.py`). Jinja UI routes under `/ui/*` and a minimal React app in `/ui`.
- **Agents** — Multiple agents (`agents/*`) plus a generic `agent/agent.py`. Authentication headers vary (`X-Agent-Token` vs `X-Agent-Id`/`X-Agent-Key`). Uploads hit `/v2/jobs/{{id}}/artifacts` and events/complete endpoints.
- **Catalog** — Test definitions under `orchestrator/catalog/tests` and packs under `orchestrator/catalog/packs`.
- **Reports** — Templating under `orchestrator/report_templates/*`, code in `orchestrator/reports/*` (missing `__init__.py`).
- **Policies (OPA)** — Rego policies in `policies/` and `policies_enabled/`; compose includes `opa`.

## 4) What’s missing or inconsistent (gap analysis)

**Critical (must-fix to reach a runnable, cohesive v2 stack)**
1. **Single source of truth for the FastAPI app.** Decide on `routers/app.py` (recommended) and update Docker entrypoint to `uvicorn routers.app:app`. Remove/merge the stub in `orchestrator/app.py`, porting any needed endpoints.
2. **Unify SQLAlchemy base.** Replace `orchestrator/models/base.py` with a thin import from `orchestrator/db.py` _or_ move `Base` to `models/base.py` and import it from `db.py`. Ensure Alembic `env.py` imports the right `Base`.
3. **Auth/tenancy model.** `auth.py`/`tenancy.py` reference `Membership` + `Role` that don’t exist. Add `models/membership.py` and a simple `Role` enum (or collapse to the existing `User.role` string). Update queries accordingly.
4. **Agent auth contract.** Standardize on **`X-Agent-Id` + `X-Agent-Key`** for agents and **`ORCH_URL`** for the orchestrator URL. Update all agents and compose files. Remove the legacy `X-Agent-Token` path unless you intend to support both.
5. **Broken files.** Fix `orchestrator/bootstrap_extras.py` (syntax) and add `orchestrator/reports/__init__.py`.

**High priority**
6. **Brain providers.** `openai_chat.py` / `anthropic.py` contain scaffolding; wire them via `plan_engine.py` and expose via `v3_brain_guarded.py`. Add environment-driven enable/disable and good error messaging.
7. **Reports → PDF.** Add `reporter` service to compose (e.g., Gotenberg) and pass `REPORTER_URL`. Alternatively, add a pure-Python fallback (e.g., WeasyPrint) under a feature flag.
8. **Compose correctness.** Fix case mismatch for `infra/agent.aws.DockerFile` vs `docker-compose.agents.enhanced.yml`. Verify volumes: mount `/evidence` and `alembic` correctly.
9. **Consistency of settings.** Centralize env names in `orchestrator/settings.py` and consume there throughout (DB URL, EVIDENCE_DIR, OPA_URL, REDIS_URL, LLM keys).

**Medium**
10. **CI pipeline.** Add GH Actions workflow to build, run migrations, and execute smoke tests (`scripts/ci_*`). Cache Docker layers and Python deps.
11. **UI.** Either serve the Jinja UI only (server-side) or build & host the React UI from `/ui` (vite build) behind `/ui/`. Avoid split-brain UIs.
12. **Docs.** Fill out `docs/API.md` and include OpenAPI link, common curls, and security model.

## 5) Concrete next steps (by area)

### A. Orchestrator app (owner: Backend)
- [ ] Move canonical app to `routers/app.py`.  
  **Change**: In `infra/orchestrator.Dockerfile`, set the CMD to `uvicorn routers.app:app --host 0.0.0.0 --port 8080`.  
  **Accept**: `/docs` loads; `/health` returns 200; v2/v3 routes visible.

- [ ] Delete or archive `orchestrator/app.py` _or_ make it import and re-export `routers.app:app`.  
  **Accept**: one app only; no divergent behavior.

- [ ] Add `orchestrator/bootstrap_extras.py` patch:
  ```python
  # orchestrator/bootstrap_extras.py
  from .routers import (
      v2_agents_bus, v2_agents_bus_lease2, v2_artifacts, v2_artifacts_index,
      v2_artifacts_downloads, findings_v2, v2_findings_reports,
      v2_quotas_approvals, v2_listings, v2_brain, v3_brain_guarded,
      ui_pages, ui_brain, ui_code, ui_builder, ui_mobile
  )

  def mount_all(app):
      for r in [v2_agents_bus, v2_agents_bus_lease2, v2_artifacts, v2_artifacts_index,
                v2_artifacts_downloads, findings_v2, v2_findings_reports,
                v2_quotas_approvals, v2_listings, v2_brain, v3_brain_guarded,
                ui_pages, ui_brain, ui_code, ui_builder, ui_mobile]:
          app.include_router(r.router)
  ```

### B. DB & migrations (owner: Backend)
- [ ] Replace `orchestrator/models/base.py` with:
  ```python
  # orchestrator/models/base.py
  from ..db import Base, get_db  # re-export for model modules and Alembic
  ```
  **Accept**: `alembic revision --autogenerate` and `alembic upgrade head` work.

- [ ] Implement missing `Membership` model and optional `Role` enum; update `auth.py`/`tenancy.py`.
  **Accept**: Joining a tenant yields a `Membership` row; guarded routes pass.

- [ ] Add `orchestrator/reports/__init__.py` (empty).  
  **Accept**: `from orchestrator.reports import render` succeeds.

### C. Agents & Bus (owner: Agents)
- [ ] Standardize env to **`ORCH_URL`** across all agents and compose files.  
  **Accept**: Agents come online and lease jobs.

- [ ] Standardize auth to **`X-Agent-Id` + `X-Agent-Key`**. Remove legacy `X-Agent-Token` code paths.  
  **Accept**: `/v2/agents/register` returns id/key; `/v2/agents/lease2` works with `kinds`.

- [ ] Fix compose case mismatch: rename file to `infra/agent.aws.Dockerfile` _or_ update compose to `agent.aws.DockerFile`.
  **Accept**: `docker compose -f infra/docker-compose.agents.enhanced.yml build` succeeds.

### D. Brain (owner: AI)
- [ ] Finish `openai_chat.py` and `anthropic.py` implementations; respect `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`.  
  **Accept**: `/v3/brain/plan/guarded` returns a plan using selected provider; Heuristic fallback works with `BRAIN_PROVIDER=heuristic`.

- [ ] Add `GET /v3/brain/providers` status endpoint (if not already exposed) returning availability and default.  
  **Accept**: returns provider info; toggles via env.

### E. Reports (owner: Backend)
- [ ] Add `reporter` service (e.g., Gotenberg) to compose and set `REPORTER_URL`.  
  **Accept**: `/v2/reports/enhanced/run/{run}.pdf` returns a file.

- [ ] Ensure `EVIDENCE_DIR` volume mounted and indexed by `/v2/runs/{id}/artifacts/index.json`.  
  **Accept**: index lists uploaded artifacts; downloads authorized.

### F. CI/CD (owner: DevOps)
- [ ] Add `.github/workflows/ci.yml` running `scripts/ci_stack.sh`, plus `scripts/print_logs_on_fail.sh`.  
  **Accept**: PRs build, migrate DB, boot stack, pass smoke.

### G. UI (owner: Frontend)
- [ ] Decide on UI path. If React: build with Vite and serve static from orchestrator under `/ui/`. If Jinja: remove `/ui` React folder.  
  **Accept**: One UI path; end-to-end flows work (create engagement → run plan → view findings/artifacts/report).

## 6) Risks & mitigations

- **Security**: Never enable intrusive tests by default. Keep `ALLOW_ACTIVE_SCAN=0` and add approvals flow. Enforce OPA once the policy matures.
- **Provider bill shock**: Add per-tenant quotas and require explicit opt-in for LLM providers.
- **Data**: Mount `/evidence` and back it up; store artifact metadata in DB.

## 7) Milestone plan (2 weeks)

**Day 1–2**: App consolidation, Base fix, missing models.  
**Day 3–4**: Agent auth env standardization; compose fixes.  
**Day 5–6**: Brain providers wiring; guarded endpoint.  
**Day 7–8**: Reports PDF & artifacts end-to-end.  
**Day 9–10**: UI decision + polish; CI pipeline.  
**Buffer**: 2 days for docs and acceptance.

## 8) Appendix A — Per-file review

{per_file_table}

---

_Authored automatically from repository contents; if anything looks off, it reflects the current files in the ZIP, not assumptions._
