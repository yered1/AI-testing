#!/usr/bin/env bash
set -euo pipefail
if ! grep -q "Delta v1.4.2" README.md 2>/dev/null; then
  echo -e "\n\n" >> README.md
  cat README_DELTA_v142.md >> README.md
  echo "README updated with v1.4.2 delta."
else
  echo "README already contains v1.4.2 delta."
fi
