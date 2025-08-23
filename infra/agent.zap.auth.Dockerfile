FROM owasp/zap2docker-stable
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*
RUN pip3 install --no-cache-dir requests==2.32.3 python-owasp-zap-v2.4==0.0.21
WORKDIR /app
COPY agents/zap_auth_agent /app/agent
CMD ["python3","/app/agent/agent.py"]
