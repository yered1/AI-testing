FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir requests==2.32.3
COPY agents/dev_agent /app/agent
ENV PYTHONUNBUFFERED=1
CMD ["python","/app/agent/agent.py"]
