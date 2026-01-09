#!/bin/bash

# Update system
yum update -y

# Install Node.js 18
curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -
yum install -y nodejs

# Install NGINX
amazon-linux-extras install nginx1 -y

# Create application directory
mkdir -p /var/www/app
cd /var/www/app

# Create package.json
cat > package.json <<'PKG'
{
  "name": "two-tier-app",
  "version": "1.0.0",
  "description": "Two-tier application with MongoDB",
  "main": "server.js",
  "scripts": {
    "start": "node server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "mongodb": "^6.0.0"
  }
}
PKG

# Create server.js
cat > server.js <<'APP'
const express = require('express');
const { MongoClient } = require('mongodb');

const app = express();
const PORT = process.env.PORT || 3000;

const MONGO_URI = process.env.MONGO_URI || 'mongodb://localhost:27017';
let db;

MongoClient.connect(MONGO_URI, {
  useNewUrlParser: true,
  useUnifiedTopology: true
})
  .then(client => {
    console.log('✅ Connected to MongoDB');
    db = client.db('myapp');
  })
  .catch(err => {
    console.error('❌ MongoDB connection error:', err);
  });

app.use(express.json());

app.get('/health', (req, res) => {
  const health = {
    status: 'UP',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    mongodb: db ? 'connected' : 'disconnected',
    hostname: require('os').hostname()
  };
  res.status(200).json(health);
});

app.get('/', (req, res) => {
  res.json({
    message: 'Welcome to Two-Tier Application',
    version: '1.0.0',
    timestamp: new Date().toISOString(),
    hostname: require('os').hostname()
  });
});

app.get('/api/items', async (req, res) => {
  try {
    const items = await db.collection('items').find().toArray();
    res.json({ success: true, count: items.length, data: items });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

app.post('/api/items', async (req, res) => {
  try {
    const result = await db.collection('items').insertOne({
      ...req.body,
      createdAt: new Date()
    });
    res.status(201).json({ success: true, id: result.insertedId });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`🚀 Server running on port $${PORT}`);
});
APP

# Create .env file
cat > .env <<EOF
PORT=3000
MONGO_URI=mongodb://appuser:${mongodb_app_password}@${mongodb_primary_ip}:27017,${mongodb_secondary_ip}:27017/myapp?replicaSet=rs0&readPreference=primaryPreferred
EOF

# Install dependencies
npm install

# Create systemd service
cat > /etc/systemd/system/webapp.service <<'SERVICE'
[Unit]
Description=Two-Tier Web Application
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/var/www/app
EnvironmentFile=/var/www/app/.env
ExecStart=/usr/bin/node server.js
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE

# Start application
systemctl daemon-reload
systemctl start webapp
systemctl enable webapp

# Configure NGINX
cat > /etc/nginx/nginx.conf <<'NGINX'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log;
pid /run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';

    access_log  /var/log/nginx/access.log  main;

    sendfile            on;
    tcp_nopush          on;
    tcp_nodelay         on;
    keepalive_timeout   65;
    types_hash_max_size 4096;

    include             /etc/nginx/mime.types;
    default_type        application/octet-stream;

    upstream nodejs_backend {
        server 127.0.0.1:3000;
        keepalive 64;
    }

    server {
        listen       80 default_server;
        listen       [::]:80 default_server;
        server_name  _;

        location / {
            proxy_pass http://nodejs_backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
        }
    }
}
NGINX

# Start NGINX
systemctl start nginx
systemctl enable nginx

echo "✅ Web/App setup complete"
