#!/bin/bash

# Railway startup script for Voice Agent
# This script starts both the web server and the LiveKit agent

echo "🚀 Starting Voice Agent on Railway..."

# Check required environment variables
if [ -z "$LIVEKIT_API_KEY" ] || [ -z "$LIVEKIT_API_SECRET" ] || [ -z "$LIVEKIT_URL" ] || [ -z "$CEREBRAS_API_KEY" ]; then
    echo "❌ Missing required environment variables!"
    echo "Required: LIVEKIT_API_KEY, LIVEKIT_API_SECRET, LIVEKIT_URL, CEREBRAS_API_KEY"
    exit 1
fi

# Start the LiveKit agent in the background
echo "🤖 Starting LiveKit agent..."
python agent.py start &
AGENT_PID=$!

# Give the agent a moment to start
sleep 3

# Start the web server in the foreground
echo "🌐 Starting web server on port ${PORT:-8080}..."
python server.py

# If web server exits, also stop the agent
kill $AGENT_PID 2>/dev/null
