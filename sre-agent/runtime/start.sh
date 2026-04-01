#!/bin/bash
# SRE Agent Local Development Startup Script

set -e

echo "🚀 Starting SRE Agent locally..."

# Activate Python 3.12 virtual environment
if [ -d ".venv312" ]; then
    echo "🐍 Using Python 3.12 virtual environment"
    source .venv312/bin/activate
else
    echo "⚠️  Python 3.12 virtual environment not found"
    echo "   Creating it now..."
    python3.12 -m venv .venv312
    source .venv312/bin/activate
    pip install -r requirements.txt
    echo "✅ Virtual environment created and dependencies installed"
fi

# The config.py now automatically loads .env if it exists
# But we still check for it to provide better error messages
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "📝 Created .env from .env.example - please edit it with your values"
        echo "   Required variables: LLM_API_KEY or Vertex AI config, PAGERDUTY_API_TOKEN, OPS_AUTH_TOKEN, SERVICE_REGISTRY"
        exit 1
    else
        echo "❌ .env.example file not found"
        exit 1
    fi
fi

echo "📝 Using configuration from .env file (auto-loaded)"

# Verify the application can load configuration
python -c "
import sys
import os
sys.path.insert(0, '.')
try:
    from config import Config
    config = Config()
    print('✅ Configuration loaded successfully')
    print(f'   LLM Provider: {\"Vertex AI\" if config.vertex_ai else \"API Key\"}')
    print(f'   Model: {config.llm_model}')
    if not config.vertex_ai and not config.llm_api_key:
        print('❌ LLM_API_KEY is required for non-Vertex AI providers')
        sys.exit(1)
    if not config.pagerduty_api_token:
        print('❌ PAGERDUTY_API_TOKEN is required')
        sys.exit(1)
    if not config.ops_auth_token:
        print('❌ OPS_AUTH_TOKEN is required')
        sys.exit(1)
    if not config.services:
        print('❌ SERVICE_REGISTRY is required')
        sys.exit(1)
except Exception as e:
    print(f'❌ Configuration error: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    exit 1
fi

echo "✅ Environment configuration validated"
echo "🔧 Starting uvicorn server on http://localhost:8080"
echo "📊 Health check: http://localhost:8080/health"
echo "📚 Docs: http://localhost:8080/docs"
echo ""

# Start the service
exec python -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload
