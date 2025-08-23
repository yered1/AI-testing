# File: AI-testing/orchestrator/pyproject.toml

- Size: 770 bytes
- Kind: text
- SHA256: 62fea091b6bfb8024f51e3addaa6fcfd2b18371860cd36aa86ca852d6aa19531

## Head (first 60 lines)

```
[tool.poetry]
name = "ai-testing-orchestrator"
version = "0.8.1"
description = "AI testing orchestrator (v0.8.1 — complete API + agents + reports)"
authors = ["You <you@example.com>"]
readme = "README.md"
packages = [{include = "orchestrator"}]

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "0.111.0"
uvicorn = {extras = ["standard"], version = "0.30.1"}
pydantic = "2.8.2"
pydantic-settings = "2.3.4"
python-multipart = "0.0.9"
sqlalchemy = "2.0.31"
psycopg = {version = "3.1.19", extras = ["binary"]}
alembic = "1.13.2"
authlib = "1.3.1"
python-jose = {extras=["cryptography"], version="3.3.0"}
httpx = "0.27.0"
jinja2 = "3.1.4"
sse-starlette = "2.1.3"

[tool.poetry.group.dev.dependencies]
pytest = "^8.2.0"
pytest-asyncio = "^0.24.0"
requests = "^2.32.3"
```

