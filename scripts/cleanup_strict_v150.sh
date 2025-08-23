#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.."; pwd)"
cd "$ROOT"

DRY_RUN="${DRY_RUN:-1}"

patterns=(
  "__MACOSX"
  ".DS_Store"
  "**/__pycache__"
  "**/*.pyc"
  "**/*.pyo"
  "**/.pytest_cache"
  "**/.mypy_cache"
  "**/.tox"
  "**/.coverage*"
  "**/htmlcov"
  "**/Thumbs.db"
  ".idea"
  ".vscode"
)

found=()
for pat in "${patterns[@]}"; do
  while IFS= read -r -d '' f; do
    found+=("$f")
  done < <(eval "find . -path './.git' -prune -o -name \"${pat##*/}\" -o -path \"$pat\" -print0 2>/dev/null" || true)
done

# Unique
declare -A seen
unique=()
for f in "${found[@]}"; do
  if [[ -z "${seen[$f]+x}" ]]; then
    seen[$f]=1
    unique+=("$f")
  fi
done

echo "Cleanup candidates (${#unique[@]}):"
printf ' - %s\n' "${unique[@]}"

if [[ "${DRY_RUN}" != "0" ]]; then
  echo "DRY_RUN=1 -> Not deleting. Set DRY_RUN=0 to delete."
  exit 0
fi

# Backup archive
ts=$(date +%Y%m%d_%H%M%S)
tar czf "pre_cleanup_backup_${ts}.tar.gz" "${unique[@]}" || true
echo "Backup archive created: pre_cleanup_backup_${ts}.tar.gz"

# Delete
for f in "${unique[@]}"; do
  rm -rf "$f" || true
done
echo "Cleanup complete."
