#!/bin/bash

# Voice Agent Docker Setup Script
# This script helps you get started with Docker instead of virtual environment

echo "🎤 Voice Agent Docker Setup"
echo "=========================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker Desktop first."
    echo "   Download from: https://www.docker.com/products/docker-desktop/"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

echo "✅ Docker is installed and running"

# Check if .env file exists
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "📝 Creating .env file from .env.example..."
        cp .env.example .env
        echo "⚠️  Please edit .env file and add your API keys before continuing."
        echo "   Required keys: LIVEKIT_API_KEY, LIVEKIT_API_SECRET, CEREBRAS_API_KEY, DEEPGRAM_API_KEY"
        
        # Ask if user wants to edit now
        read -p "Do you want to edit the .env file now? (y/n): " edit_env
        if [ "$edit_env" = "y" ] || [ "$edit_env" = "Y" ]; then
            ${EDITOR:-nano} .env
        else
            echo "Please edit .env manually before running the application."
            exit 1
        fi
    else
        echo "❌ .env.example file not found. Please create .env file manually."
        exit 1
    fi
fi

echo "✅ Environment file (.env) exists"

# Build and start the application
echo "🏗️  Building Docker images..."
docker-compose build

if [ $? -eq 0 ]; then
    echo "✅ Docker images built successfully"
    
    echo "🚀 Starting Voice Agent application..."
    docker-compose up -d
    
    if [ $? -eq 0 ]; then
        echo "✅ Voice Agent is now running!"
        echo ""
        echo "🌐 Web Interface: http://localhost:8080"
        echo ""
        echo "📋 Useful commands:"
        echo "   View logs:     docker-compose logs -f"
        echo "   Stop app:      docker-compose down"  
        echo "   Restart:       docker-compose restart"
        echo ""
        echo "📖 For more details, see README.md"
        
        # Open browser (optional)
        read -p "Do you want to open the web interface in your browser? (y/n): " open_browser
        if [ "$open_browser" = "y" ] || [ "$open_browser" = "Y" ]; then
            if command -v open &> /dev/null; then
                open http://localhost:8080
            elif command -v xdg-open &> /dev/null; then
                xdg-open http://localhost:8080
            else
                echo "Please open http://localhost:8080 in your browser manually."
            fi
        fi
    else
        echo "❌ Failed to start Voice Agent application"
        exit 1
    fi
else
    echo "❌ Failed to build Docker images"
    exit 1
fi
