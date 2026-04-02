#!/bin/bash
# Codespaces startup script for Advisor Voice Agent

echo "🚀 Starting Advisor Voice Agent..."

# Check if .env exists, if not create from example
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "⚠️  Created .env from .env.example - please update with your API keys"
    fi
fi

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Set Codespaces-specific defaults
export PORT=${PORT:-8080}
export GRADIO_SERVER_PORT=${GRADIO_SERVER_PORT:-8080}
export GRADIO_SERVER_NAME="0.0.0.0"
export PYTHONUNBUFFERED=1

echo "📊 Environment:"
echo "  PORT: $PORT"
echo "  GRADIO_SERVER_PORT: $GRADIO_SERVER_PORT"
echo "  GRADIO_SERVER_NAME: $GRADIO_SERVER_NAME"

echo "🎯 Starting application..."
python app.py
