FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends ssh && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY orchestrator/agent_sdk /app/orchestrator/agent_sdk
COPY agents/kali_remote_agent /app/agent
RUN pip install --no-cache-dir paramiko==3.4.0 requests==2.32.3 pyyaml==6.0.2
ENV PYTHONPATH=/app
CMD ["python","/app/agent/agent.py"]
