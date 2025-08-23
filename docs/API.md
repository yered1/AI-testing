# API Documentation

## Base URL
```
http://localhost:8080
```

## Authentication
Most endpoints require authentication headers:
```
X-Dev-User: username
X-Dev-Email: user@example.com
X-Tenant-Id: tenant_id
```

## Core Endpoints

### Health Check
```http
GET /health
```

### Get Catalog
```http
GET /v2/catalog
```

### Create Engagement
```http
POST /v2/engagements
Content-Type: application/json

{
  "name": "Test Engagement",
  "type": "web_application",
  "scope": {
    "targets": ["http://example.com"],
    "excluded": []
  }
}
```

### Create Plan
```http
POST /v2/engagements/{engagement_id}/plan
Content-Type: application/json

{
  "tests": [
    {
      "id": "web_basic",
      "params": {}
    }
  ]
}
```

### Start Run
```http
POST /v2/plans/{plan_id}/run
```

### Get Run Status
```http
GET /v2/runs/{run_id}
```

### Get Report
```http
GET /v2/reports/run/{run_id}
```

## Agent Endpoints

### Generate Agent Token
```http
POST /v2/agent_tokens
Content-Type: application/json

{
  "tenant_id": "t_default",
  "name": "agent-name"
}
```

### Lease Job (Agent)
```http
POST /v2/agents/lease
Authorization: Bearer {agent_token}

{
  "agent_type": "zap"
}
```
