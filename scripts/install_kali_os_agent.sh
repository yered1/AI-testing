#!/usr/bin/env bash
set -euo pipefail

# Defaults (override via env or flags)
ORCH_URL="${ORCH_URL:-http://localhost:8080}"
TENANT_ID="${TENANT_ID:-t_demo}"
AGENT_TOKEN="${AGENT_TOKEN:-}"
AGENT_NAME="${AGENT_NAME:-kali-os}"
WORKDIR="${WORKDIR:-/var/lib/kali-os-agent}"
TOOLS_FILE="${TOOLS_FILE:-/etc/kali-os-agent/tools.yaml}"
UNIT_NAME="${UNIT_NAME:-kali-os-agent}"
ALLOW_ACTIVE_SCAN="${ALLOW_ACTIVE_SCAN:-0}"
CA_BUNDLE="${CA_BUNDLE:-}"

if [[ -z "$AGENT_TOKEN" ]]; then
  echo "Set AGENT_TOKEN environment variable before running."
  exit 2
fi

sudo mkdir -p /opt/ai-testing/kali-os-agent /etc/kali-os-agent "$WORKDIR"
sudo cp -f agents/kali_os_agent/agent.py /opt/ai-testing/kali-os-agent/agent.py
sudo chmod +x /opt/ai-testing/kali-os-agent/agent.py
if [[ ! -f "$TOOLS_FILE" ]]; then
  sudo mkdir -p "$(dirname "$TOOLS_FILE")"
  sudo cp -f agents/kali_os_agent/tools.yaml "$TOOLS_FILE"
fi

# Create env file
sudo tee /etc/kali-os-agent/config.env >/dev/null <<EOF
ORCH_URL=$ORCH_URL
TENANT_ID=$TENANT_ID
AGENT_TOKEN=$AGENT_TOKEN
AGENT_NAME=$AGENT_NAME
AGENT_WORKDIR=$WORKDIR
TOOLS_FILE=$TOOLS_FILE
ALLOW_ACTIVE_SCAN=$ALLOW_ACTIVE_SCAN
CA_BUNDLE=$CA_BUNDLE
EOF

# Create systemd unit
sudo tee /etc/systemd/system/${UNIT_NAME}.service >/dev/null <<'UNIT'
[Unit]
Description=AI-Testing Kali OS Agent
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
EnvironmentFile=/etc/kali-os-agent/config.env
ExecStart=/usr/bin/env bash -lc '/usr/bin/python3 /opt/ai-testing/kali-os-agent/agent.py'
Restart=always
RestartSec=3
WorkingDirectory=/opt/ai-testing/kali-os-agent
# Hardening (adjust if needed)
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=full

[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable ${UNIT_NAME}.service
sudo systemctl restart ${UNIT_NAME}.service

echo "Kali OS Agent installed and started. Journal: sudo journalctl -u ${UNIT_NAME} -f"
