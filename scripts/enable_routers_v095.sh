#!/usr/bin/env bash
set -euo pipefail
F="orchestrator/bootstrap_extras.py"
if ! grep -q "v2_agents_bus_lease2" "$F"; then
  cat >> "$F" <<'EOF'

# --- v0.9.5: extra routers (lease2 + agent artifacts) ---
from .routers import v2_agents_bus_lease2, v2_agents_artifacts
app.include_router(v2_agents_bus_lease2.router, tags=["agents"])
app.include_router(v2_agents_artifacts.router, tags=["agents","artifacts"])
EOF
  echo "Appended lease2 + agent artifacts routers to $F"
else
  echo "Routers already present in $F"
fi
