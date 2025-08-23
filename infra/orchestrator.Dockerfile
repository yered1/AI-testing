FROM python:3.11-slim


# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    python3-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY orchestrator/requirements.txt /app/requirements.txt
COPY orchestrator/pyproject.toml /app/pyproject.toml 2>/dev/null || true

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    sqlalchemy==2.0.23 \
    alembic==1.12.1 \
    psycopg2-binary==2.9.9 \
    pydantic==2.5.0 \
    pydantic-settings==2.1.0 \
    python-multipart==0.0.6 \
    python-jose[cryptography]==3.3.0 \
    passlib[bcrypt]==1.7.4 \
    httpx==0.25.2 \
    redis==5.0.1 \
    sse-starlette==1.8.2 \
    jinja2==3.1.2 \
    aiofiles==23.2.1 \
    asyncpg==0.29.0 \
    pytest==7.4.3 \
    pytest-asyncio==0.21.1 \
    openai==1.3.8 \
    anthropic==0.7.8

# Copy orchestrator code
COPY orchestrator /app

# Create directories
RUN mkdir -p /app/alembic /app/catalog /app/routers /app/brain /evidence

# Create a simple health check endpoint if not exists
RUN echo 'from fastapi import FastAPI\napp = FastAPI()\n@app.get("/health")\nasync def health():\n    return {"status": "healthy"}' > /app/health_check.py || true

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]