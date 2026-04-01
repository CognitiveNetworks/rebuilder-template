#!/bin/bash
# SRE Agent Local Development Startup Script

set -e

echo "🚀 Starting SRE Agent locally..."

# Load environment variables from .env if it exists
if [ -f ".env" ]; then
    echo "📝 Loading environment variables from .env"
    source .env
else
    echo "❌ .env file not found. Please create it from .env.example"
    exit 1
fi

# Verify required variables are set
required_vars=("LLM_API_KEY" "PAGERDUTY_API_TOKEN" "OPS_AUTH_TOKEN" "SERVICE_REGISTRY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Required environment variable $var is not set"
        exit 1
    fi
done

echo "✅ Environment variables loaded successfully"
echo "🔧 Starting uvicorn server on http://localhost:8080"
echo "📊 Health check: http://localhost:8080/health"
echo "📚 Docs: http://localhost:8080/docs"
echo ""

# Start the service
exec python -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload
