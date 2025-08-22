#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if ! grep -q "Delta v0.9.5" README.md; then
  echo -e "\n\n" >> README.md
  cat README_DELTA_v095.md >> README.md
  echo "README updated with v0.9.5 delta."
else
  echo "README already contains v0.9.5 delta."
fi
