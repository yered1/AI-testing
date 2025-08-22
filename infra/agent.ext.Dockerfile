FROM python:3.11-slim
RUN apt-get update && apt-get install -y nmap && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN pip install --no-cache-dir requests==2.32.3
COPY agents/dev_agent_ext /app/agent
CMD ["python","/app/agent/agent.py"]
