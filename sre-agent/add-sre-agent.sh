#!/bin/bash
# Add SRE agent service to existing docker-compose.yml
# Usage: add-sre-agent.sh <input_dir> <project_name>

set -e

INPUT_DIR="$1"
PROJECT_NAME="$2"
TEMPLATE_DIR="$(dirname "$0")"

DOCKER_COMPOSE_FILE="$INPUT_DIR/docker-compose.yml"

# Check if docker-compose.yml exists
if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
    echo "⚠️  No docker-compose.yml found - SRE agent requires containerized services"
    echo "   Skipping SRE agent integration"
    exit 0
fi

# Check if SRE agent is already included
if grep -q "sre-agent:" "$DOCKER_COMPOSE_FILE"; then
    echo "✅ SRE agent already present in docker-compose.yml"
    exit 0
fi

# Check if this is a service (not a library) - include SRE agent for services
if grep -q -i "service\|api\|application" "$INPUT_DIR/prd.md" 2>/dev/null; then
    echo "📝 Service detected - adding SRE agent to docker-compose.yml"
else
    echo "📝 Library detected - skipping SRE agent integration"
    exit 0
fi

# Create SRE agent service block
SRE_AGENT_SERVICE="
  sre-agent:
    build:
      context: ./sre-agent
      dockerfile: runtime/Dockerfile
    ports:
      - \"8080:8080\"
    environment:
      # Vertex AI Configuration (uses Google Application Default Credentials)
      LLM_MODEL: \"google/gemini-2.0-flash\"
      LLM_API_BASE_URL: \"https://us-central1-aiplatform.googleapis.com/v1beta1/projects/alloydb-scann-experiment/locations/us-central1/endpoints/openapi\"
      # No LLM_API_KEY needed - uses Google credentials
      PAGERDUTY_API_TOKEN: \${PD_ACCESS_TOKEN}
      PAGERDUTY_ROUTING_KEY: \${PD_ROUTING_KEY:-}
      OPS_AUTH_TOKEN: \"demo-ops-token\"
      SERVICE_REGISTRY: \"${PROJECT_NAME}|http://app:8000|true\"
      SRE_PROMPT_PATH: \"/app/skill.md\"
      INCIDENTS_DIR: \"/app/incidents\"
      MAX_CONCURRENT_ALERTS: \"3\"
    volumes:
      # Mount Google credentials for Vertex AI authentication
      - ~/.config/gcloud/application_default_credentials.json:/app/gcloud-credentials.json:ro
    env_file:
      - .env
    depends_on:
      app:
        condition: service_started"

# Add SRE agent service before the volumes section
awk "
    /volumes:/ {
        print \"$SRE_AGENT_SERVICE\"
        print \"\"
        print \"volumes:\"
        next
    }
    { print }
" "$DOCKER_COMPOSE_FILE" > "$DOCKER_COMPOSE_FILE.tmp" && mv "$DOCKER_COMPOSE_FILE.tmp" "$DOCKER_COMPOSE_FILE"

echo "✅ Added SRE agent service to docker-compose.yml"

# Update .env.example with SRE agent variables
ENV_FILE="$INPUT_DIR/.env.example"
if [ -f "$ENV_FILE" ]; then
    if ! grep -q "PD_ACCESS_TOKEN" "$ENV_FILE"; then
        echo "" >> "$ENV_FILE"
        echo "# SRE Agent - PagerDuty Integration" >> "$ENV_FILE"
        echo "PD_ACCESS_TOKEN=your-pagerduty-api-token-here" >> "$ENV_FILE"
        echo "PD_ROUTING_KEY=your-pagerduty-routing-key-here" >> "$ENV_FILE"
        echo "✅ Added S agent variables to .env.example"
    fi
else
    echo "# SRE Agent - PagerDuty Integration" > "$ENV_FILE"
    echo "PD_ACCESS_TOKEN=your-pagerduty-api-token-here" >> "$ENV_FILE"
    echo "PD_ROUTING_KEY=your-pagerduty-routing-key-here" >> "$ENV_FILE"
    echo "✅ Created .env.example with SRE agent variables"
fi
