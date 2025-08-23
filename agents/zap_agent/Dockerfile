# ============================================
# agents/zap_agent/Dockerfile
"""Dockerfile for ZAP agent"""

dockerfile_content = """FROM owasp/zap2docker-stable:latest

# Install Python requirements
USER root
RUN apt-get update && apt-get install -y \\
    python3-pip \\
    && rm -rf /var/lib/apt/lists/*

# Create agent directory
WORKDIR /zap/agent

# Copy agent code
COPY agent.py .
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Switch back to ZAP user
USER zap

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV ORCHESTRATOR_URL=http://orchestrator:8080

# Run agent
CMD ["python3", "agent.py"]
"""