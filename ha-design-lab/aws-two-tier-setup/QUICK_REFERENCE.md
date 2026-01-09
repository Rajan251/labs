# 🚀 Quick Reference - Two-Tier AWS Architecture

> **Quick commands and reference for managing your two-tier architecture**

---

## 📋 Table of Contents

1. [Terraform Commands](#terraform-commands)
2. [AWS CLI Commands](#aws-cli-commands)
3. [Monitoring Commands](#monitoring-commands)
4. [Troubleshooting](#troubleshooting)
5. [Useful URLs](#useful-urls)

---

## 🔧 Terraform Commands

### Initial Setup

```bash
# Navigate to environment directory
cd terraform/environments/dev

# Copy example variables
cp terraform.tfvars.example terraform.tfvars

# Edit variables (set your IP, passwords, etc.)
nano terraform.tfvars

# Set MongoDB passwords as environment variables
export TF_VAR_mongodb_admin_password="YourSecurePassword123!"
export TF_VAR_mongodb_app_password="AppPassword123!"

# Initialize Terraform
terraform init

# Validate configuration
terraform validate

# Plan deployment
terraform plan

# Apply (deploy infrastructure)
terraform apply

# Get outputs
terraform output

# Get specific output
terraform output alb_dns_name
```

### Updates and Changes

```bash
# Update infrastructure
terraform apply

# Update specific resource
terraform apply -target=module.autoscaling

# Destroy everything
terraform destroy

# Destroy specific resource
terraform destroy -target=module.database.aws_instance.mongodb_primary
```

---

## ☁️ AWS CLI Commands

### VPC and Networking

```bash
# List VPCs
aws ec2 describe-vpcs --filters "Name=tag:Project,Values=TwoTierArchitecture"

# List subnets
aws ec2 describe-subnets --filters "Name=tag:Project,Values=TwoTierArchitecture"

# List security groups
aws ec2 describe-security-groups --filters "Name=tag:Project,Values=TwoTierArchitecture"
```

### EC2 Instances

```bash
# List all instances
aws ec2 describe-instances \
  --filters "Name=tag:Project,Values=TwoTierArchitecture" \
  --query 'Reservations[].Instances[].[InstanceId,State.Name,Tags[?Key==`Name`].Value|[0],PrivateIpAddress,PublicIpAddress]' \
  --output table

# Get MongoDB instance IPs
aws ec2 describe-instances \
  --filters "Name=tag:Role,Values=database" \
  --query 'Reservations[].Instances[].[Tags[?Key==`Name`].Value|[0],PrivateIpAddress]' \
  --output table

# SSH to instance (via bastion)
ssh -i your-key.pem ec2-user@INSTANCE_IP
```

### Load Balancer

```bash
# Get ALB DNS name
aws elbv2 describe-load-balancers \
  --query 'LoadBalancers[?contains(LoadBalancerName, `two-tier`)].DNSName' \
  --output text

# Check target health
aws elbv2 describe-target-health \
  --target-group-arn $(aws elbv2 describe-target-groups \
    --query 'TargetGroups[?contains(TargetGroupName, `webapp`)].TargetGroupArn' \
    --output text)
```

### Auto-Scaling

```bash
# List ASG
aws autoscaling describe-auto-scaling-groups \
  --query 'AutoScalingGroups[?contains(AutoScalingGroupName, `webapp`)].{Name:AutoScalingGroupName,Min:MinSize,Max:MaxSize,Desired:DesiredCapacity,Current:Instances|length(@)}' \
  --output table

# Get ASG instances
aws autoscaling describe-auto-scaling-instances \
  --query 'AutoScalingInstances[?contains(AutoScalingGroupName, `webapp`)].[InstanceId,HealthStatus,LifecycleState]' \
  --output table

# Set desired capacity
aws autoscaling set-desired-capacity \
  --auto-scaling-group-name webapp-asg \
  --desired-capacity 4

# View scaling activities
aws autoscaling describe-scaling-activities \
  --auto-scaling-group-name webapp-asg \
  --max-records 10
```

---

## 📊 Monitoring Commands

### CloudWatch Metrics

```bash
# CPU Utilization (last hour)
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=AutoScalingGroupName,Value=dev-webapp-asg \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum \
  --output table

# ALB Request Count
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name RequestCount \
  --dimensions Name=LoadBalancer,Value=app/dev-two-tier-alb/xxx \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum \
  --output table

# List alarms
aws cloudwatch describe-alarms \
  --alarm-name-prefix dev-webapp \
  --query 'MetricAlarms[].[AlarmName,StateValue,MetricName]' \
  --output table
```

### Application Testing

```bash
# Get ALB DNS
ALB_DNS=$(terraform output -raw alb_dns_name)

# Test health endpoint
curl http://$ALB_DNS/health

# Test application
curl http://$ALB_DNS/

# Load test
ab -n 1000 -c 50 http://$ALB_DNS/

# Advanced load test
wrk -t12 -c400 -d30s http://$ALB_DNS/
```

---

## 🔍 Troubleshooting

### Check Application Logs

```bash
# SSH to instance
ssh -i your-key.pem ec2-user@INSTANCE_IP

# Check webapp service
sudo systemctl status webapp
sudo journalctl -u webapp -f

# Check NGINX
sudo systemctl status nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### MongoDB Troubleshooting

```bash
# Connect to MongoDB
mongosh "mongodb://MONGO_PRIMARY_IP:27017" \
  -u admin -p YourPassword --authenticationDatabase admin

# Check replica set status
rs.status()

# Check configuration
rs.conf()

# Check logs
sudo tail -f /var/log/mongodb/mongod.log
```

### Network Troubleshooting

```bash
# Test connectivity to MongoDB from app instance
nc -zv MONGO_PRIMARY_IP 27017

# Test ALB health check
curl -v http://localhost/health

# Check security group rules
aws ec2 describe-security-groups \
  --group-ids sg-xxx \
  --query 'SecurityGroups[].IpPermissions'
```

---

## 🌐 Useful URLs

### AWS Console

```
VPC Dashboard:
https://console.aws.amazon.com/vpc/

EC2 Dashboard:
https://console.aws.amazon.com/ec2/

Load Balancers:
https://console.aws.amazon.com/ec2/v2/home#LoadBalancers

Auto Scaling Groups:
https://console.aws.amazon.com/ec2/autoscaling/home#AutoScalingGroups

CloudWatch:
https://console.aws.amazon.com/cloudwatch/
```

### Application Endpoints

```bash
# Get from Terraform
terraform output application_url
terraform output health_check_url

# Or manually
http://YOUR-ALB-DNS-NAME/
http://YOUR-ALB-DNS-NAME/health
http://YOUR-ALB-DNS-NAME/api/items
```

---

## 📝 Common Tasks

### Scale Up/Down

```bash
# Manually scale
aws autoscaling set-desired-capacity \
  --auto-scaling-group-name dev-webapp-asg \
  --desired-capacity 5

# Update min/max
aws autoscaling update-auto-scaling-group \
  --auto-scaling-group-name dev-webapp-asg \
  --min-size 2 \
  --max-size 20
```

### Update Application Code

```bash
# Create new launch template version
# Update user data with new code
terraform apply

# Refresh instances
aws autoscaling start-instance-refresh \
  --auto-scaling-group-name dev-webapp-asg
```

### Backup MongoDB

```bash
# SSH to MongoDB primary
mongodump \
  --uri="mongodb://admin:Password@localhost:27017/?authSource=admin" \
  --out=/backup/$(date +%Y%m%d)

# Upload to S3
aws s3 cp /backup/$(date +%Y%m%d) s3://your-bucket/mongodb-backups/ --recursive
```

---

## 🎯 Quick Health Check

```bash
#!/bin/bash
# Save as health-check.sh

ALB_DNS=$(terraform output -raw alb_dns_name)

echo "=== Two-Tier Architecture Health Check ==="
echo ""

echo "1. ALB Health:"
curl -s http://$ALB_DNS/health | jq '.'
echo ""

echo "2. Target Health:"
TG_ARN=$(terraform output -raw target_group_arn)
aws elbv2 describe-target-health --target-group-arn $TG_ARN \
  --query 'TargetHealthDescriptions[].[Target.Id,TargetHealth.State]' \
  --output table
echo ""

echo "3. ASG Status:"
aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names dev-webapp-asg \
  --query 'AutoScalingGroups[0].{Desired:DesiredCapacity,Current:Instances|length(@),Healthy:Instances[?HealthStatus==`Healthy`]|length(@)}' \
  --output table
echo ""

echo "4. Recent Scaling Activities:"
aws autoscaling describe-scaling-activities \
  --auto-scaling-group-name dev-webapp-asg \
  --max-records 5 \
  --query 'Activities[].[StartTime,Description,StatusCode]' \
  --output table
```

---

## 📚 Documentation Links

- [Architecture Overview](./docs/00-ARCHITECTURE-OVERVIEW.md)
- [Infrastructure Setup](./docs/01-INFRASTRUCTURE-SETUP.md)
- [Database Setup](./docs/02-DATABASE-TIER-SETUP.md)
- [Web/App Setup](./docs/03-WEBAPP-TIER-SETUP.md)
- [Auto-Scaling](./docs/04-AUTOSCALING-SETUP.md)
- [Web UI Steps](./docs/05-WEB-UI-STEPS.md)
- [Testing](./docs/06-TESTING-VERIFICATION.md)

---

**Quick reference complete! 🚀**
