# AI-Testing Platform

## Overview
AI-Testing is a comprehensive security testing orchestration platform that automates various security testing methodologies including web application testing, network scanning, code analysis, and mobile application testing.

## Architecture
The platform consists of:
- **Orchestrator**: Core API service managing test execution
- **Agents**: Distributed testing agents for various security tools
- **UI**: Web interface for test management
- **Brain**: AI-powered test planning and analysis

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.9+
- Node.js 16+ (for UI development)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yered1/AI-testing.git
cd AI-testing
```

2. Set up environment:
```bash
cp orchestrator/.env.example orchestrator/.env
# Edit .env with your configuration
```

3. Start the platform:
```bash
docker compose -f infra/docker-compose.yml up -d
```

4. Run migrations:
```bash
docker compose exec orchestrator alembic upgrade head
```

5. Access the UI:
```
http://localhost:8080/ui
```

## Features

### Core Capabilities
- **Web Application Testing**: ZAP, Nuclei integration
- **Network Scanning**: Nmap, DNS discovery
- **Code Analysis**: Semgrep, static analysis
- **Mobile Testing**: APK analysis
- **Kali Integration**: Remote Kali Linux tool execution

### Security Features
- RBAC with OAuth2/OIDC support
- Multi-tenancy
- Audit logging
- Artifact encryption

### AI Features
- Automated test planning
- Risk assessment
- Finding enrichment
- Report generation

## API Documentation

### Authentication
```bash
# Get auth token
curl -X POST http://localhost:8080/v2/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'
```

### Core Endpoints

#### Engagements
- `POST /v2/engagements` - Create engagement
- `GET /v2/engagements/{id}` - Get engagement
- `POST /v2/engagements/{id}/plan` - Create test plan
- `POST /v2/engagements/{id}/run` - Start test run

#### Agents
- `POST /v2/agent_tokens` - Create agent token
- `GET /v2/agents/lease` - Lease jobs for agent
- `POST /v2/jobs/{id}/complete` - Complete job

#### Reports
- `GET /v2/reports/run/{id}` - Get run report
- `GET /v2/reports/run/{id}.zip` - Download report bundle

## Agent Development

### Creating a Custom Agent

1. Extend the base agent class:
```python
from agent_sdk import BaseAgent

class CustomAgent(BaseAgent):
    def process_job(self, job):
        # Implementation
        pass
```

2. Register with orchestrator:
```python
agent = CustomAgent(
    orchestrator_url="http://localhost:8080",
    token="your-agent-token"
)
agent.start()
```

## Configuration

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: Application secret key
- `ALLOW_ACTIVE_SCAN`: Enable intrusive scanning (default: false)
- `EVIDENCE_DIR`: Artifact storage directory

### Docker Compose Profiles
- `default`: Core services only
- `full`: All services including agents
- `dev`: Development environment with hot reload

## Security Considerations

⚠️ **Important Security Notes**:
- Never enable `ALLOW_ACTIVE_SCAN` without proper authorization
- Rotate agent tokens regularly
- Use TLS in production
- Implement network segmentation for agents
- Review OPA policies before deployment

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License
[Your License Here]

## Support
- Issues: https://github.com/yered1/AI-testing/issues
- Documentation: https://docs.ai-testing.io
