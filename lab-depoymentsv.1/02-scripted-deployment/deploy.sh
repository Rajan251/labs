#!/bin/bash
# 02-scripted-deployment/deploy.sh
# Automated deployment script using rsync and ssh.

set -e

SERVERS=("192.168.1.10" "192.168.1.11")
USER="deploy"
SSH_KEY="~/.ssh/id_rsa"
REMOTE_DIR="/opt/app"
LOCAL_DIR="./dist"

echo "🚀 Starting Deployment..."

# Build
echo "📦 Building application..."
# npm run build
mkdir -p $LOCAL_DIR
echo "v2.0.0" > $LOCAL_DIR/version.txt

for SERVER in "${SERVERS[@]}"; do
    echo "----------------------------------------"
    echo "📡 Deploying to $SERVER..."
    
    # Sync files
    echo "   Syncing files..."
    rsync -avz -e "ssh -i $SSH_KEY" --delete $LOCAL_DIR/ $USER@$SERVER:$REMOTE_DIR/
    
    # Restart service
    echo "   Restarting service..."
    ssh -i $SSH_KEY $USER@$SERVER "sudo systemctl restart myapp.service"
    
    # Health check
    echo "   Verifying health..."
    HTTP_STATUS=$(ssh -i $SSH_KEY $USER@$SERVER "curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/health || echo 500")
    
    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "✅ $SERVER is healthy."
    else
        echo "❌ $SERVER failed health check (Status: $HTTP_STATUS)."
        exit 1
    fi
done

echo "🎉 Deployment Complete!"
