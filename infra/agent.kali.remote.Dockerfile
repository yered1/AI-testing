FROM python:3.11-slim
RUN apt-get update && apt-get install -y openssh-client && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir requests==2.32.3 pyyaml==6.0.2
WORKDIR /app/agent
COPY agents/kali_remote_agent /app/agent
CMD ["python","agent.py"]
