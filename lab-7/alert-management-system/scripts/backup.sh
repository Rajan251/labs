#!/bin/bash

# ============================================
# BACKUP SCRIPT
# ============================================
# Backs up Prometheus and Alertmanager data
# ============================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}Alert Management System - Backup${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo -e "${BLUE}Backup location: $BACKUP_DIR${NC}"
echo ""

# ==========================================
# Backup configurations
# ==========================================
echo -e "${BLUE}[1/3] Backing up configurations...${NC}"

CONFIG_BACKUP="$BACKUP_DIR/config_$TIMESTAMP.tar.gz"

tar -czf "$CONFIG_BACKUP" \
    -C "$PROJECT_ROOT" \
    prometheus/prometheus.yml \
    prometheus/rules/ \
    prometheus/targets/ \
    alertmanager/alertmanager.yml \
    alertmanager/templates/ \
    docker/docker-compose.yml \
    2>/dev/null || true

if [ -f "$CONFIG_BACKUP" ]; then
    echo -e "${GREEN}✓ Configuration backed up: $CONFIG_BACKUP${NC}"
else
    echo -e "${RED}✗ Configuration backup failed${NC}"
fi

echo ""

# ==========================================
# Backup Prometheus data
# ==========================================
echo -e "${BLUE}[2/3] Backing up Prometheus data...${NC}"

if docker ps | grep -q prometheus; then
    PROM_BACKUP="$BACKUP_DIR/prometheus_data_$TIMESTAMP.tar.gz"
    
    docker run --rm \
        --volumes-from prometheus \
        -v "$BACKUP_DIR:/backup" \
        alpine \
        tar -czf "/backup/prometheus_data_$TIMESTAMP.tar.gz" -C /prometheus . \
        2>/dev/null || true
    
    if [ -f "$PROM_BACKUP" ]; then
        echo -e "${GREEN}✓ Prometheus data backed up: $PROM_BACKUP${NC}"
    else
        echo -e "${RED}✗ Prometheus data backup failed${NC}"
    fi
else
    echo -e "${RED}✗ Prometheus container not running${NC}"
fi

echo ""

# ==========================================
# Backup Alertmanager data
# ==========================================
echo -e "${BLUE}[3/3] Backing up Alertmanager data...${NC}"

if docker ps | grep -q alertmanager; then
    AM_BACKUP="$BACKUP_DIR/alertmanager_data_$TIMESTAMP.tar.gz"
    
    docker run --rm \
        --volumes-from alertmanager \
        -v "$BACKUP_DIR:/backup" \
        alpine \
        tar -czf "/backup/alertmanager_data_$TIMESTAMP.tar.gz" -C /alertmanager . \
        2>/dev/null || true
    
    if [ -f "$AM_BACKUP" ]; then
        echo -e "${GREEN}✓ Alertmanager data backed up: $AM_BACKUP${NC}"
    else
        echo -e "${RED}✗ Alertmanager data backup failed${NC}"
    fi
else
    echo -e "${RED}✗ Alertmanager container not running${NC}"
fi

echo ""

# ==========================================
# Summary
# ==========================================
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}Backup completed!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "${BLUE}Backup files:${NC}"
ls -lh "$BACKUP_DIR"/*_$TIMESTAMP* 2>/dev/null || echo "No backups created"
echo ""
echo -e "${BLUE}To restore:${NC}"
echo "1. Stop services: docker-compose down"
echo "2. Extract backup: tar -xzf <backup-file>"
echo "3. Start services: docker-compose up -d"
echo ""
