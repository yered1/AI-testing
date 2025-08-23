#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if ! grep -q "Delta v1.5.2" README.md; then
  printf "\n\n" >> README.md
  cat README_DELTA_v152.md >> README.md
  echo "README updated with v1.5.2 delta."
else
  echo "README already contains v1.5.2 delta."
fi
