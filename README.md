# AI-Testing Platform

A comprehensive security testing orchestration platform that automates various security testing methodologies including web application testing, network scanning, code analysis, and mobile application testing.

## Features

- **Multi-Agent Architecture**: Distributed testing agents for various security tools
- **AI-Powered Planning**: Intelligent test plan generation and risk assessment
- **Comprehensive Testing**: Web, network, code, mobile, and infrastructure testing
- **RBAC & Multi-tenancy**: Enterprise-ready access control
- **Real-time Reporting**: Live test execution monitoring and comprehensive reports

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.9+
- 8GB RAM minimum
- Linux or macOS

### Installation

```bash
# Clone repository
git clone https://github.com/yered1/AI-testing.git
cd AI-testing

# Setup environment
cp config/default.env .env
# Edit .env with your configuration

# Start platform
./scripts/manage.sh full-start

# Access the platform
open http://localhost:8080/ui
```

### Basic Usage

```bash
# Service management
./scripts/manage.sh up          # Start services
./scripts/manage.sh down        # Stop services
./scripts/manage.sh logs        # View logs
./scripts/manage.sh status      # Check status

# Testing
./scripts/manage.sh test        # Run smoke tests

# Agent management
./scripts/manage.sh agent-token my-agent  # Generate agent token
```

## Architecture

The platform consists of:
- **Orchestrator**: Core API service managing test execution
- **Agents**: Distributed testing agents (ZAP, Nuclei, Semgrep, Nmap, etc.)
- **UI**: Web interface for test management
- **Brain**: AI-powered test planning and analysis
- **OPA**: Policy engine for access control

## API Documentation

### Authentication
```bash
curl -X POST http://localhost:8080/v2/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'
```

### Core Endpoints
- `POST /v2/engagements` - Create engagement
- `POST /v2/engagements/{id}/plan` - Create test plan
- `POST /v2/plans/{id}/run` - Start test run
- `GET /v2/reports/run/{id}` - Get report

## Development

### Running Tests
```bash
# Unit tests
pytest tests/unit

# Integration tests
pytest tests/integration

# Smoke tests
./scripts/manage.sh test
```

### Adding New Agents
See [docs/AGENTS.md](docs/AGENTS.md) for agent development guide.

## Deployment

### Docker Compose (Development)
```bash
docker compose -f infra/docker-compose.yml up -d
```

### Kubernetes (Production)
```bash
kubectl apply -f infra/kubernetes/
```

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed deployment instructions.

## Security

⚠️ **Important Security Notes**:
- Never enable `ALLOW_ACTIVE_SCAN` without proper authorization
- Rotate agent tokens regularly
- Use TLS in production
- Review [docs/SECURITY.md](docs/SECURITY.md) before deployment

## Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## License

[Your License]

## Support

- Issues: https://github.com/yered1/AI-testing/issues
- Documentation: [docs/](docs/)
