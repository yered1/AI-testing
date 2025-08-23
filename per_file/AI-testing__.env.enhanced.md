# File: AI-testing/.env.enhanced

- Size: 1157 bytes
- Kind: text
- SHA256: 84257767473c1e4219f9f5e7dd4c049e34f4f7b4708edaef4f80f24be59a1107

## Head (first 60 lines)

```
# Enhanced AI Pentest Platform Configuration

# Core Settings
ORCHESTRATOR_URL=http://localhost:8080
TENANT_ID=t_demo
EVIDENCE_DIR=/evidence
SIMULATE_PROGRESS=false

# AI Brain Providers
# OpenAI
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE_URL=https://api.openai.com/v1

# Anthropic
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-3-5-sonnet-20240620

# Azure OpenAI
AZURE_OPENAI_KEY=
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_DEPLOYMENT=

# AWS Agent Configuration
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_DEFAULT_REGION=us-east-1
# Or use AWS_PROFILE=default

# Metasploit Agent Configuration
ALLOW_EXPLOITATION=0  # Set to 1 to enable actual exploitation (DANGEROUS!)
SAFE_MODE=1          # Set to 0 to disable safety checks
MSF_HOST=msf
MSF_PORT=55553
MSF_USER=msf
MSF_PASS=msf
LHOST=0.0.0.0

# Security Settings
ALLOW_ACTIVE_SCAN=0  # Set to 1 for intrusive scans
REQUIRE_APPROVAL=true
MAX_CONCURRENT_JOBS=5

# Notification Settings
SLACK_WEBHOOK_URL=
EMAIL_NOTIFICATIONS=false

# Database
DATABASE_URL=postgresql://pentest:pentest@db:5432/pentest
REDIS_URL=redis://redis:6379

# Auth (if using OIDC)
OIDC_ISSUER=
OIDC_CLIENT_ID=
OIDC_CLIENT_SECRET=
```

