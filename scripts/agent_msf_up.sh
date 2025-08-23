#!/bin/bash
# Start Metasploit Agent

set -e

# Check if token is provided
if [ -z "$AGENT_TOKEN" ]; then
    echo "Error: AGENT_TOKEN not set"
    echo "Usage: AGENT_TOKEN=<token> bash $0"
    exit 1
fi

# Safety check
if [ "$ALLOW_EXPLOITATION" == "1" ]; then
    echo "⚠️  WARNING: Exploitation is ENABLED!"
    echo "This agent will attempt to exploit vulnerabilities."
    echo "Only use with proper authorization!"
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "Running in SAFE MODE (no actual exploitation)"
fi

# Export for docker-compose
export MSF_AGENT_TOKEN="$AGENT_TOKEN"

# Start MSF and agent
echo "Starting Metasploit Framework and Agent..."
docker compose -f infra/docker-compose.agents.enhanced.yml up -d msf msf_agent

echo "Waiting for MSF to initialize..."
sleep 10

echo "MSF Agent started. Tailing logs..."
docker compose -f infra/docker-compose.agents.enhanced.yml logs -f msf_agent
