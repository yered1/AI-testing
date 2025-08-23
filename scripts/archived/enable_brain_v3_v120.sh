#!/usr/bin/env bash
set -euo pipefail
f="orchestrator/bootstrap_extras.py"
ins=$'# v1.2.0 brain v3 router\nfrom .routers import v3_brain\napp.include_router(v3_brain.router, tags=[\"brain-v3\"])'
grep -q "routers import v3_brain" "$f" || echo "$ins" >> "$f"
echo "Brain v3 router mounted."
