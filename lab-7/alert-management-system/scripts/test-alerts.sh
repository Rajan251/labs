#!/bin/bash

# ============================================
# TEST ALERTS SCRIPT
# ============================================
# This script sends test alerts to Alertmanager
# to verify the alert routing and notification setup
# ============================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ALERTMANAGER_URL="${ALERTMANAGER_URL:-http://localhost:9093}"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}Alert Management System - Test Alerts${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# ==========================================
# FUNCTION: Send test alert
# ==========================================
send_alert() {
    local alertname=$1
    local severity=$2
    local summary=$3
    local description=$4
    
    echo -e "${BLUE}Sending test alert: $alertname${NC}"
    
    curl -s -X POST "$ALERTMANAGER_URL/api/v2/alerts" \
        -H "Content-Type: application/json" \
        -d "[{
            \"labels\": {
                \"alertname\": \"$alertname\",
                \"severity\": \"$severity\",
                \"cluster\": \"production\",
                \"environment\": \"prod\",
                \"component\": \"test\",
                \"team\": \"infrastructure\"
            },
            \"annotations\": {
                \"summary\": \"$summary\",
                \"description\": \"$description\",
                \"runbook_url\": \"https://runbooks.example.com/test\"
            },
            \"startsAt\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",
            \"endsAt\": \"$(date -u -d '+5 minutes' +%Y-%m-%dT%H:%M:%SZ)\"
        }]"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Alert sent successfully${NC}"
    else
        echo -e "${RED}✗ Failed to send alert${NC}"
        return 1
    fi
    
    echo ""
}

# ==========================================
# Check if Alertmanager is running
# ==========================================
echo -e "${BLUE}Checking Alertmanager status...${NC}"

if curl -s "$ALERTMANAGER_URL/-/healthy" > /dev/null; then
    echo -e "${GREEN}✓ Alertmanager is running${NC}"
else
    echo -e "${RED}✗ Alertmanager is not accessible at $ALERTMANAGER_URL${NC}"
    echo "Please start the system first: cd docker && docker-compose up -d"
    exit 1
fi

echo ""

# ==========================================
# Send test alerts
# ==========================================
echo -e "${YELLOW}Sending test alerts...${NC}"
echo ""

# Test 1: Critical alert (should go to PagerDuty)
send_alert \
    "TestCriticalAlert" \
    "critical" \
    "TEST: Critical alert for PagerDuty" \
    "This is a test critical alert. It should trigger a PagerDuty incident."

sleep 2

# Test 2: Warning alert (should go to Slack)
send_alert \
    "TestWarningAlert" \
    "warning" \
    "TEST: Warning alert for Slack" \
    "This is a test warning alert. It should send a Slack notification."

sleep 2

# Test 3: Info alert (should go to Email)
send_alert \
    "TestInfoAlert" \
    "info" \
    "TEST: Info alert for Email" \
    "This is a test info alert. It should send an email notification."

# ==========================================
# Summary
# ==========================================
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}Test alerts sent successfully!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "${BLUE}What to check:${NC}"
echo "1. Alertmanager UI: $ALERTMANAGER_URL/#/alerts"
echo "2. PagerDuty: Check for incident from TestCriticalAlert"
echo "3. Slack: Check #alerts-warnings channel for TestWarningAlert"
echo "4. Email: Check inbox for TestInfoAlert"
echo ""
echo -e "${YELLOW}Note: Alerts will auto-resolve in 5 minutes${NC}"
echo ""

# ==========================================
# Optional: Show current alerts
# ==========================================
echo -e "${BLUE}Current alerts in Alertmanager:${NC}"
curl -s "$ALERTMANAGER_URL/api/v2/alerts" | jq -r '.[] | "\(.labels.alertname) - \(.labels.severity) - \(.status.state)"' 2>/dev/null || echo "Install jq to see formatted output"
echo ""
