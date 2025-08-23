#!/usr/bin/env bash
set -euo pipefail

: "${ORCH_URL:?ORCH_URL is required}"
: "${TENANT_ID:?TENANT_ID is required}"
: "${AGENT_TOKEN:?AGENT_TOKEN is required}"

PREFIX="/opt/kali-os-agent"
sudo mkdir -p "$PREFIX"
sudo cp -r agents/kali_os_agent "$PREFIX/"
sudo mkdir -p /etc/kali-os-agent
sudo cp "$PREFIX/kali_os_agent/tools.yaml" /etc/kali-os-agent/tools.yaml

# Config
cat <<EOF | sudo tee /etc/kali-os-agent/config.env >/dev/null
ORCH_URL=$ORCH_URL
TENANT_ID=$TENANT_ID
AGENT_TOKEN=$AGENT_TOKEN
ALLOW_ACTIVE_SCAN=${ALLOW_ACTIVE_SCAN:-0}
TOOLS_FILE=/etc/kali-os-agent/tools.yaml
EOF

# Service
cat <<'UNIT' | sudo tee /etc/systemd/system/kali-os-agent.service >/dev/null
[Unit]
Description=Kali OS Agent
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
EnvironmentFile=/etc/kali-os-agent/config.env
WorkingDirectory=/opt/kali-os-agent/kali_os_agent
ExecStart=/usr/bin/env python3 /opt/kali-os-agent/kali_os_agent/agent.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable --now kali-os-agent
echo "Kali OS Agent installed and started."
