#!/bin/bash
# 12-cloud-deployments/gcp/gce-startup-script.sh

apt-get update
apt-get install -y docker.io git

# Clone and run
git clone https://github.com/example/myapp.git /opt/myapp
cd /opt/myapp
docker build -t myapp .
docker run -d -p 80:8000 myapp
