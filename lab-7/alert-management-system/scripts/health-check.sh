#!/bin/bash

# ============================================
# HEALTH CHECK SCRIPT
# ============================================
# Checks the health of all monitoring components
# ============================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}Alert Management System - Health Check${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# ==========================================
# FUNCTION: Check service health
# ==========================================
check_service() {
    local service_name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo -n "Checking $service_name... "
    
    status_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    
    if [ "$status_code" = "$expected_status" ]; then
        echo -e "${GREEN}✓ OK${NC} (HTTP $status_code)"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $status_code)"
        return 1
    fi
}

# ==========================================
# FUNCTION: Check Docker container
# ==========================================
check_container() {
    local container_name=$1
    
    echo -n "Checking container $container_name... "
    
    if docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
        status=$(docker inspect --format='{{.State.Status}}' "$container_name")
        health=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "none")
        
        if [ "$status" = "running" ]; then
            if [ "$health" = "healthy" ] || [ "$health" = "none" ]; then
                echo -e "${GREEN}✓ Running${NC}"
                return 0
            else
                echo -e "${YELLOW}⚠ Running but unhealthy${NC} (health: $health)"
                return 1
            fi
        else
            echo -e "${RED}✗ Not running${NC} (status: $status)"
            return 1
        fi
    else
        echo -e "${RED}✗ Not found${NC}"
        return 1
    fi
}

# ==========================================
# Check Docker containers
# ==========================================
echo -e "${BLUE}[1/3] Checking Docker containers...${NC}"
echo ""

containers=("prometheus" "alertmanager" "node-exporter" "blackbox-exporter")
container_failures=0

for container in "${containers[@]}"; do
    check_container "$container" || ((container_failures++))
done

echo ""

# ==========================================
# Check service endpoints
# ==========================================
echo -e "${BLUE}[2/3] Checking service endpoints...${NC}"
echo ""

endpoint_failures=0

check_service "Prometheus" "http://localhost:9090/-/healthy" || ((endpoint_failures++))
check_service "Alertmanager" "http://localhost:9093/-/healthy" || ((endpoint_failures++))
check_service "Node Exporter" "http://localhost:9100/metrics" || ((endpoint_failures++))
check_service "Blackbox Exporter" "http://localhost:9115/health" || ((endpoint_failures++))

echo ""

# ==========================================
# Check Prometheus targets
# ==========================================
echo -e "${BLUE}[3/3] Checking Prometheus targets...${NC}"
echo ""

target_failures=0

if command -v jq &> /dev/null; then
    targets=$(curl -s http://localhost:9090/api/v1/targets | jq -r '.data.activeTargets[] | "\(.labels.job) - \(.health)"')
    
    while IFS= read -r line; do
        job=$(echo "$line" | cut -d' ' -f1)
        health=$(echo "$line" | cut -d' ' -f3)
        
        echo -n "Target $job... "
        if [ "$health" = "up" ]; then
            echo -e "${GREEN}✓ UP${NC}"
        else
            echo -e "${RED}✗ DOWN${NC}"
            ((target_failures++))
        fi
    done <<< "$targets"
else
    echo -e "${YELLOW}⚠ jq not installed, skipping target check${NC}"
fi

echo ""

# ==========================================
# Summary
# ==========================================
total_failures=$((container_failures + endpoint_failures + target_failures))

echo -e "${BLUE}============================================${NC}"
if [ $total_failures -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo -e "${BLUE}============================================${NC}"
    exit 0
else
    echo -e "${RED}✗ $total_failures check(s) failed${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo ""
    echo -e "${YELLOW}Troubleshooting:${NC}"
    echo "1. Check Docker logs: docker-compose logs [service]"
    echo "2. Restart services: docker-compose restart"
    echo "3. Check configuration files for errors"
    echo "4. View full status: docker-compose ps"
    exit 1
fi
