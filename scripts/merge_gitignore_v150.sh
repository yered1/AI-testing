#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.."; pwd)"
cd "$ROOT"
if [ ! -f .gitignore ]; then
  touch .gitignore
fi
append="templates/gitignore.append"
if ! grep -q "Consolidated ignores" .gitignore; then
  echo "" >> .gitignore
  cat "$append" >> .gitignore
  echo "Merged templates/gitignore.append into .gitignore"
else
  echo ".gitignore already contains consolidated ignores"
fi
