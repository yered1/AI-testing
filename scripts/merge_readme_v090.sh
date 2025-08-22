#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if ! grep -q "Delta v0.9.0" README.md; then
  echo -e "\n\n" >> README.md
  cat README_DELTA_v090.md >> README.md
  echo "README updated with v0.9.0 delta."
else
  echo "README already contains v0.9.0 delta."
fi
