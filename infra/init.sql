-- Initialize database for AI Pentest Platform

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Enable Row Level Security
ALTER DATABASE pentest SET row_security = on;

-- Create base tables if not exists (Alembic will handle the rest)
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Create default tenant
INSERT INTO tenants (id, name, created_at) 
VALUES ('t_demo', 'Demo Tenant', NOW())
ON CONFLICT (id) DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE pentest TO pentest;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO pentest;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO pentest;