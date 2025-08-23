# AI-Testing Platform

Automated security testing platform with multiple scanning agents.

## Features

- Web application scanning (ZAP)
- Vulnerability detection (Nuclei)  
- Static code analysis (Semgrep)
- Network scanning (Nmap)
- Centralized orchestration
- Real-time progress tracking

## Quick Start

```bash
# Setup
cp .env.example .env
# Edit .env with your settings

# Start platform
./scripts/manage.sh up

# Check health
./scripts/manage.sh test

# View logs
./scripts/manage.sh logs
```

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Browser   │────▶│ Orchestrator │────▶│   Agents    │
└─────────────┘     └──────────────┘     └─────────────┘
                           │                     │
                           ▼                     ▼
                    ┌──────────────┐     ┌─────────────┐
                    │   Database   │     │   Results   │
                    └──────────────┘     └─────────────┘
```

## API Documentation

Access interactive API docs at http://localhost:8080/docs

## Development

```bash
# Run tests
pytest tests/

# Format code
black orchestrator/

# Type check
mypy orchestrator/
```

## License

MIT
