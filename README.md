# AI-Testing Platform

A comprehensive automated security testing orchestration platform that manages distributed security testing agents for web applications, APIs, mobile apps, and infrastructure.

## 🚀 Features

- **Multi-Agent Architecture**: Distributed testing with specialized agents (ZAP, Nuclei, Semgrep, Nmap, Kali tools)
- **AI-Powered Planning**: Intelligent test plan generation using OpenAI/Anthropic
- **Comprehensive Coverage**: Web, API, mobile, network, and code security testing
- **Enterprise Ready**: RBAC, multi-tenancy, audit logging
- **Real-time Monitoring**: Live test execution tracking and reporting

## 📋 Prerequisites

- Docker & Docker Compose v2
- Python 3.9+
- 8GB RAM minimum
- Linux/macOS (Windows WSL2 supported)

## 🔧 Quick Start

### 1. Clone and Setup
```bash
git clone https://github.com/yered1/AI-testing.git
cd AI-testing
cp .env.example .env
```

### 2. Configure Environment
Edit `.env` and set:
- `SECRET_KEY` - Generate a secure random string
- `DB_PASSWORD` - Change from default
- AI provider keys (optional): `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`

### 3. Start Platform
```bash
# Start all services and initialize
./scripts/manage.sh full-start

# Verify health
./scripts/manage.sh status
```

### 4. Access Platform
- API: http://localhost:8080
- UI: http://localhost:8080/ui
- Health: http://localhost:8080/health

## 📚 Documentation

- [Architecture Overview](docs/ARCHITECTURE.md)
- [API Documentation](docs/API.md)
- [Agent Development](docs/AGENTS.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Security Guidelines](docs/SECURITY.md)

## 🛠 Management Commands

```bash
# Service Management
./scripts/manage.sh up          # Start services
./scripts/manage.sh down        # Stop services
./scripts/manage.sh restart     # Restart services
./scripts/manage.sh logs        # View logs
./scripts/manage.sh status      # Check status

# Database
./scripts/manage.sh migrate     # Run migrations
./scripts/manage.sh db-shell    # PostgreSQL shell

# Testing
./scripts/manage.sh test        # Run tests
./scripts/manage.sh test-api    # Quick health check

# Agents
./scripts/manage.sh agent-token [name]  # Generate token

# Development
./scripts/manage.sh shell       # Orchestrator shell
./scripts/manage.sh clean       # Clean temp files
```

## 🧪 Running a Security Test

### Via API
```bash
# 1. Create engagement
curl -X POST http://localhost:8080/v2/engagements \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Scan",
    "type": "web_application",
    "scope": {"targets": ["http://example.com"]}
  }'

# 2. Create and run plan
# See API documentation for details
```

### Via UI
1. Navigate to http://localhost:8080/ui/builder
2. Create engagement
3. Select tests
4. Run and monitor

## 🤖 Available Agents

| Agent | Purpose | Status |
|-------|---------|--------|
| ZAP | Web app scanning | ✅ Ready |
| Nuclei | Vulnerability detection | ✅ Ready |
| Semgrep | Code analysis | ✅ Ready |
| Nmap | Network scanning | ✅ Ready |
| Mobile APK | Android analysis | ✅ Ready |
| Kali Remote | Advanced tools | ✅ Ready |

## 🏗 Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│     UI      │────▶│ Orchestrator │────▶│   Agents    │
└─────────────┘     └──────────────┘     └─────────────┘
                           │                     │
                           ▼                     ▼
                    ┌──────────────┐     ┌─────────────┐
                    │   Database   │     │   Reports   │
                    └──────────────┘     └─────────────┘
```

## 🔒 Security

⚠️ **Important Security Notes:**
- **NEVER** set `ALLOW_ACTIVE_SCAN=1` without proper authorization
- Use strong passwords and rotate tokens regularly
- Enable TLS in production
- Review security policies before deployment
- Implement network segmentation for agents

## 🐛 Troubleshooting

### Services won't start
```bash
# Check Docker
docker info
./scripts/manage.sh status

# Check ports
sudo lsof -i :8080
sudo lsof -i :5432
```

### Database issues
```bash
# Reset database (DELETES DATA)
./scripts/manage.sh full-reset
```

### View logs
```bash
./scripts/manage.sh logs orchestrator
./scripts/manage.sh logs db
```

## 📦 Development

### Project Structure
```
ai-testing/
├── orchestrator/     # Core API service
├── agents/          # Testing agents
├── ui/              # Web interface
├── infra/           # Infrastructure configs
├── scripts/         # Management scripts
├── policies/        # OPA policies
└── docs/           # Documentation
```

### Adding New Agents
See [Agent Development Guide](docs/AGENTS.md)

### Running Tests
```bash
pytest tests/unit
pytest tests/integration
./scripts/manage.sh test
```

## 🚢 Deployment

### Docker Compose (Development)
```bash
docker compose -f infra/docker-compose.yml up -d
```

### Kubernetes (Production)
```bash
kubectl apply -f infra/kubernetes/
```

### Cloud Deployment
- AWS: Use ECS or EKS
- GCP: Use Cloud Run or GKE
- Azure: Use Container Instances or AKS

See [Deployment Guide](docs/DEPLOYMENT.md) for details.

## 📄 License

[Specify your license]

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

## 📞 Support

- Issues: https://github.com/yered1/AI-testing/issues
- Documentation: [docs/](docs/)

---
Built with ❤️ for the security community
