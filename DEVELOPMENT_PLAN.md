
# Development Plan (Actionable for LLM Agents)

This plan turns the audit into concrete steps. Claude (or any LLM) should **only create new files** (no in-place edits), placing them under `patches/v2.0.0/` with clear filenames. Each new file must include:
- The **relative destination path** in the first commented line.
- The **rationale** (why the change is needed).
- The **full replacement content** for that file or a **unified diff** if minimal changes.

After a batch, a human/dev can apply them and commit.

---

## 0) Repository Hygiene (Safe)
**Goals**: remove OS junk, add missing `__init__.py`, fix .gitignore.

**Files to generate**:
1. `patches/v2.0.0/scripts/cleanup_safe.sh` – deletes `__MACOSX/`, `.DS_Store`, `__pycache__/`, `*.pyc`, `.pytest_cache/`.
2. `patches/v2.0.0/templates/gitignore.append` – add macOS/Python/Node/Docker ignores.
3. `patches/v2.0.0/scripts/add_missing_inits.py` – scan python dirs with .py files and inject `__init__.py` where missing (no overwrite).

---

## 1) Alembic / DB Migrations (Critical CI)
**Findings**: Alembic folder or INI missing/invalid; formatter_generic missing.

**Actions**:
- If `orchestrator/alembic` is absent, **create** baseline Alembic structure under that path with env.py, versions/.
- Provide `orchestrator/alembic.ini` containing `[formatter_generic]` and proper logging.
- Ensure env loads `DATABASE_URL/DB_URL/DB_DSN`. Use `PYTHONPATH=/app` and `workdir=/app/orchestrator` in CI.

**Files to generate**:
1. `patches/v2.0.0/orchestrator/alembic.ini`
2. `patches/v2.0.0/orchestrator/alembic/env.py`
3. `patches/v2.0.0/orchestrator/alembic/versions/0001_init.py` – create core tables if missing (tenants, users, memberships, engagements, plans, runs, jobs, agents, run_events, artifacts).
4. `patches/v2.0.0/.github/workflows/ci_migrate_step.md` – instructions to run alembic with proper env.

---

## 2) OPA & Policies (Boot blocker)
**Findings**: Compose references bad image tag; rego parse issues (`or` usage).

**Actions**:
- Add `infra/docker-compose.opa.compat.yml` overriding OPA image to `openpolicyagent/opa:0.65.0`.
- Introduce `policies_enabled/` with minimal valid policy; mount that path in compose; disable legacy policies until fixed.
- Provide `policies/policy.v3.rego` fixed version (no inline `or` in same rule body).

**Files**:
1. `patches/v2.0.0/infra/docker-compose.opa.compat.yml`
2. `patches/v2.0.0/policies_enabled/policy.rego`
3. `patches/v2.0.0/policies/policy.v3.rego` (fixed).

---

## 3) Router Mount Completeness
**Findings**: Some routers in `orchestrator/routers/` not included.

**Actions**:
- Generate `scripts/repair_bootstrap.py` to auto-append `include_router()` for any missing router.
- Alternatively, produce a canonical `orchestrator/bootstrap_extras.py` that imports & mounts all routers (idempotent).

**Files**:
1. `patches/v2.0.0/scripts/repair_bootstrap.py`
2. `patches/v2.0.0/orchestrator/bootstrap_extras.py` (full content).

---

## 4) Brain (LLM Providers) – Implement & Guard
**Findings**: Missing `__init__.py` in `orchestrator/brain` or providers; providers stubs.

**Actions**:
- Add `__init__.py` markers.
- Implement provider stubs: `openai_chat.py`, `anthropic.py` with env-driven toggles; add `heuristic.py` as fallback.
- Implement `autoplan` endpoint in `routers/v3_brain.py` that returns a plan from provider.

**Files**:
1. `patches/v2.0.0/orchestrator/brain/__init__.py`
2. `patches/v2.0.0/orchestrator/brain/providers/__init__.py`
3. `patches/v2.0.0/orchestrator/brain/providers/openai_chat.py`
4. `patches/v2.0.0/orchestrator/brain/providers/anthropic.py`
5. `patches/v2.0.0/orchestrator/brain/providers/heuristic.py`
6. `patches/v2.0.0/orchestrator/routers/v3_brain.py`

---

## 5) Artifacts & Findings
**Actions**:
- Add models and endpoints for findings: `GET/POST /v2/runs/{id}/findings`.
- Implement artifact index: `GET /v2/runs/{id}/artifacts/index.json` listing artifacts (id,label,kind,filename).
- Implement `GET /v2/artifacts/{id}/download` streaming file.

**Files**:
1. `patches/v2.0.0/orchestrator/routers/v2_findings.py`
2. `patches/v2.0.0/orchestrator/routers/v2_artifacts.py`

---

## 6) Reporting Service Wiring
**Actions**:
- Implement `services/reporter/app.py` render endpoint accepting JSON context and returning HTML/PDF (MVP can return HTML).
- Add orchestrator client to call reporter at run completion and store report as artifact.

**Files**:
1. `patches/v2.0.0/services/reporter/app.py`
2. `patches/v2.0.0/orchestrator/services/reporter_client.py`

---

## 7) Agents Consistency & Safety
**Actions**:
- Merge redundant dev agents; standardize env (`ORCH_URL`, `TENANT_ID`, `AGENT_TOKEN`).
- Enforce allowlist for remote/kali agent tools via `tools.yaml`. Add examples: `naabu_basic`, `masscan_safe`, `gobuster_dns_safe`, `ffuf_post_json`, `sqlmap_smart`.
- Ensure timeouts and artifact uploads consistent.

**Files**:
1. `patches/v2.0.0/agents/kali_os_agent/tools.yaml`
2. `patches/v2.0.0/agents/AGENT_README.md`

---

## 8) UI Enhancements
**Actions**:
- Add Findings view: call `/v2/runs/{id}/findings` and render table; add “Download Report” button.
- Add Approvals panel to approve pending runs.

**Files**:
1. `patches/v2.0.0/ui/src/pages/Findings.tsx`
2. `patches/v2.0.0/ui/src/components/ReportButton.tsx`

---

## 9) CI Scripts (Deterministic)
**Actions**:
- Build orchestrator, bring up db+opa with compat, run alembic with `PYTHONPATH=/app -w /app/orchestrator -c alembic.ini`, then up full stack, wait `/health`.
- On failure, print logs.

**Files**:
1. `patches/v2.0.0/scripts/ci_migrate.sh`
2. `patches/v2.0.0/scripts/ci_stack.sh`
3. `patches/v2.0.0/scripts/wait_for_api.sh`
4. `patches/v2.0.0/scripts/print_logs_on_fail.sh`
5. `patches/v2.0.0/.github/workflows/ci.yml` (new or patched)

---

## 10) Optional Advanced Features (Backlog)
- Cloud audit agent (AWS ScoutSuite) with secure secrets handling.
- Privilege escalation agent (LinPEAS/WinPEAS via SSH). 
- Metasploit agent (msfrpcd) for verified exploitation (approval-gated).
- Fuzzing jobs (ZAP fuzzer API; wfuzz templates).

Document each as separate RFC markdown files in `docs/rfc/` with skeleton code stubs under `patches/`.
