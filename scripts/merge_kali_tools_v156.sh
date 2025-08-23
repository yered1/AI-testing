#!/usr/bin/env bash
set -Eeuo pipefail
BASE="agents/kali_os_agent/tools.yaml"
EXTRA="agents/kali_os_agent/tools_extras/gobuster_ffuf_sqlmap.yaml"
mkdir -p "$(dirname "$BASE")"
if [ ! -f "$BASE" ]; then
  echo "tools:" > "$BASE"
fi
echo "" >> "$BASE"
sed '/^#/d' "$EXTRA" >> "$BASE"
echo "Merged extra Kali tools into $BASE"
