# File: AI-testing/infra/docker-compose.v2.yml

- Size: 2131 bytes
- Kind: text
- SHA256: e5ad5e39c44824c244feed51f333706ee7e1285f1d9a6590fc8d487b43f393ad

## Head (first 60 lines)

```
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: pentest
      POSTGRES_PASSWORD: pentest
      POSTGRES_DB: pentest
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    ports:
      - "5432:5432"
    networks:
      - ai-testing-net
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U pentest"]
      interval: 10s
      timeout: 5s
      retries: 5

  opa:
    image: ${OPA_IMAGE:-openpolicyagent/opa:0.65.0}
    command:
      - "run"
      - "--server"
      - "--addr=0.0.0.0:8181"
      - "/policies"
    volumes:
      - ../policies:/policies:ro
    ports:
      - "8181:8181"
    networks:
      - ai-testing-net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8181/health"]
      interval: 10s
      timeout: 5s
      retries: 5

  orchestrator:
    build:
      context: ..
      dockerfile: infra/orchestrator.Dockerfile
    environment:
      DATABASE_URL: postgresql://pentest:pentest@db:5432/pentest
      OPA_URL: http://opa:8181
      REDIS_URL: redis://redis:6379
      SIMULATE_PROGRESS: ${SIMULATE_PROGRESS:-false}
      EVIDENCE_DIR: /evidence
      SLACK_WEBHOOK_URL: ${SLACK_WEBHOOK_URL:-}
      OPENAI_API_KEY: ${OPENAI_API_KEY:-}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:-}
      PYTHONUNBUFFERED: 1
    volumes:
      - ../orchestrator:/app
      - evidence_data:/evidence
    ports:
      - "8080:8080"
```

## Tail (last 60 lines)

```
      - ai-testing-net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8181/health"]
      interval: 10s
      timeout: 5s
      retries: 5

  orchestrator:
    build:
      context: ..
      dockerfile: infra/orchestrator.Dockerfile
    environment:
      DATABASE_URL: postgresql://pentest:pentest@db:5432/pentest
      OPA_URL: http://opa:8181
      REDIS_URL: redis://redis:6379
      SIMULATE_PROGRESS: ${SIMULATE_PROGRESS:-false}
      EVIDENCE_DIR: /evidence
      SLACK_WEBHOOK_URL: ${SLACK_WEBHOOK_URL:-}
      OPENAI_API_KEY: ${OPENAI_API_KEY:-}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:-}
      PYTHONUNBUFFERED: 1
    volumes:
      - ../orchestrator:/app
      - evidence_data:/evidence
    ports:
      - "8080:8080"
    networks:
      - ai-testing-net
    depends_on:
      db:
        condition: service_healthy
      opa:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 10s
      timeout: 5s
      retries: 10
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - ai-testing-net
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

networks:
  ai-testing-net:
    driver: bridge
    name: infra_ai-testing-net

volumes:
  postgres_data:
  evidence_data:
```

