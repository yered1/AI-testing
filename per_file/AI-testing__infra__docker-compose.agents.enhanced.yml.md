# File: AI-testing/infra/docker-compose.agents.enhanced.yml

- Size: 1666 bytes
- Kind: text
- SHA256: 4bfc8257f4869122212a2cb38b7bdea5b054bfef988aea45def7de1373291540

## Head (first 60 lines)

```
version: '3.8'

services:
  aws_agent:
    build:
      context: ..
      dockerfile: infra/agent.aws.Dockerfile
    environment:
      ORCHESTRATOR_URL: ${ORCHESTRATOR_URL:-http://orchestrator:8080}
      AGENT_TOKEN: ${AWS_AGENT_TOKEN}
      TENANT_ID: ${TENANT_ID:-t_demo}
      ALLOW_ACTIVE_SCAN: ${ALLOW_ACTIVE_SCAN:-0}
      # AWS credentials - set these securely
      AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
      AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}
      AWS_DEFAULT_REGION: ${AWS_DEFAULT_REGION:-us-east-1}
    networks:
      - ai-testing-net
    restart: unless-stopped

  msf_agent:
    build:
      context: ..
      dockerfile: infra/agent.msf.Dockerfile
    environment:
      ORCHESTRATOR_URL: ${ORCHESTRATOR_URL:-http://orchestrator:8080}
      AGENT_TOKEN: ${MSF_AGENT_TOKEN}
      TENANT_ID: ${TENANT_ID:-t_demo}
      ALLOW_EXPLOITATION: ${ALLOW_EXPLOITATION:-0}
      SAFE_MODE: ${SAFE_MODE:-1}
      MSF_HOST: ${MSF_HOST:-msf}
      MSF_PORT: ${MSF_PORT:-55553}
      MSF_USER: ${MSF_USER:-msf}
      MSF_PASS: ${MSF_PASS:-msf}
      LHOST: ${LHOST:-0.0.0.0}
    networks:
      - ai-testing-net
    depends_on:
      - msf
    restart: unless-stopped

  msf:
    image: metasploitframework/metasploit-framework:latest
    environment:
      MSF_DATABASE_CONFIG: /usr/src/metasploit-framework/config/database.yml
    command: >
      sh -c "msfdb init &&
             msfrpcd -P ${MSF_PASS:-msf} -S -f -a 0.0.0.0 -p 55553"
    networks:
      - ai-testing-net
    volumes:
      - msf_data:/root/.msf4
    restart: unless-stopped

networks:
  ai-testing-net:
    external: true
    name: infra_ai-testing-net

volumes:
```

## Tail (last 60 lines)

```

services:
  aws_agent:
    build:
      context: ..
      dockerfile: infra/agent.aws.Dockerfile
    environment:
      ORCHESTRATOR_URL: ${ORCHESTRATOR_URL:-http://orchestrator:8080}
      AGENT_TOKEN: ${AWS_AGENT_TOKEN}
      TENANT_ID: ${TENANT_ID:-t_demo}
      ALLOW_ACTIVE_SCAN: ${ALLOW_ACTIVE_SCAN:-0}
      # AWS credentials - set these securely
      AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
      AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}
      AWS_DEFAULT_REGION: ${AWS_DEFAULT_REGION:-us-east-1}
    networks:
      - ai-testing-net
    restart: unless-stopped

  msf_agent:
    build:
      context: ..
      dockerfile: infra/agent.msf.Dockerfile
    environment:
      ORCHESTRATOR_URL: ${ORCHESTRATOR_URL:-http://orchestrator:8080}
      AGENT_TOKEN: ${MSF_AGENT_TOKEN}
      TENANT_ID: ${TENANT_ID:-t_demo}
      ALLOW_EXPLOITATION: ${ALLOW_EXPLOITATION:-0}
      SAFE_MODE: ${SAFE_MODE:-1}
      MSF_HOST: ${MSF_HOST:-msf}
      MSF_PORT: ${MSF_PORT:-55553}
      MSF_USER: ${MSF_USER:-msf}
      MSF_PASS: ${MSF_PASS:-msf}
      LHOST: ${LHOST:-0.0.0.0}
    networks:
      - ai-testing-net
    depends_on:
      - msf
    restart: unless-stopped

  msf:
    image: metasploitframework/metasploit-framework:latest
    environment:
      MSF_DATABASE_CONFIG: /usr/src/metasploit-framework/config/database.yml
    command: >
      sh -c "msfdb init &&
             msfrpcd -P ${MSF_PASS:-msf} -S -f -a 0.0.0.0 -p 55553"
    networks:
      - ai-testing-net
    volumes:
      - msf_data:/root/.msf4
    restart: unless-stopped

networks:
  ai-testing-net:
    external: true
    name: infra_ai-testing-net

volumes:
  msf_data:
```

