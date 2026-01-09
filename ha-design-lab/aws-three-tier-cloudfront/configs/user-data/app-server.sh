#!/bin/bash
# Application Server User Data Script
# This script sets up a basic Node.js application server

set -e

# Update system
yum update -y

# Install Node.js
curl -sL https://rpm.nodesource.com/setup_18.x | bash -
yum install -y nodejs

# Install CloudWatch Agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
rpm -U ./amazon-cloudwatch-agent.rpm

# Install Git
yum install -y git

# Create application directory
mkdir -p /opt/app
cd /opt/app

# Create a sample Node.js application
cat > /opt/app/server.js <<'EOF'
const http = require('http');
const os = require('os');

const PORT = process.env.PORT || 8080;

const server = http.createServer((req, res) => {
  if (req.url === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'healthy', hostname: os.hostname() }));
  } else {
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(`
      <html>
        <head><title>Three-Tier App</title></head>
        <body>
          <h1>Welcome to Three-Tier Application!</h1>
          <p>Server: ${os.hostname()}</p>
          <p>Platform: ${os.platform()}</p>
          <p>Uptime: ${os.uptime()} seconds</p>
        </body>
      </html>
    `);
  }
});

server.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
EOF

# Create package.json
cat > /opt/app/package.json <<'EOF'
{
  "name": "three-tier-app",
  "version": "1.0.0",
  "description": "Sample application for three-tier architecture",
  "main": "server.js",
  "scripts": {
    "start": "node server.js"
  }
}
EOF

# Install dependencies
npm install

# Create systemd service
cat > /etc/systemd/system/app.service <<'EOF'
[Unit]
Description=Three-Tier Application
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/opt/app
ExecStart=/usr/bin/node /opt/app/server.js
Restart=on-failure
Environment=PORT=8080

[Install]
WantedBy=multi-user.target
EOF

# Set permissions
chown -R ec2-user:ec2-user /opt/app

# Enable and start application
systemctl daemon-reload
systemctl enable app
systemctl start app

echo "Application server setup complete!"
