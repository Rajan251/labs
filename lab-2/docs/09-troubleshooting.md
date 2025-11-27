# 9. Troubleshooting Guide

## Ubuntu Server Issues

### Issue 1: Disk Space Full

**Symptoms**:
- Cannot write files
- Services failing to start
- Slow performance

**Diagnosis**:
```bash
# Check disk usage
df -h

# Find large directories
du -sh /* | sort -h

# Find large files
find / -type f -size +100M -exec ls -lh {} \;
```

**Solutions**:
```bash
# Clean apt cache
sudo apt clean
sudo apt autoremove

# Clean journal logs
sudo journalctl --vacuum-time=7d

# Clean Docker (if installed)
docker system prune -a
docker volume prune

# Remove old kernels
sudo apt autoremove --purge
```

### Issue 2: Cannot Connect via SSH

**Solutions**:
```bash
# Check SSH service
sudo systemctl status sshd

# Check firewall
sudo ufw status

# Restart SSH
sudo systemctl restart sshd

# Check SSH config
sudo nano /etc/ssh/sshd_config
```

### Issue 3: High CPU/Memory Usage

**Diagnosis**:
```bash
# Check processes
top
htop

# Check specific process
ps aux | grep jenkins
```

**Solutions**:
- Increase server resources
- Optimize Jenkins jobs
- Limit concurrent builds

## Jenkins Issues

### Issue 1: Jenkins Won't Start

**Check logs**:
```bash
sudo journalctl -u jenkins -n 50
sudo tail -f /var/log/jenkins/jenkins.log
```

**Common causes and solutions**:

**Port conflict**:
```bash
# Check what's using port 8080
sudo lsof -i :8080

# Change Jenkins port
sudo nano /etc/default/jenkins
# Change HTTP_PORT=8080 to HTTP_PORT=8081

sudo systemctl restart jenkins
```

**Java not found**:
```bash
# Install Java
sudo apt install -y openjdk-17-jdk

# Verify
java -version
```

**Permission issues**:
```bash
# Fix ownership
sudo chown -R jenkins:jenkins /var/lib/jenkins
sudo chown -R jenkins:jenkins /var/cache/jenkins
sudo chown -R jenkins:jenkins /var/log/jenkins

sudo systemctl restart jenkins
```

### Issue 2: Plugin Installation Fails

**Solutions**:
```bash
# Check internet connectivity
ping google.com

# Configure proxy (if needed)
# Manage Jenkins → Manage Plugins → Advanced → HTTP Proxy

# Manually download plugin
# Download .hpi file and upload via Manage Jenkins → Manage Plugins → Advanced
```

### Issue 3: Build Stuck in Queue

**Causes**:
- No available executors
- Node offline
- Label mismatch

**Solutions**:
```bash
# Increase executors
# Manage Jenkins → Configure System → # of executors

# Check node status
# Manage Jenkins → Manage Nodes and Clouds

# Check build queue
# View queue on Jenkins dashboard
```

### Issue 4: Workspace Issues

**Clean workspace**:
```bash
# From Jenkins UI
# Job → Workspace → Wipe Out Current Workspace

# Manually
sudo rm -rf /var/lib/jenkins/workspace/<job-name>

# Fix permissions
sudo chown -R jenkins:jenkins /var/lib/jenkins/workspace
```

## Docker Issues

### Issue 1: Permission Denied on Docker Socket

**Error**:
```
Got permission denied while trying to connect to the Docker daemon socket
```

**Solutions**:
```bash
# Add user to docker group
sudo usermod -aG docker jenkins
sudo usermod -aG docker $USER

# Logout and login again, or:
newgrp docker

# Restart Jenkins
sudo systemctl restart jenkins

# Temporary fix (not recommended)
sudo chmod 666 /var/run/docker.sock
```

### Issue 2: Docker Daemon Not Running

**Check status**:
```bash
sudo systemctl status docker
```

**Start Docker**:
```bash
sudo systemctl start docker
sudo systemctl enable docker
```

**Check logs**:
```bash
sudo journalctl -u docker -n 50
```

### Issue 3: Image Build Fails

**"No space left on device"**:
```bash
# Clean Docker
docker system prune -a
docker volume prune

# Check disk space
df -h
```

**"Cannot connect to Docker daemon"**:
```bash
# Check Docker is running
sudo systemctl status docker

# Check socket
ls -l /var/run/docker.sock
```

**Build context too large**:
```bash
# Create .dockerignore file
echo "node_modules" >> .dockerignore
echo ".git" >> .dockerignore
echo "*.log" >> .dockerignore
```

### Issue 4: Container Keeps Restarting

**Check logs**:
```bash
docker logs <container-id>
docker logs --tail 100 <container-id>
```

**Common causes**:
- Application crash
- Missing environment variables
- Port conflict
- Resource limits

**Solutions**:
```bash
# Check container status
docker ps -a

# Inspect container
docker inspect <container-id>

# Check resource usage
docker stats <container-id>
```

## Kubernetes Issues

### Issue 1: ImagePullBackOff

**Error**: Cannot pull container image

**Diagnosis**:
```bash
kubectl describe pod <pod-name> -n <namespace>
```

**Common causes and solutions**:

**Image doesn't exist**:
```bash
# Verify image name and tag
docker pull <image-name>:<tag>
```

**Private registry authentication**:
```bash
# Create image pull secret
kubectl create secret docker-registry regcred \
  --docker-server=docker.io \
  --docker-username=<username> \
  --docker-password=<password> \
  --docker-email=<email> \
  -n <namespace>

# Add to deployment
spec:
  template:
    spec:
      imagePullSecrets:
      - name: regcred
```

**Network issues**:
```bash
# Test from node
ssh node
docker pull <image-name>:<tag>
```

### Issue 2: CrashLoopBackOff

**Error**: Container keeps crashing

**Diagnosis**:
```bash
# Check pod logs
kubectl logs <pod-name> -n <namespace>

# Check previous logs
kubectl logs <pod-name> --previous -n <namespace>

# Describe pod
kubectl describe pod <pod-name> -n <namespace>
```

**Common causes**:
- Application error
- Missing configuration
- Failed health checks
- Resource limits too low

**Solutions**:
```bash
# Check application logs for errors
kubectl logs <pod-name> -n <namespace>

# Increase resource limits
kubectl edit deployment <deployment-name> -n <namespace>

# Check ConfigMaps and Secrets
kubectl get configmap -n <namespace>
kubectl get secret -n <namespace>
```

### Issue 3: Pod Pending

**Error**: Pod stuck in Pending state

**Diagnosis**:
```bash
kubectl describe pod <pod-name> -n <namespace>
```

**Common causes**:

**Insufficient resources**:
```bash
# Check node resources
kubectl describe nodes

# Check resource requests
kubectl describe pod <pod-name> -n <namespace>
```

**Node selector mismatch**:
```bash
# Check node labels
kubectl get nodes --show-labels

# Update deployment
kubectl edit deployment <deployment-name> -n <namespace>
```

**PVC not bound**:
```bash
# Check PVC status
kubectl get pvc -n <namespace>

# Check PV
kubectl get pv
```

### Issue 4: Service Not Accessible

**Diagnosis**:
```bash
# Check service
kubectl get svc -n <namespace>

# Check endpoints
kubectl get endpoints <service-name> -n <namespace>

# Describe service
kubectl describe svc <service-name> -n <namespace>
```

**Solutions**:

**No endpoints**:
```bash
# Check pod labels match service selector
kubectl get pods -n <namespace> --show-labels
kubectl describe svc <service-name> -n <namespace>
```

**Wrong port**:
```bash
# Verify port configuration
kubectl describe svc <service-name> -n <namespace>
```

**Test from within cluster**:
```bash
# Create test pod
kubectl run test --image=busybox -it --rm -- sh

# Test service
wget -O- http://<service-name>.<namespace>.svc.cluster.local
```

### Issue 5: Deployment Not Updating

**Check rollout status**:
```bash
kubectl rollout status deployment/<deployment-name> -n <namespace>
```

**View rollout history**:
```bash
kubectl rollout history deployment/<deployment-name> -n <namespace>
```

**Force update**:
```bash
# Restart deployment
kubectl rollout restart deployment/<deployment-name> -n <namespace>

# Or delete pods
kubectl delete pods -l app=<app-label> -n <namespace>
```

## Pipeline Issues

### Issue 1: Pipeline Fails at Checkout

**Error**: Cannot clone repository

**Solutions**:
```bash
# Check Git credentials in Jenkins
# Manage Jenkins → Manage Credentials

# Test Git access from Jenkins
# Pipeline script:
sh 'git ls-remote <repo-url>'

# Check SSH keys
# For Jenkins user:
sudo -u jenkins ssh -T git@github.com
```

### Issue 2: Docker Build Fails in Pipeline

**Error**: docker: command not found

**Solutions**:
```bash
# Verify Docker is installed
docker --version

# Check jenkins user can run Docker
sudo -u jenkins docker ps

# Add jenkins to docker group
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins
```

### Issue 3: kubectl Command Fails

**Error**: Unable to connect to server

**Solutions**:
```bash
# Verify kubeconfig
sudo -u jenkins kubectl get nodes

# Check credentials in Jenkins
# Manage Jenkins → Manage Credentials

# Test in pipeline
withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
    sh 'kubectl get nodes'
}
```

### Issue 4: Image Push Fails

**Error**: Authentication required

**Solutions**:
```bash
# Login to registry
docker login

# For Jenkins, add credentials
# Manage Jenkins → Manage Credentials

# Use in pipeline
docker.withRegistry('https://docker.io', 'dockerhub-credentials') {
    dockerImage.push()
}
```

## YAML Syntax Errors

### Validate YAML

```bash
# Online validators or:
kubectl apply --dry-run=client -f deployment.yaml

# Use yamllint
sudo apt install yamllint
yamllint deployment.yaml
```

### Common YAML Mistakes

**Indentation**:
```yaml
# Wrong
spec:
containers:
- name: app

# Correct
spec:
  containers:
  - name: app
```

**Missing colons**:
```yaml
# Wrong
name app

# Correct
name: app
```

**Wrong quotes**:
```yaml
# Wrong
command: ['sh', '-c', 'echo "Hello World"']

# Correct
command: ['sh', '-c', 'echo Hello World']
```

## Network Issues

### Test Connectivity

```bash
# Test from Jenkins server
curl -I https://github.com
ping google.com

# Test Docker registry
curl -I https://registry-1.docker.io

# Test Kubernetes API
curl -k https://<k8s-api>:6443
```

### DNS Issues

```bash
# Check DNS resolution
nslookup github.com
dig github.com

# Test from pod
kubectl run test --image=busybox -it --rm -- nslookup kubernetes.default
```

## Best Practices for Troubleshooting

1. ✅ **Check logs first** - Most issues show up in logs
2. ✅ **Use describe commands** - Get detailed resource information
3. ✅ **Test incrementally** - Isolate the problem
4. ✅ **Check permissions** - Many issues are permission-related
5. ✅ **Verify connectivity** - Network issues are common
6. ✅ **Check resource limits** - CPU/memory constraints cause failures
7. ✅ **Review recent changes** - What changed before the issue?
8. ✅ **Use dry-run** - Test changes before applying

## Getting Help

### Useful Commands

```bash
# System information
uname -a
lsb_release -a

# Resource usage
free -h
df -h
top

# Network
ip addr
ip route
netstat -tulpn

# Services
systemctl status jenkins
systemctl status docker

# Logs
journalctl -xe
tail -f /var/log/syslog
```

### Community Resources

- [Jenkins Documentation](https://www.jenkins.io/doc/)
- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Stack Overflow](https://stackoverflow.com/)
- [GitHub Issues](https://github.com/)

## Next Steps

Proceed to [Best Practices](10-best-practices.md) for optimization and security guidelines.
