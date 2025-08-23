FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create agent user
RUN useradd -m -s /bin/bash agent

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY agents/aws_agent/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install ScoutSuite
RUN pip install --no-cache-dir scoutsuite

# Copy agent code
COPY orchestrator/agent_sdk /app/orchestrator/agent_sdk
COPY agents/aws_agent /app/agents/aws_agent

# Set permissions
RUN chown -R agent:agent /app

# Switch to non-root user
USER agent

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV ORCHESTRATOR_URL=http://orchestrator:8080
ENV AGENT_TOKEN=""
ENV TENANT_ID="t_demo"
ENV ALLOW_ACTIVE_SCAN=0

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Run the agent
CMD ["python", "-u", "agents/aws_agent/agent.py"]