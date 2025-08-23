# Delta v1.5.1 — CI fix for OPA image (no-rootless tag) (additive)

**Why your CI failed:** The compose file referenced `openpolicyagent/opa:0.65.0-rootless`. The OPA project no longer publishes `-rootless` variants (since v0.58, all images are rootless). Use the base tag instead (e.g., `openpolicyagent/opa:0.65.0`).

**What this adds:**

- `infra/docker-compose.opa.compat.yml` — overrides only the OPA image to `${OPA_IMAGE:-openpolicyagent/opa:0.65.0}`.
- `scripts/ci_fix_opa_v151.sh` — patches `.github/workflows/ci.yml` to include the compat override (idempotent).
- `scripts/ci_local_up_v151.sh` — local helper to start the full CI stack with the compat file and wait for `/health`.

## Apply

```bash
# Add overlay to your repo (from the repo root)
unzip -o ~/Downloads/ai-testing-overlay-v151.zip
git add -A
git commit -m "v1.5.1 overlay: CI fix for OPA image via compat compose"
```

## Patch your GitHub CI

```bash
bash scripts/ci_fix_opa_v151.sh
git add .github/workflows/ci.yml
git commit -m "ci: include OPA compat compose to fix OPA image tag"
git push
```

## Run locally (mirrors CI)

```bash
bash scripts/ci_local_up_v151.sh
python scripts/ci_smoke.py
```

> You can also set `OPA_IMAGE` environment variable to another known-good tag without editing files, e.g.:
> 
> ```bash
> OPA_IMAGE=openpolicyagent/opa:0.67.1 bash scripts/ci_local_up_v151.sh
> ```
