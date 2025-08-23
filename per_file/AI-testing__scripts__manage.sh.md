# File: AI-testing/scripts/manage.sh

- Size: 723 bytes
- Kind: text
- SHA256: 9f9228c2f65956eb6c46ff74667a520ad8b0c0a5bdbe437abdecad2e70bcfb00

## Head (first 60 lines)

```
#!/bin/bash
# AI-Testing Platform Management

set -e

COMMAND=${1:-help}

case "$COMMAND" in
    up)
        echo "Starting platform..."
        docker-compose up -d
        echo "Platform running at http://localhost:8080"
        ;;
    
    down)
        echo "Stopping platform..."
        docker-compose down
        ;;
    
    logs)
        docker-compose logs -f
        ;;
    
    reset)
        docker-compose down -v
        docker-compose up -d
        ;;
    
    test)
        curl -s http://localhost:8080/health | python3 -m json.tool
        ;;
    
    help)
        echo "Usage: $0 [up|down|logs|reset|test]"
        ;;
    
    *)
        echo "Unknown command: $COMMAND"
        exit 1
        ;;
esac
```

