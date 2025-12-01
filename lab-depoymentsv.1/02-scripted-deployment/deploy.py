# 02-scripted-deployment/deploy.py
import os
import subprocess
import sys
import datetime

SERVERS = ["192.168.1.10", "192.168.1.11"]
USER = "deploy"
KEY_PATH = "~/.ssh/id_rsa"
REMOTE_PATH = "/opt/myapp"
LOCAL_PATH = "./dist"

def run_command(command):
    """Run a shell command and return output."""
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode().strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Error executing command: {command}")
        print(e.stderr.decode())
        sys.exit(1)

def build_app():
    print("📦 Building application...")
    # Simulate build
    if not os.path.exists(LOCAL_PATH):
        os.makedirs(LOCAL_PATH)
    with open(f"{LOCAL_PATH}/version.txt", "w") as f:
        f.write(f"Build {datetime.datetime.now()}")

def deploy_to_server(server):
    print(f"📡 Deploying to {server}...")
    
    # Rsync
    print(f"   Syncing files to {server}...")
    rsync_cmd = f"rsync -avz -e 'ssh -i {KEY_PATH}' {LOCAL_PATH}/ {USER}@{server}:{REMOTE_PATH}/"
    run_command(rsync_cmd)
    
    # Restart Service
    print(f"   Restarting service on {server}...")
    ssh_cmd = f"ssh -i {KEY_PATH} {USER}@{server} 'sudo systemctl restart myapp'"
    # run_command(ssh_cmd) # Commented out for safety in demo
    
    print(f"✅ {server} updated successfully.")

def main():
    print("🚀 Starting Python Deployment Script")
    build_app()
    
    for server in SERVERS:
        deploy_to_server(server)
        
    print("🎉 All servers deployed successfully.")

if __name__ == "__main__":
    main()
