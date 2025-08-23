# Extends previously built orchestrator image to include pg client driver for Alembic/SQLAlchemy
FROM infra-orchestrator:latest
RUN pip install --no-cache-dir psycopg2-binary==2.9.9
