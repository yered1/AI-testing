#!/usr/bin/env bash
set -Eeuo pipefail
if ! grep -q "v1.5.6 — CI Alembic Path Fix" README.md 2>/dev/null; then
  echo -e "\n\n" >> README.md
  cat README_DELTA_v156.md >> README.md
  echo "README updated with v1.5.6 delta."
else
  echo "README already contains v1.5.6 delta."
fi
