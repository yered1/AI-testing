#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.."; pwd)"
BOOT="$ROOT/orchestrator/bootstrap_extras.py"
# Add includes if not present
grep -q "v2_artifacts_downloads" "$BOOT" ||   echo -e "\nfrom .routers import v2_artifacts_downloads" >> "$BOOT"
grep -q "ui_code" "$BOOT" ||   echo -e "\nfrom .routers import ui_code" >> "$BOOT"
# And attach to app if not already
grep -q "v2_artifacts_downloads.router" "$BOOT" ||   echo -e "\napp.include_router(v2_artifacts_downloads.router, tags=[\"artifacts\"])" >> "$BOOT"
grep -q "ui_code.router" "$BOOT" ||   echo -e "\napp.include_router(ui_code.router, tags=[\"ui\"])" >> "$BOOT"
echo "Routers added to bootstrap_extras.py"
