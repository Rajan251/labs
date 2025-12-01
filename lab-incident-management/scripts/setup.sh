#!/bin/bash

# Setup script for Incident Management & Alerting System
# This script initializes the development environment

set -e

echo "🚀 Setting up Incident Management & Alerting System..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker installed${NC}"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose installed${NC}"

# Check Python (for incident API later)
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}⚠ Python 3 is not installed. Required for incident API.${NC}"
else
    echo -e "${GREEN}✓ Python 3 installed${NC}"
fi

# Check promtool (optional)
if ! command -v promtool &> /dev/null; then
    echo -e "${YELLOW}⚠ promtool is not installed. Alert validation will be skipped.${NC}"
else
    echo -e "${GREEN}✓ promtool installed${NC}"
fi

echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created${NC}"
    echo -e "${YELLOW}⚠ Please edit .env file with your actual credentials${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

echo ""

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/grafana/provisioning/datasources
mkdir -p monitoring/grafana/provisioning/dashboards
mkdir -p monitoring/prometheus/alerts
mkdir -p monitoring/alertmanager/templates
mkdir -p monitoring/blackbox
mkdir -p incident-api/migrations/versions
mkdir -p slack-bot/handlers
mkdir -p runbooks
mkdir -p automation
mkdir -p postmortem/templates
mkdir -p analytics
mkdir -p scripts
mkdir -p tests/integration
mkdir -p docs/ADR
echo -e "${GREEN}✓ Directories created${NC}"

echo ""

# Validate Prometheus configuration
if command -v promtool &> /dev/null; then
    echo "🔍 Validating Prometheus configuration..."
    
    if promtool check config monitoring/prometheus/prometheus.yml; then
        echo -e "${GREEN}✓ Prometheus config is valid${NC}"
    else
        echo -e "${RED}❌ Prometheus config validation failed${NC}"
        exit 1
    fi
    
    echo ""
    echo "🔍 Validating alert rules..."
    
    for file in monitoring/prometheus/alerts/*.yaml; do
        if [ -f "$file" ]; then
            if promtool check rules "$file"; then
                echo -e "${GREEN}✓ $(basename $file) is valid${NC}"
            else
                echo -e "${RED}❌ $(basename $file) validation failed${NC}"
                exit 1
            fi
        fi
    done
    
    if promtool check rules monitoring/prometheus/recording_rules.yaml; then
        echo -e "${GREEN}✓ recording_rules.yaml is valid${NC}"
    else
        echo -e "${RED}❌ recording_rules.yaml validation failed${NC}"
        exit 1
    fi
fi

echo ""

# Check Alertmanager configuration
echo "🔍 Checking Alertmanager configuration..."
if grep -q "YOUR_PAGERDUTY_SERVICE_KEY" monitoring/alertmanager/config.yml; then
    echo -e "${YELLOW}⚠ Please update PagerDuty service key in monitoring/alertmanager/config.yml${NC}"
fi
if grep -q "YOUR/SLACK/WEBHOOK" monitoring/alertmanager/config.yml; then
    echo -e "${YELLOW}⚠ Please update Slack webhook URL in monitoring/alertmanager/config.yml${NC}"
fi

echo ""

# Summary
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your credentials"
echo "2. Update monitoring/alertmanager/config.yml with PagerDuty and Slack credentials"
echo "3. Run: docker-compose up -d"
echo "4. Access services:"
echo "   - Prometheus: http://localhost:9090"
echo "   - Grafana: http://localhost:3000 (admin/admin)"
echo "   - Alertmanager: http://localhost:9093"
echo ""
echo "For more information, see docs/SETUP.md"
