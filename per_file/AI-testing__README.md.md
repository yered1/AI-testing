# File: AI-testing/README.md

- Size: 1547 bytes
- Kind: text
- SHA256: f7b947ecfcedffe67f02b23c87bd67312884ec9e8cc4178f82bea503259792e2

## Head (first 60 lines)

```
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

```

## Tail (last 60 lines)

```

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
```

