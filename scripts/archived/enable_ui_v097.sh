#!/usr/bin/env bash
set -euo pipefail
BE="orchestrator/bootstrap_extras.py"
SNIP=$'# --- v0.9.7 UI include ---\nfrom .routers import ui_pages as ui_pages_router\napp.include_router(ui_pages_router.router, tags=[\"ui\"])\\ntry:\\n    ui_pages_router.mount_static(app)\\nexcept Exception:\\n    pass\\n'
if ! grep -q "routers import ui_pages" "$BE"; then
  printf "\n%s" "$SNIP" >> "$BE"
  echo "UI router appended to $BE"
else
  echo "UI router already present; no change."
fi
