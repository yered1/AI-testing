FROM python:3.11-slim
RUN pip install --no-cache-dir poetry==1.8.3
WORKDIR /app
COPY orchestrator/pyproject.toml orchestrator/poetry.lock* /app/orchestrator/
RUN cd /app/orchestrator && poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi
COPY orchestrator /app/orchestrator
COPY catalog /app/catalog
COPY schemas /app/schemas
COPY policies /app/policies
EXPOSE 8080
WORKDIR /app/orchestrator
CMD ["uvicorn", "app_v2:app", "--host", "0.0.0.0", "--port", "8080"]
