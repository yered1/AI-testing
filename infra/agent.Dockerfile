FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir requests
COPY agent/agent.py /app/agent.py
RUN chmod +x /app/agent.py
ENV ORCH_URL=http://orchestrator:8080 TENANT_ID=t_demo AGENT_TOKEN= AGENT_NAME= dev=true STATE_DIR=/data
VOLUME ["/data"]
CMD ["/app/agent.py"]
