# Repository Cleanup (Safe)

This guide explains how to identify and remove junk files safely, and how to fix missing router includes.

## 1) Audit
```bash
bash scripts/run_repo_doctor_v141.sh
# -> repo_audit_v141.json
```

## 2) Safe cleanup
```bash
bash scripts/cleanup_safe_v141.sh
```

## 3) Fix missing routers
```bash
bash scripts/fix_bootstrap_includes_v141.sh
```

## 4) Optional: Archive version deltas & merge scripts
```bash
CONFIRM=1 bash scripts/archive_docs_v141.sh
```

## 5) .gitignore hygiene
```bash
bash scripts/merge_gitignore_v141.sh
```
