#!/bin/bash

# ============================================
# MongoDB Replica Set Configuration Script
# ============================================

set -e

echo "🗄️  MongoDB Replica Set Configuration"
echo "======================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    print_error "jq is not installed. Install it with: sudo yum install -y jq"
    exit 1
fi

# Get MongoDB IPs from Terraform outputs
if [ -f "../deployment-outputs.json" ]; then
    MONGO_PRIMARY_IP=$(jq -r '.mongodb_primary_private_ip.value' ../deployment-outputs.json)
    MONGO_SECONDARY_IP=$(jq -r '.mongodb_secondary_private_ip.value' ../deployment-outputs.json)
else
    print_error "deployment-outputs.json not found"
    print_info "Run deploy.sh first or manually set MONGO_PRIMARY_IP and MONGO_SECONDARY_IP"
    exit 1
fi

print_info "MongoDB Primary IP: $MONGO_PRIMARY_IP"
print_info "MongoDB Secondary IP: $MONGO_SECONDARY_IP"
echo ""

# Prompt for passwords
read -sp "Enter MongoDB admin password: " ADMIN_PASSWORD
echo ""
read -sp "Enter MongoDB app user password: " APP_PASSWORD
echo ""
echo ""

# Create replica set initialization script
cat > /tmp/init-replica-set.js <<EOF
// Initialize replica set
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "$MONGO_PRIMARY_IP:27017", priority: 2 },
    { _id: 1, host: "$MONGO_SECONDARY_IP:27017", priority: 1 }
  ]
});

// Wait for replica set to initialize
sleep(5000);

// Create admin user
use admin;
db.createUser({
  user: "admin",
  pwd: "$ADMIN_PASSWORD",
  roles: [{ role: "root", db: "admin" }]
});

// Create application user
use myapp;
db.createUser({
  user: "appuser",
  pwd: "$APP_PASSWORD",
  roles: [{ role: "readWrite", db: "myapp" }]
});

print("✅ Replica set initialized and users created");
EOF

print_info "Replica set configuration script created"
echo ""

print_info "To complete the setup:"
echo "1. SSH to MongoDB primary instance"
echo "2. Copy and run the initialization script"
echo ""
echo "Commands:"
echo "  scp -i your-key.pem /tmp/init-replica-set.js ec2-user@$MONGO_PRIMARY_IP:/tmp/"
echo "  ssh -i your-key.pem ec2-user@$MONGO_PRIMARY_IP"
echo "  mongosh < /tmp/init-replica-set.js"
echo ""

print_success "Configuration script ready at /tmp/init-replica-set.js"
