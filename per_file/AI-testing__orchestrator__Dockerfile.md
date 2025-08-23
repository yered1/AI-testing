# File: AI-testing/orchestrator/Dockerfile

- Size: 423 bytes
- Kind: text
- SHA256: 38d7e19e27dfb7df4cff2b866bf74cf2a33940f7e783e610b6e1fdb21a20d25a

## Head (first 60 lines)

```
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create evidence directory
RUN mkdir -p /evidence

EXPOSE 8080

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
```

