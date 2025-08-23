#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.."; pwd)"
GI="$ROOT/.gitignore"
TPL="$ROOT/templates/gitignore.append"
touch "$GI"
while IFS= read -r line; do
  grep -qxF "$line" "$GI" || echo "$line" >> "$GI"
done < "$TPL"
echo "Updated .gitignore"
