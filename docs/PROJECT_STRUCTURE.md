# AI-Testing Platform - Project Structure

## Directory Layout

```
ai-testing/
├── orchestrator/          # Core orchestration service
│   ├── app.py            # Main application
│   ├── models/           # Database models
│   ├── routers/          # API endpoints
│   ├── services/         # Business logic
│   ├── agent_sdk/        # Agent SDK
│   └── alembic/          # Database migrations
│
├── agents/               # Security testing agents
│   ├── zap_agent/        # OWASP ZAP agent
│   ├── nuclei_agent/     # Nuclei scanner
│   ├── semgrep_agent/    # Code analysis
│   ├── nmap_agent/       # Network scanner
│   ├── mobile_apk_agent/ # Mobile testing
│   └── kali_agent/       # Kali tools integration
│
├── ui/                   # Web interface
│   ├── src/              # Source code
│   ├── public/           # Static assets
│   └── package.json      # Dependencies
│
├── infra/                # Infrastructure
│   ├── docker-compose.yml # Main compose file
│   ├── kubernetes/       # K8s manifests
│   └── terraform/        # IaC definitions
│
├── policies/             # OPA policies
│   └── rbac.rego        # RBAC rules
│
├── scripts/              # Utility scripts
│   ├── manage.sh        # Main management script
│   ├── setup/           # Installation scripts
│   ├── maintenance/     # Cleanup & maintenance
│   ├── testing/         # Test scripts
│   ├── agents/          # Agent-specific scripts
│   └── deployment/      # Deployment scripts
│
├── tests/                # Test suites
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── e2e/             # End-to-end tests
│
├── docs/                 # Documentation
│   ├── API.md           # API documentation
│   ├── AGENTS.md        # Agent development guide
│   ├── DEPLOYMENT.md    # Deployment guide
│   └── SECURITY.md      # Security guidelines
│
├── config/               # Configuration files
│   ├── default.env      # Default environment
│   ├── staging.env      # Staging environment
│   └── production.env   # Production environment
│
└── templates/            # Report templates
    ├── html/
    ├── pdf/
    └── markdown/
```

## Key Files

- `scripts/manage.sh` - Central management script
- `.env` - Environment configuration
- `docker-compose.yml` - Service definitions
- `README.md` - Main documentation

## Quick Start

1. Copy environment file: `cp config/default.env .env`
2. Start services: `./scripts/manage.sh up`
3. Run migrations: `./scripts/manage.sh migrate`
4. Access UI: http://localhost:8080/ui
