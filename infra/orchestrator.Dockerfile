FROM python:3.11-slim
WORKDIR /app
COPY orchestrator/requirements.txt /app/orchestrator/requirements.txt
RUN pip install --no-cache-dir -r /app/orchestrator/requirements.txt
COPY orchestrator /app/orchestrator
COPY schemas /app/schemas
COPY catalog /app/catalog
EXPOSE 8080
WORKDIR /app/orchestrator
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
