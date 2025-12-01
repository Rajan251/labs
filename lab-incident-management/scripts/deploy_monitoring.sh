#!/bin/bash

# Deploy monitoring stack using Docker Compose

set -e

echo "🚀 Deploying monitoring stack..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please run ./scripts/setup.sh first."
    exit 1
fi

# Pull latest images
echo "📥 Pulling Docker images..."
docker-compose pull

# Start services
echo "🐳 Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

services=("prometheus" "grafana" "alertmanager" "node-exporter" "cadvisor" "postgres" "redis")

for service in "${services[@]}"; do
    if docker-compose ps | grep -q "$service.*Up"; then
        echo "✓ $service is running"
    else
        echo "❌ $service is not running"
        docker-compose logs "$service"
        exit 1
    fi
done

echo ""
echo "✅ Monitoring stack deployed successfully!"
echo ""
echo "Access services at:"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana: http://localhost:3000 (admin/admin)"
echo "  - Alertmanager: http://localhost:9093"
echo "  - Node Exporter: http://localhost:9100"
echo "  - cAdvisor: http://localhost:8080"
echo ""
echo "To view logs: docker-compose logs -f [service-name]"
echo "To stop: docker-compose down"
