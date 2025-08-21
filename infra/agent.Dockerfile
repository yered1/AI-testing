FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir requests==2.32.3
COPY agents/kali_gateway /app/agent
CMD ["python","/app/agent/agent.py"]
