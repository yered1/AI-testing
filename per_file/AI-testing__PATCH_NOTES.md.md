# File: AI-testing/PATCH_NOTES.md

- Size: 887 bytes
- Kind: text
- SHA256: 852d49da7066935ccc069f54b8dbb96cb0550b66529c45f5840d91e85f6b0dfe

## Head (first 60 lines)

```
# Patch Notes (2025-08-23)

## What changed
- **Docker**: Orchestrator now serves the **v2** API by default (`uvicorn app_v2:app`).
- **Agents → Lease**: `/v2/agents/lease2` now:
  - Uses `FOR UPDATE SKIP LOCKED` to avoid double leasing.
  - Matches jobs by agent-provided `kinds` (e.g., `["semgrep"]`, `["zap"]`, `["nuclei"]`).
- **Run lifecycle**:
  - Jobs flip to `running` on `job.started`/`job.running`/`adapter.started`.
  - Runs end as **failed** if any job failed/canceled; else **completed**.
- **Artifacts index**:
  - `GET /v2/runs/{run_id}/artifacts/index.json` for agent chaining (Semgrep/Mobile).
- **Agents**:
  - Semgrep default `ORCH_URL` → `http://localhost:8080` (Compose sets it to orchestrator).
  - Nuclei/ZAP pass `{"kinds":[...]}` to `/v2/agents/lease2`.

## Apply
Unzip this patch into the repo root and rebuild orchestrator (see instructions in the chat).

```

