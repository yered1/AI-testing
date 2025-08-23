#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if ! grep -q "v1.5.4" README.md 2>/dev/null; then
  echo -e "\n\n" >> README.md
  cat README_DELTA_v154.md >> README.md
  echo "README updated with v1.5.4 delta."
else
  echo "README already contains v1.5.4 delta."
fi
