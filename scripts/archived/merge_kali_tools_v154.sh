#!/usr/bin/env bash
set -euo pipefail
EXTRA="agents/kali_os_agent/tools_extras/naabu_masscan.yaml"
DEST="agents/kali_os_agent/tools.yaml"
if [ ! -f "$DEST" ]; then
  mkdir -p "$(dirname "$DEST")"
  cp "$EXTRA" "$DEST"
  echo "Created $DEST with extras."
  exit 0
fi
echo "" >> "$DEST"
cat "$EXTRA" >> "$DEST"
echo "Appended naabu/masscan extras to $DEST"
