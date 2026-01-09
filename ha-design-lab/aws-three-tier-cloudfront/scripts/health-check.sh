#!/bin/bash
# Health check script for AWS Three-Tier Architecture

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_failure() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Check if environment argument is provided
if [ -z "$1" ]; then
    ENVIRONMENT="dev"
else
    ENVIRONMENT=$1
fi

TERRAFORM_DIR="terraform/environments/${ENVIRONMENT}"

if [ ! -d "$TERRAFORM_DIR" ]; then
    print_failure "Environment directory not found: $TERRAFORM_DIR"
    exit 1
fi

cd "$TERRAFORM_DIR"

print_info "Running health checks for environment: $ENVIRONMENT"
echo ""

# Get outputs
ALB_DNS=$(terraform output -raw alb_dns_name 2>/dev/null || echo "")
CLOUDFRONT_DOMAIN=$(terraform output -raw cloudfront_domain_name 2>/dev/null || echo "")
VPN_IP=$(terraform output -raw vpn_server_ip 2>/dev/null || echo "")
APP_ASG=$(terraform output -raw app_asg_name 2>/dev/null || echo "")
DB_ASG=$(terraform output -raw db_asg_name 2>/dev/null || echo "")

# Check VPN Server
print_info "Checking VPN Server..."
if [ -n "$VPN_IP" ]; then
    if ping -c 1 -W 2 "$VPN_IP" &> /dev/null; then
        print_success "VPN Server is reachable at $VPN_IP"
    else
        print_failure "VPN Server is not reachable at $VPN_IP"
    fi
else
    print_failure "VPN Server IP not found"
fi

# Check ALB
print_info "Checking Application Load Balancer..."
if [ -n "$ALB_DNS" ]; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://$ALB_DNS" || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        print_success "ALB is healthy (HTTP $HTTP_CODE)"
    else
        print_failure "ALB returned HTTP $HTTP_CODE"
    fi
else
    print_failure "ALB DNS not found"
fi

# Check CloudFront
print_info "Checking CloudFront Distribution..."
if [ -n "$CLOUDFRONT_DOMAIN" ]; then
    CF_STATUS=$(aws cloudfront get-distribution --id "$(terraform output -raw cloudfront_distribution_id)" --query 'Distribution.Status' --output text 2>/dev/null || echo "Unknown")
    if [ "$CF_STATUS" = "Deployed" ]; then
        print_success "CloudFront is deployed"
    else
        print_failure "CloudFront status: $CF_STATUS"
    fi
else
    print_failure "CloudFront domain not found"
fi

# Check Auto Scaling Groups
print_info "Checking Auto Scaling Groups..."
if [ -n "$APP_ASG" ]; then
    APP_INSTANCES=$(aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names "$APP_ASG" --query 'AutoScalingGroups[0].Instances[?HealthStatus==`Healthy`]' --output json | jq length)
    print_success "Application ASG has $APP_INSTANCES healthy instances"
else
    print_failure "Application ASG not found"
fi

if [ -n "$DB_ASG" ]; then
    DB_INSTANCES=$(aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names "$DB_ASG" --query 'AutoScalingGroups[0].Instances[?HealthStatus==`Healthy`]' --output json | jq length)
    print_success "Database ASG has $DB_INSTANCES healthy instances"
else
    print_failure "Database ASG not found"
fi

# Check GuardDuty
print_info "Checking GuardDuty..."
GD_STATUS=$(aws guardduty list-detectors --query 'DetectorIds[0]' --output text 2>/dev/null || echo "")
if [ -n "$GD_STATUS" ] && [ "$GD_STATUS" != "None" ]; then
    print_success "GuardDuty is enabled"
else
    print_failure "GuardDuty is not enabled"
fi

# Check CloudTrail
print_info "Checking CloudTrail..."
CT_STATUS=$(aws cloudtrail describe-trails --query 'trailList[?Name==`'$(terraform output -raw project_name 2>/dev/null || echo "unknown")'-'$ENVIRONMENT'-trail`].IsLogging' --output text 2>/dev/null || echo "")
if [ "$CT_STATUS" = "True" ]; then
    print_success "CloudTrail is logging"
else
    print_failure "CloudTrail is not logging"
fi

echo ""
print_info "Health check completed"
