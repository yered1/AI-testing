# Delta v1.5.7 — CI: Alembic path + logging, OPA/db overrides; Brain pkg init

This drop fixes the CI migration sequence by:
- Running Alembic from **/app/orchestrator** with `PYTHONPATH=/app`.
- Using a **CI-specific Alembic config** (`orchestrator/alembic.ci.ini`) that includes logging formatter `formatter_generic`.
- Loading `Base` **without importing the full package** via `alembic/env_ci.py` (avoids extras/brain imports during migrations).
- For OPA, forcing a valid tag and mounting only `policies_enabled/` with a minimal valid policy.
- Ensuring DB creds/DSN are consistent for CI and waiting on DB health before migrate.

**Apply:**
```bash
git checkout -b fix/ci-v157
unzip -o ai-testing-overlay-v157.zip
git add -A && git commit -m "v1.5.7: CI alembic path+ini+env; OPA/DB overrides; brain pkg init"
```

**Run in CI (or locally mirroring CI):**
```bash
bash scripts/ci_migrate_v157.sh
bash scripts/ci_stack_up_v157.sh
bash scripts/wait_for_api_v157.sh
python scripts/ci_smoke.py
```

**Notes:**
- Added package markers: `orchestrator/brain/__init__.py`, `orchestrator/brain/providers/__init__.py` to avoid import-package issues at runtime.
- You can patch your existing workflow with `bash scripts/ci_patch_v157.sh`.
