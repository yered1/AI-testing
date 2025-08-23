
# Repo Cleanup Guide (safe)

- `scripts/run_repo_doctor.sh`: audit only
- `scripts/cleanup_safe.sh`: remove caches (pyc, __pycache__, .pytest_cache, .DS_Store)
- Nothing else is removed or modified. For deeper consolidation, review the audit report and decide explicitly.
