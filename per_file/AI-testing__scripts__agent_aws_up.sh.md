# File: AI-testing/scripts/agent_aws_up.sh

- Size: 739 bytes
- Kind: text
- SHA256: 582bf262d4ab2b2ba4fd6420e821578a4cf95c1bf1ce10531b8fe355a1cdc422

## Head (first 60 lines)

```
#!/bin/bash
# Start AWS Security Agent

set -e

# Check if token is provided
if [ -z "$AGENT_TOKEN" ]; then
    echo "Error: AGENT_TOKEN not set"
    echo "Usage: AGENT_TOKEN=<token> bash $0"
    exit 1
fi

# Check AWS credentials
if [ -z "$AWS_ACCESS_KEY_ID" ] && [ -z "$AWS_PROFILE" ]; then
    echo "Warning: No AWS credentials configured"
    echo "Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY or AWS_PROFILE"
fi

# Export for docker-compose
export AWS_AGENT_TOKEN="$AGENT_TOKEN"

# Start the agent
echo "Starting AWS Security Agent..."
docker compose -f infra/docker-compose.agents.enhanced.yml up -d aws_agent

echo "AWS Agent started. Tailing logs..."
docker compose -f infra/docker-compose.agents.enhanced.yml logs -f aws_agent
```

