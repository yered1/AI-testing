# Delta v0.9.6 — Report Bundle ZIP + Artifacts Index (additive)

Adds:
- **/v2/reports/run/{run_id}.zip** — one-click export: `report.md`, `report.html`, `report.json` + `artifacts/*` files
- **/v2/runs/{run_id}/artifacts/index.json** — machine-readable artifact list
- Router auto-mount script: `scripts/enable_reports_bundle_v096.sh`
- Smoke: `scripts/smoke_bundle_v096.sh`

## Apply
```bash
unzip -o ~/Downloads/ai-testing-overlay-v096.zip
git add -A && git commit -m "v0.9.6 overlay: report bundle zip + artifacts index"
bash scripts/enable_reports_bundle_v096.sh
```

## Use
```bash
# Download a zip bundle for a run
curl -L http://localhost:8080/v2/reports/run/<RUN_ID>.zip \\
  -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo' \\
  -o run_<RUN_ID>_bundle.zip
```

> The bundle reads files from `EVIDENCE_DIR` and includes only files present on disk and recorded in DB.
