#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
T="orchestrator/bootstrap_extras.py"
ins() {
  line="$1"
  if ! grep -q "$line" "$T"; then
    echo "$line" >> "$T"
  fi
}
ins "from orchestrator.routers.v3_brain_guarded import router as router_brain_guarded"
ins "app.include_router(router_brain_guarded)"
ins "from orchestrator.routers.ui_brain import router as router_ui_brain"
ins "app.include_router(router_ui_brain)"
echo "Brain guarded & UI mounted."
