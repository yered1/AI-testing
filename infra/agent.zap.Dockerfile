FROM owasp/zap2docker-stable
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*
RUN pip3 install --no-cache-dir requests==2.32.3
WORKDIR /app
COPY agents/zap_agent /app/agent
CMD ["python3","/app/agent/agent.py"]
