#!/usr/bin/env bash
set -euo pipefail
FILE="orchestrator/bootstrap_extras.py"
LINE="from .routers import ui_mobile"
INCL="app.include_router(ui_mobile.router, tags=[\"ui\"])"
if ! grep -q "ui_mobile" "$FILE"; then
  echo "" >> "$FILE"
  echo "$LINE" >> "$FILE"
  echo "$INCL" >> "$FILE"
  echo "ui_mobile mounted."
else
  echo "ui_mobile already mounted."
fi
