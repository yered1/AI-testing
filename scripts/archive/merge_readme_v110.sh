#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if ! grep -q "Delta v1.1.0" README.md; then
  echo -e "\n\n" >> README.md
  cat README_DELTA_v110.md >> README.md
  echo "README updated with v1.1.0 delta."
else
  echo "README already contains v1.1.0 delta."
fi
