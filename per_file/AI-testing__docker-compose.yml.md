# File: AI-testing/docker-compose.yml

- Size: 1548 bytes
- Kind: text
- SHA256: 172fb96ef4a456f935f954026836be7724cfd9dfe21f2405c4c46dd187f2317f

## Head (first 60 lines)

```
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${DB_NAME:-ai_testing}
      POSTGRES_USER: ${DB_USER:-postgres}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-postgres}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - ai_testing

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - ai_testing

  orchestrator:
    build:
      context: ./orchestrator
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://${DB_USER:-postgres}:${DB_PASSWORD:-postgres}@db:5432/${DB_NAME:-ai_testing}
      REDIS_URL: redis://redis:6379
      SECRET_KEY: ${SECRET_KEY:-change-me-in-production}
      ALLOW_ACTIVE_SCAN: ${ALLOW_ACTIVE_SCAN:-0}
      EVIDENCE_DIR: /evidence
    volumes:
      - ./orchestrator:/app
      - evidence_data:/evidence
    depends_on:
      - db
      - redis
    ports:
      - "8080:8080"
    networks:
      - ai_testing

  opa:
    image: openpolicyagent/opa:0.65.0
    command: ["run", "--server", "--addr", ":8181", "/policies"]
    volumes:
      - ./policies:/policies:ro
    networks:
      - ai_testing
```

## Tail (last 60 lines)

```
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - ai_testing

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - ai_testing

  orchestrator:
    build:
      context: ./orchestrator
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://${DB_USER:-postgres}:${DB_PASSWORD:-postgres}@db:5432/${DB_NAME:-ai_testing}
      REDIS_URL: redis://redis:6379
      SECRET_KEY: ${SECRET_KEY:-change-me-in-production}
      ALLOW_ACTIVE_SCAN: ${ALLOW_ACTIVE_SCAN:-0}
      EVIDENCE_DIR: /evidence
    volumes:
      - ./orchestrator:/app
      - evidence_data:/evidence
    depends_on:
      - db
      - redis
    ports:
      - "8080:8080"
    networks:
      - ai_testing

  opa:
    image: openpolicyagent/opa:0.65.0
    command: ["run", "--server", "--addr", ":8181", "/policies"]
    volumes:
      - ./policies:/policies:ro
    networks:
      - ai_testing

volumes:
  postgres_data:
  redis_data:
  evidence_data:

networks:
  ai_testing:
    driver: bridge
```

