# File: AI-testing/infra/agent.msf.dockerfile

- Size: 1095 bytes
- Kind: text
- SHA256: b11a106d9e595a18f1b3ad74cbbc54f1559a74cccd111abfb4062d87109c5a30

## Head (first 60 lines)

```
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Create agent user
RUN useradd -m -s /bin/bash agent

# Set working directory
WORKDIR /app

# Copy requirements
COPY agents/msf_agent/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY orchestrator/agent_sdk /app/orchestrator/agent_sdk
COPY agents/msf_agent /app/agents/msf_agent

# Set permissions
RUN chown -R agent:agent /app

# Switch to non-root user
USER agent

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV ORCHESTRATOR_URL=http://orchestrator:8080
ENV AGENT_TOKEN=""
ENV TENANT_ID="t_demo"
ENV ALLOW_EXPLOITATION=0
ENV SAFE_MODE=1
ENV MSF_HOST=localhost
ENV MSF_PORT=55553
ENV MSF_USER=msf
ENV MSF_PASS=msf

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Run the agent
CMD ["python", "-u", "agents/msf_agent/agent.py"]
```

