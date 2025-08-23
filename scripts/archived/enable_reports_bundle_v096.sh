#!/usr/bin/env bash
set -euo pipefail
FILE="orchestrator/bootstrap_extras.py"
LINE="from .routers import v2_reports_bundle"
if ! grep -q "$LINE" "$FILE"; then
  echo "$LINE" >> "$FILE"
  echo "app.include_router(v2_reports_bundle.router, tags=[\"reports\"]) " >> "$FILE"
  echo "Added v2_reports_bundle to bootstrap_extras.py"
else
  echo "v2_reports_bundle already referenced."
fi
