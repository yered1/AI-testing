#!/usr/bin/env bash
set -euo pipefail
TOOLS_MAIN="agents/kali_os_agent/tools.yaml"
EXTRA="agents/kali_os_agent/tools_extras/gobuster_ffuf_sqlmap.yaml"

mkdir -p "$(dirname "$TOOLS_MAIN")"
if [ ! -f "$TOOLS_MAIN" ]; then
  echo "tools:" > "$TOOLS_MAIN"
fi

echo "" >> "$TOOLS_MAIN"
echo "# == merged from tools_extras/gobuster_ffuf_sqlmap.yaml ==" >> "$TOOLS_MAIN"
awk 'f;/^tools:/ && ++n==1{f=1;next}' "$EXTRA" >> "$TOOLS_MAIN"
echo "Merged into $TOOLS_MAIN"
