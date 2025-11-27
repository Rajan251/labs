#!/bin/bash

# ============================================
# ALERT MANAGEMENT SYSTEM - SETUP SCRIPT
# ============================================
# This script performs initial setup:
# - Validates prerequisites
# - Creates necessary directories
# - Validates configurations
# - Sets up environment
# ============================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}Alert Management System - Setup${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# ==========================================
# FUNCTION: Print colored messages
# ==========================================
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# ==========================================
# STEP 1: Check Prerequisites
# ==========================================
echo -e "${BLUE}[1/6] Checking prerequisites...${NC}"

# Check Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
    print_success "Docker installed: $DOCKER_VERSION"
else
    print_error "Docker is not installed"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check Docker Compose
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version | awk '{print $3}' | sed 's/,//')
    print_success "Docker Compose installed: $COMPOSE_VERSION"
else
    print_error "Docker Compose is not installed"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if Docker daemon is running
if docker info &> /dev/null; then
    print_success "Docker daemon is running"
else
    print_error "Docker daemon is not running"
    echo "Please start Docker daemon"
    exit 1
fi

echo ""

# ==========================================
# STEP 2: Create Directories
# ==========================================
echo -e "${BLUE}[2/6] Creating directories...${NC}"

mkdir -p "$PROJECT_ROOT/prometheus/rules"
mkdir -p "$PROJECT_ROOT/prometheus/targets"
mkdir -p "$PROJECT_ROOT/alertmanager/templates"
mkdir -p "$PROJECT_ROOT/alertmanager/config"
mkdir -p "$PROJECT_ROOT/pagerduty"
mkdir -p "$PROJECT_ROOT/scripts"
mkdir -p "$PROJECT_ROOT/docs"
mkdir -p "$PROJECT_ROOT/examples"

print_success "Directories created"
echo ""

# ==========================================
# STEP 3: Setup Environment File
# ==========================================
echo -e "${BLUE}[3/6] Setting up environment file...${NC}"

ENV_FILE="$PROJECT_ROOT/docker/.env"
ENV_EXAMPLE="$PROJECT_ROOT/docker/.env.example"

if [ -f "$ENV_FILE" ]; then
    print_warning ".env file already exists, skipping..."
else
    if [ -f "$ENV_EXAMPLE" ]; then
        cp "$ENV_EXAMPLE" "$ENV_FILE"
        print_success "Created .env file from template"
        print_warning "IMPORTANT: Edit $ENV_FILE and add your PagerDuty integration key!"
    else
        print_error ".env.example not found"
        exit 1
    fi
fi

echo ""

# ==========================================
# STEP 4: Validate Prometheus Configuration
# ==========================================
echo -e "${BLUE}[4/6] Validating Prometheus configuration...${NC}"

PROM_CONFIG="$PROJECT_ROOT/prometheus/prometheus.yml"

if [ -f "$PROM_CONFIG" ]; then
    # Use promtool if available, otherwise skip validation
    if command -v promtool &> /dev/null; then
        if promtool check config "$PROM_CONFIG" &> /dev/null; then
            print_success "Prometheus configuration is valid"
        else
            print_error "Prometheus configuration is invalid"
            promtool check config "$PROM_CONFIG"
            exit 1
        fi
    else
        print_warning "promtool not found, skipping validation"
        print_info "Configuration will be validated when Prometheus starts"
    fi
else
    print_error "Prometheus configuration not found: $PROM_CONFIG"
    exit 1
fi

echo ""

# ==========================================
# STEP 5: Validate Alert Rules
# ==========================================
echo -e "${BLUE}[5/6] Validating alert rules...${NC}"

RULES_DIR="$PROJECT_ROOT/prometheus/rules"

if [ -d "$RULES_DIR" ]; then
    RULE_COUNT=$(find "$RULES_DIR" -name "*.yml" | wc -l)
    
    if [ "$RULE_COUNT" -gt 0 ]; then
        if command -v promtool &> /dev/null; then
            for rule_file in "$RULES_DIR"/*.yml; do
                if promtool check rules "$rule_file" &> /dev/null; then
                    print_success "Valid: $(basename "$rule_file")"
                else
                    print_error "Invalid: $(basename "$rule_file")"
                    promtool check rules "$rule_file"
                    exit 1
                fi
            done
        else
            print_warning "promtool not found, skipping validation"
            print_info "Found $RULE_COUNT rule files"
        fi
    else
        print_warning "No alert rule files found in $RULES_DIR"
    fi
else
    print_error "Rules directory not found: $RULES_DIR"
    exit 1
fi

echo ""

# ==========================================
# STEP 6: Validate Alertmanager Configuration
# ==========================================
echo -e "${BLUE}[6/6] Validating Alertmanager configuration...${NC}"

AM_CONFIG="$PROJECT_ROOT/alertmanager/alertmanager.yml"

if [ -f "$AM_CONFIG" ]; then
    # Use amtool if available, otherwise skip validation
    if command -v amtool &> /dev/null; then
        if amtool check-config "$AM_CONFIG" &> /dev/null; then
            print_success "Alertmanager configuration is valid"
        else
            print_error "Alertmanager configuration is invalid"
            amtool check-config "$AM_CONFIG"
            exit 1
        fi
    else
        print_warning "amtool not found, skipping validation"
        print_info "Configuration will be validated when Alertmanager starts"
    fi
else
    print_error "Alertmanager configuration not found: $AM_CONFIG"
    exit 1
fi

echo ""

# ==========================================
# SUMMARY
# ==========================================
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}Setup completed successfully!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Edit docker/.env and add your PagerDuty integration key"
echo "2. Start the system: cd docker && docker-compose up -d"
echo "3. Check status: docker-compose ps"
echo "4. Test alerts: ../scripts/test-alerts.sh"
echo ""
echo -e "${BLUE}Web Interfaces:${NC}"
echo "• Prometheus:    http://localhost:9090"
echo "• Alertmanager:  http://localhost:9093"
echo "• Node Exporter: http://localhost:9100/metrics"
echo ""
echo -e "${YELLOW}⚠ Remember to configure your PagerDuty integration key!${NC}"
echo ""
