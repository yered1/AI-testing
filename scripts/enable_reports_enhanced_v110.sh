#!/usr/bin/env bash
set -euo pipefail
BOOT="orchestrator/bootstrap_extras.py"
LINE="from .routers import v2_reports_enhanced"
LINE2="app.include_router(v2_reports_enhanced.router, tags=[\"reports\"])"
grep -q "v2_reports_enhanced" "$BOOT" || {
  echo "Patching $BOOT"
  printf "\n%s\n%s\n" "$LINE" "$LINE2" >> "$BOOT"
  echo "Done."
}
