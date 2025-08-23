FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends unzip ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN pip install --no-cache-dir requests==2.32.3 androguard==4.1.1
COPY agents/mobile_apk_agent /app/agent
CMD ["python","/app/agent/agent.py"]
