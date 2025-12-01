#!/bin/bash
# 01-manual-deployment/deploy-manual.sh
# A script to guide a user through a manual deployment process.
# Usage: ./deploy-manual.sh <server_ip> <user> <key_path>

SERVER_IP=$1
USER=$2
KEY_PATH=$3
APP_DIR="/var/www/myapp"
LOCAL_BUILD_DIR="./build"

if [ -z "$SERVER_IP" ] || [ -z "$USER" ] || [ -z "$KEY_PATH" ]; then
    echo "Usage: $0 <server_ip> <user> <key_path>"
    exit 1
fi

echo ">>> Starting Manual Deployment to $SERVER_IP..."

# Step 1: Build the application locally
echo ">>> Step 1: Building application..."
# Example build command
# npm install && npm run build
mkdir -p $LOCAL_BUILD_DIR
echo "Build Artifact" > $LOCAL_BUILD_DIR/index.html
echo "✅ Build complete."

# Step 2: Transfer files
echo ">>> Step 2: Transferring files to server..."
scp -i $KEY_PATH -r $LOCAL_BUILD_DIR/* $USER@$SERVER_IP:/tmp/myapp_build/
if [ $? -ne 0 ]; then
    echo "❌ File transfer failed."
    exit 1
fi
echo "✅ Files transferred."

# Step 3: Connect and Install/Restart
echo ">>> Step 3: Configuring server and restarting services..."
ssh -i $KEY_PATH $USER@$SERVER_IP << EOF
    echo "--- Connected to Server ---"
    
    # Backup existing version
    if [ -d "$APP_DIR" ]; then
        echo "Backing up current version..."
        sudo cp -r $APP_DIR ${APP_DIR}_backup_\$(date +%F_%T)
    fi

    # Create app directory if not exists
    sudo mkdir -p $APP_DIR

    # Move new files
    echo "Deploying new version..."
    sudo cp -r /tmp/myapp_build/* $APP_DIR/
    
    # Fix permissions
    sudo chown -R www-data:www-data $APP_DIR
    sudo chmod -R 755 $APP_DIR

    # Restart Service (e.g., NGINX or Systemd service)
    echo "Restarting service..."
    # sudo systemctl restart myapp
    # sudo systemctl restart nginx
    
    echo "--- Deployment Complete ---"
EOF

echo "✅ Manual Deployment Finished Successfully."
