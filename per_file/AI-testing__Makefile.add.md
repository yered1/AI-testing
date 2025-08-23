# File: AI-testing/Makefile.add

- Size: 161 bytes
- Kind: text
- SHA256: ba8d122cfcd49b3427397fa6c2e0f0a52751a218ed9c462b7bbf5b6dc5695ecc

## Head (first 60 lines)

```
agent-up:
	docker compose -f infra/docker-compose.v2.yml up --build -d agent_dev1

agent-logs:
	docker compose -f infra/docker-compose.v2.yml logs -f agent_dev1
```

