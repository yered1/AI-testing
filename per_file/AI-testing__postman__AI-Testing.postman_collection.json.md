# File: AI-testing/postman/AI-Testing.postman_collection.json

- Size: 3652 bytes
- Kind: text
- SHA256: 51e4127cc38f474b35d234c7eb8750d2da9cb50da10139bbf5d6e425ef04c4ee

## Head (first 60 lines)

```
{
  "info": {
    "name": "AI Testing Platform",
    "_postman_id": "f3f2d7fa-7f5d-4d30-b60c-9d2e0e6fbd77",
    "description": "Collection for orchestrator v2 endpoints with DEV headers.",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Health",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "{{baseUrl}}/health",
          "host": [
            "{{baseUrl}}"
          ],
          "path": [
            "health"
          ]
        }
      }
    },
    {
      "name": "Catalog",
      "request": {
        "method": "GET",
        "header": [
          {
            "key": "X-Dev-User",
            "value": "{{devUser}}"
          },
          {
            "key": "X-Dev-Email",
            "value": "{{devEmail}}"
          },
          {
            "key": "X-Tenant-Id",
            "value": "{{tenantId}}"
          }
        ],
        "url": {
          "raw": "{{baseUrl}}/v1/catalog",
          "host": [
            "{{baseUrl}}"
          ],
          "path": [
            "v1",
            "catalog"
          ]
        }
      }
    },
    {
      "name": "Create engagement",
      "request": {
        "method": "POST",
        "header": [
          {
```

## Tail (last 60 lines)

```
          {
            "key": "Content-Type",
            "value": "application/json"
          },
          {
            "key": "X-Dev-User",
            "value": "{{devUser}}"
          },
          {
            "key": "X-Dev-Email",
            "value": "{{devEmail}}"
          },
          {
            "key": "X-Tenant-Id",
            "value": "{{tenantId}}"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\"selected_tests\":[{\"id\":\"network.discovery.ping_sweep\"},{\"id\":\"network.nmap.tcp_top_1000\"}],\"agents\":{\"strategy\":\"recommended\"},\"risk_tier\":\"safe_active\"}"
        },
        "url": {
          "raw": "{{baseUrl}}/v2/engagements/{{engagementId}}/plan/validate",
          "host": [
            "{{baseUrl}}"
          ],
          "path": [
            "v2",
            "engagements",
            "{{engagementId}}",
            "plan",
            "validate"
          ]
        }
      }
    }
  ],
  "variable": [
    {
      "key": "baseUrl",
      "value": "http://localhost:8080"
    },
    {
      "key": "devUser",
      "value": "yered"
    },
    {
      "key": "devEmail",
      "value": "yered@example.com"
    },
    {
      "key": "tenantId",
      "value": "t_demo"
    },
    {
      "key": "engagementId",
      "value": "eng_xxxxxxxx"
    }
  ]
}
```

