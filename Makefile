# Makefile for Voice Agent Docker operations

.PHONY: help build up down logs restart clean shell

# Default target
help:
	@echo "Voice Agent Docker Commands:"
	@echo "  make build    - Build Docker images"
	@echo "  make up       - Start all services"
	@echo "  make down     - Stop all services"
	@echo "  make logs     - View all logs"
	@echo "  make restart  - Restart all services"
	@echo "  make clean    - Remove containers and images"
	@echo "  make shell    - Open shell in server container"

# Build Docker images
build:
	docker-compose build

# Start services
up:
	docker-compose up -d
	@echo "Services started! Access web interface at http://localhost:8080"

# Start services with logs
up-logs:
	docker-compose up

# Stop services
down:
	docker-compose down

# View logs
logs:
	docker-compose logs -f

# Restart services
restart:
	docker-compose restart

# Clean up containers and images
clean:
	docker-compose down -v --rmi all

# Open shell in server container
shell:
	docker-compose exec voice-agent-server /bin/bash

# Quick development restart
dev-restart: down build up-logs
