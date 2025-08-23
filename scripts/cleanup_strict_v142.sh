#!/usr/bin/env bash
set -euo pipefail
DRY="${DRY_RUN:-1}"
# Safe default: remove caches/junk only
declare -a GLOBS=(
  "**/__pycache__"
  "**/*.pyc"
  "**/*.pyo"
  "**/.pytest_cache"
  "**/.mypy_cache"
  "**/.tox"
  "**/.coverage*"
  "**/htmlcov"
  "**/.DS_Store"
  "**/__MACOSX"
  "**/Thumbs.db"
  "**/.idea"
  "**/.vscode"
)
shopt -s globstar nullglob
for g in "${GLOBS[@]}"; do
  for p in $g; do
    echo "CLEAN: $p"
    if [[ "$DRY" != "1" ]]; then
      rm -rf "$p" || true
      [[ -d "$p" ]] && rmdir "$p" 2>/dev/null || true
    fi
  done
done
if [[ "$DRY" == "1" ]]; then
  echo "Dry run complete. Set DRY_RUN=0 to actually delete."
else
  echo "Cleanup complete."
fi
