
#!/usr/bin/env bash
set -euo pipefail
FILE="orchestrator/bootstrap_extras.py"
ROUTER_IMPORT="from .routers import ui_builder"
INCLUDE_LINE="app.include_router(ui_builder.router, tags=[\"ui\"])\ntry:\n    ui_builder.mount_static(app)\nexcept Exception:\n    pass\n"
if ! grep -q "routers import ui_builder" "$FILE"; then
  echo "$ROUTER_IMPORT" >> "$FILE"
fi
if ! grep -q "ui_builder.router" "$FILE"; then
  printf "\n%s" "$INCLUDE_LINE" >> "$FILE"
fi
echo "ui_builder mounted."
