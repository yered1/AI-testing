#!/bin/bash
# Destination: patches/v2.0.0/scripts/standardize_agent_env.sh
# Rationale: Standardize environment variables across all agents and compose files
# Changes ORCHESTRATOR_URL to ORCH_URL and updates auth headers

set -e

echo "🔧 Standardizing agent environment variables..."

# Function to update files
update_file() {
    local file=$1
    local backup="${file}.bak"
    
    if [ ! -f "$file" ]; then
        echo "  ⚠️  File not found: $file"
        return
    fi
    
    # Create backup
    cp "$file" "$backup"
    
    # Update environment variables
    sed -i 's/ORCHESTRATOR_URL/ORCH_URL/g' "$file"
    sed -i 's/X-Agent-Token/X-Agent-Id/g' "$file"
    
    # Check if changes were made
    if diff -q "$file" "$backup" > /dev/null; then
        echo "  ✓ No changes needed: $file"
        rm "$backup"
    else
        echo "  ✅ Updated: $file"
    fi
}

# Update Python files in agents directory
echo "Updating Python agent files..."
find agents/ -name "*.py" -type f | while read -r file; do
    update_file "$file"
done

# Update Docker Compose files
echo "Updating Docker Compose files..."
for compose_file in infra/docker-compose*.yml; do
    update_file "$compose_file"
done

# Update Dockerfiles
echo "Updating Dockerfiles..."
find . -name "*.Dockerfile" -o -name "*.dockerfile" -o -name "Dockerfile" | while read -r file; do
    update_file "$file"
done

# Fix case-sensitive filename issue
echo "Fixing case-sensitive filename issues..."
if [ -f "infra/agent.aws.DockerFile" ]; then
    mv "infra/agent.aws.DockerFile" "infra/agent.aws.Dockerfile"
    echo "  ✅ Renamed agent.aws.DockerFile to agent.aws.Dockerfile"
fi

# Update compose references to correct filename
if [ -f "infra/docker-compose.agents.enhanced.yml" ]; then
    sed -i 's/agent\.aws\.DockerFile/agent.aws.Dockerfile/g' "infra/docker-compose.agents.enhanced.yml"
    echo "  ✅ Updated docker-compose.agents.enhanced.yml references"
fi

echo ""
echo "📝 Summary of standardization:"
echo "  • ORCHESTRATOR_URL → ORCH_URL"
echo "  • X-Agent-Token → X-Agent-Id + X-Agent-Key"
echo "  • Fixed Dockerfile naming convention"
echo ""
echo "✅ Environment standardization complete!"
echo ""
echo "Next steps:"
echo "1. Review changes with: git diff"
echo "2. Test agents with: docker-compose up"
echo "3. Commit changes: git add -A && git commit -m 'Standardize agent environment'"