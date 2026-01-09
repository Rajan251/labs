# Troubleshooting Guide: PayFlow Solutions Infrastructure

## Common Terraform Errors

### 1. State Lock Errors

**Error:**
```
Error: Error acquiring the state lock

Error message: ConditionalCheckFailedException: The conditional request failed
Lock Info:
  ID:        abc123...
  Path:      payflow-terraform-state-prod/infrastructure/terraform.tfstate
  Operation: OperationTypeApply
  Who:       user@hostname
  Version:   1.6.0
  Created:   2024-01-08 10:30:00 UTC
```

**Cause:** Another Terraform process is running, or a previous run crashed without releasing the lock.

**Solution:**

```bash
# 1. Check if another process is actually running
ps aux | grep terraform

# 2. If no process is running, force unlock (use with caution!)
terraform force-unlock abc123

# 3. If that fails, manually delete from DynamoDB
aws dynamodb delete-item \
  --table-name terraform-state-lock \
  --key '{"LockID": {"S": "payflow-terraform-state-prod/infrastructure/terraform.tfstate-md5"}}'
```

**Prevention:**
- Always use `terraform plan` before `apply`
- Use CI/CD pipelines to serialize deployments
- Implement proper error handling in scripts

---

### 2. Resource Already Exists

**Error:**
```
Error: Error creating VPC: VpcLimitExceeded: The maximum number of VPCs has been reached.
```

**Cause:** AWS account limits reached, or resource already exists from previous deployment.

**Solution:**

```bash
# 1. Check current VPC count
aws ec2 describe-vpcs --query 'Vpcs[*].[VpcId,Tags[?Key==`Name`].Value|[0]]' --output table

# 2. Request limit increase (if needed)
aws service-quotas request-service-quota-increase \
  --service-code vpc \
  --quota-code L-F678F1CE \
  --desired-value 10

# 3. Import existing resource into state
terraform import aws_vpc.main vpc-abc123

# 4. Or delete unused VPCs
aws ec2 delete-vpc --vpc-id vpc-abc123
```

**Common Resource Limits:**
| Resource | Default Limit | How to Check |
|----------|--------------|--------------|
| VPCs | 5 per region | `aws ec2 describe-vpcs` |
| Elastic IPs | 5 per region | `aws ec2 describe-addresses` |
| Security Groups | 2,500 per VPC | `aws ec2 describe-security-groups` |
| NAT Gateways | 5 per AZ | `aws ec2 describe-nat-gateways` |

---

### 3. Dependency Errors

**Error:**
```
Error: Error creating Auto Scaling Group: ValidationError: You must use a valid fully-formed launch template
```

**Cause:** Resource dependencies not properly defined.

**Solution:**

```hcl
# Explicit dependency
resource "aws_autoscaling_group" "app" {
  # ...
  
  launch_template {
    id      = aws_launch_template.app.id
    version = "$Latest"
  }
  
  # Explicit dependency (if implicit doesn't work)
  depends_on = [
    aws_launch_template.app,
    aws_lb_target_group.app
  ]
}
```

**Debugging:**
```bash
# View dependency graph
terraform graph | dot -Tpng > graph.png

# Or use online viewer
terraform graph | pbcopy
# Paste into: https://dreampuf.github.io/GraphvizOnline/
```

---

### 4. Invalid CIDR Block

**Error:**
```
Error: Error creating subnet: InvalidSubnet.Range: The CIDR '10.0.1.0/24' conflicts with another subnet
```

**Cause:** Overlapping CIDR blocks or invalid subnet sizing.

**Solution:**

```hcl
# Use cidrsubnet function for automatic calculation
locals {
  vpc_cidr = "10.0.0.0/16"
  
  # Public subnets: 10.0.1.0/24, 10.0.2.0/24, 10.0.3.0/24
  public_subnets = [
    for i in range(3) : cidrsubnet(local.vpc_cidr, 8, i + 1)
  ]
  
  # Private subnets: 10.0.11.0/24, 10.0.12.0/24, 10.0.13.0/24
  private_subnets = [
    for i in range(3) : cidrsubnet(local.vpc_cidr, 8, i + 11)
  ]
}
```

**CIDR Planning Tool:**
```bash
# Install ipcalc
sudo apt-get install ipcalc  # Ubuntu/Debian
brew install ipcalc          # macOS

# Calculate subnets
ipcalc 10.0.0.0/16 -s 256 256 256
```

---

### 5. Timeout Errors

**Error:**
```
Error: timeout while waiting for state to become 'available' (last state: 'pending', timeout: 10m0s)
```

**Cause:** Resource creation taking longer than expected (common with RDS, NAT Gateway).

**Solution:**

```hcl
# Increase timeout
resource "aws_db_instance" "main" {
  # ...
  
  timeouts {
    create = "60m"
    update = "60m"
    delete = "60m"
  }
}

# For NAT Gateway
resource "aws_nat_gateway" "main" {
  # ...
  
  timeouts {
    create = "10m"
    delete = "30m"
  }
}
```

**Typical Creation Times:**
| Resource | Typical Time | Max Timeout |
|----------|-------------|-------------|
| VPC | < 1 minute | 5 minutes |
| Subnet | < 1 minute | 5 minutes |
| NAT Gateway | 2-5 minutes | 10 minutes |
| RDS (Multi-AZ) | 10-20 minutes | 60 minutes |
| ALB | 2-5 minutes | 10 minutes |
| EC2 Instance | 1-3 minutes | 10 minutes |

---

### 6. Permission Denied Errors

**Error:**
```
Error: Error creating VPC: UnauthorizedOperation: You are not authorized to perform this operation.
```

**Cause:** Insufficient IAM permissions.

**Solution:**

```bash
# 1. Check current IAM user/role
aws sts get-caller-identity

# 2. Check attached policies
aws iam list-attached-user-policies --user-name your-username

# 3. Simulate policy
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::ACCOUNT:user/your-username \
  --action-names ec2:CreateVpc \
  --resource-arns "*"

# 4. Enable CloudTrail to see denied actions
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=CreateVpc \
  --max-results 10
```

**Required IAM Permissions for Terraform:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:*",
        "elasticloadbalancing:*",
        "autoscaling:*",
        "rds:*",
        "s3:*",
        "iam:*",
        "cloudwatch:*",
        "sns:*",
        "secretsmanager:*"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## AWS Resource Verification

### VPC and Networking

```bash
# List VPCs
aws ec2 describe-vpcs \
  --filters "Name=tag:Project,Values=payflow-platform" \
  --query 'Vpcs[*].[VpcId,CidrBlock,Tags[?Key==`Name`].Value|[0]]' \
  --output table

# List Subnets
aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=vpc-abc123" \
  --query 'Subnets[*].[SubnetId,CidrBlock,AvailabilityZone,Tags[?Key==`Name`].Value|[0]]' \
  --output table

# Check Route Tables
aws ec2 describe-route-tables \
  --filters "Name=vpc-id,Values=vpc-abc123" \
  --query 'RouteTables[*].Routes' \
  --output table

# Verify NAT Gateways
aws ec2 describe-nat-gateways \
  --filter "Name=vpc-id,Values=vpc-abc123" \
  --query 'NatGateways[*].[NatGatewayId,State,SubnetId]' \
  --output table

# Check Internet Gateway
aws ec2 describe-internet-gateways \
  --filters "Name=attachment.vpc-id,Values=vpc-abc123" \
  --output table
```

### Security Groups

```bash
# List Security Groups
aws ec2 describe-security-groups \
  --filters "Name=vpc-id,Values=vpc-abc123" \
  --query 'SecurityGroups[*].[GroupId,GroupName,Description]' \
  --output table

# Check specific Security Group rules
aws ec2 describe-security-groups \
  --group-ids sg-abc123 \
  --query 'SecurityGroups[0].IpPermissions' \
  --output json

# Find Security Groups with 0.0.0.0/0 access
aws ec2 describe-security-groups \
  --filters "Name=ip-permission.cidr,Values=0.0.0.0/0" \
  --query 'SecurityGroups[*].[GroupId,GroupName]' \
  --output table
```

### EC2 and Auto Scaling

```bash
# List EC2 Instances
aws ec2 describe-instances \
  --filters "Name=tag:Project,Values=payflow-platform" \
  --query 'Reservations[*].Instances[*].[InstanceId,State.Name,PrivateIpAddress,Tags[?Key==`Name`].Value|[0]]' \
  --output table

# Check Auto Scaling Groups
aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names payflow-asg-app-prod \
  --query 'AutoScalingGroups[*].[AutoScalingGroupName,DesiredCapacity,MinSize,MaxSize,Instances[*].InstanceId]' \
  --output table

# View Scaling Activities
aws autoscaling describe-scaling-activities \
  --auto-scaling-group-name payflow-asg-app-prod \
  --max-records 10 \
  --output table

# Check Launch Template
aws ec2 describe-launch-templates \
  --launch-template-names payflow-lt-app-prod \
  --output json
```

### Load Balancer

```bash
# List Load Balancers
aws elbv2 describe-load-balancers \
  --query 'LoadBalancers[*].[LoadBalancerName,DNSName,State.Code]' \
  --output table

# Check Target Groups
aws elbv2 describe-target-groups \
  --query 'TargetGroups[*].[TargetGroupName,Protocol,Port,HealthCheckPath]' \
  --output table

# View Target Health
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:us-east-1:ACCOUNT:targetgroup/payflow-tg-app-prod/abc123 \
  --query 'TargetHealthDescriptions[*].[Target.Id,TargetHealth.State,TargetHealth.Reason]' \
  --output table

# Check Listeners
aws elbv2 describe-listeners \
  --load-balancer-arn arn:aws:elasticloadbalancing:us-east-1:ACCOUNT:loadbalancer/app/payflow-alb-prod/abc123 \
  --output table
```

### RDS Database

```bash
# List RDS Instances
aws rds describe-db-instances \
  --query 'DBInstances[*].[DBInstanceIdentifier,DBInstanceStatus,Engine,MultiAZ,Endpoint.Address]' \
  --output table

# Check specific database
aws rds describe-db-instances \
  --db-instance-identifier payflow-rds-postgres-prod \
  --output json

# View automated backups
aws rds describe-db-snapshots \
  --db-instance-identifier payflow-rds-postgres-prod \
  --snapshot-type automated \
  --output table

# Check parameter groups
aws rds describe-db-parameters \
  --db-parameter-group-name payflow-pg-postgres15 \
  --query 'Parameters[?ParameterName==`rds.force_ssl`]' \
  --output table
```

### CloudWatch Monitoring

```bash
# List CloudWatch Alarms
aws cloudwatch describe-alarms \
  --alarm-name-prefix payflow \
  --query 'MetricAlarms[*].[AlarmName,StateValue,MetricName]' \
  --output table

# Get metric statistics (CPU)
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=AutoScalingGroupName,Value=payflow-asg-app-prod \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average \
  --output table

# View recent alarm history
aws cloudwatch describe-alarm-history \
  --alarm-name payflow-alarm-cpu-high \
  --max-records 10 \
  --output table
```

---

## Terraform Debugging

### Enable Debug Logging

```bash
# Set environment variables
export TF_LOG=DEBUG
export TF_LOG_PATH=terraform-debug.log

# Run Terraform
terraform plan

# View logs
tail -f terraform-debug.log

# Disable logging
unset TF_LOG
unset TF_LOG_PATH
```

**Log Levels:**
- `TRACE` - Most verbose
- `DEBUG` - Detailed debugging
- `INFO` - General information
- `WARN` - Warnings
- `ERROR` - Errors only

### Validate Configuration

```bash
# Check syntax
terraform validate

# Format code
terraform fmt -recursive

# Show plan in detail
terraform plan -out=tfplan
terraform show tfplan

# Show current state
terraform show

# List resources in state
terraform state list

# Show specific resource
terraform state show aws_vpc.main
```

### Refresh State

```bash
# Refresh state from AWS
terraform refresh

# Import existing resource
terraform import aws_instance.app i-abc123

# Remove resource from state (doesn't delete in AWS)
terraform state rm aws_instance.app

# Move resource in state
terraform state mv aws_instance.app aws_instance.app_new
```

---

## Common Application Issues

### 1. Cannot Connect to Database

**Symptoms:**
- Application logs show "connection refused" or "timeout"
- Health checks failing

**Debugging:**

```bash
# 1. Check RDS endpoint
aws rds describe-db-instances \
  --db-instance-identifier payflow-rds-postgres-prod \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text

# 2. Test from EC2 instance
aws ssm start-session --target i-abc123

# Inside EC2 instance:
sudo yum install postgresql15 -y
psql -h payflow-rds-postgres-prod.abc123.us-east-1.rds.amazonaws.com -U admin -d payflow

# 3. Check security group
aws ec2 describe-security-groups \
  --group-ids sg-db123 \
  --query 'SecurityGroups[0].IpPermissions'

# 4. Verify secret in Secrets Manager
aws secretsmanager get-secret-value \
  --secret-id payflow/prod/db-password \
  --query 'SecretString' \
  --output text
```

### 2. ALB Returns 502/503 Errors

**Symptoms:**
- ALB health checks failing
- Intermittent 502 Bad Gateway or 503 Service Unavailable

**Debugging:**

```bash
# 1. Check target health
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:... \
  --output table

# 2. Check application logs
aws logs tail /aws/ec2/payflow-app --follow

# 3. Test application directly (from bastion)
curl http://10.0.11.5:8080/health

# 4. Check security group (ALB → App)
aws ec2 describe-security-groups --group-ids sg-app123

# 5. Verify health check settings
aws elbv2 describe-target-groups \
  --target-group-arns arn:aws:elasticloadbalancing:... \
  --query 'TargetGroups[0].HealthCheckPath'
```

### 3. Auto Scaling Not Working

**Symptoms:**
- Instances not scaling up during high load
- Instances not scaling down during low load

**Debugging:**

```bash
# 1. Check scaling policies
aws autoscaling describe-policies \
  --auto-scaling-group-name payflow-asg-app-prod \
  --output table

# 2. View scaling activities
aws autoscaling describe-scaling-activities \
  --auto-scaling-group-name payflow-asg-app-prod \
  --max-records 20 \
  --output table

# 3. Check CloudWatch alarms
aws cloudwatch describe-alarms \
  --alarm-names payflow-alarm-cpu-high \
  --output json

# 4. View current metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=AutoScalingGroupName,Value=payflow-asg-app-prod \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average

# 5. Manually trigger scaling (for testing)
aws autoscaling set-desired-capacity \
  --auto-scaling-group-name payflow-asg-app-prod \
  --desired-capacity 5
```

---

## Performance Issues

### High Latency

**Checklist:**
1. Check ALB response time metrics
2. Review application logs for slow queries
3. Check database performance (CPU, IOPS)
4. Verify NAT Gateway not bottlenecked
5. Check for network ACL misconfigurations

```bash
# ALB metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name TargetResponseTime \
  --dimensions Name=LoadBalancer,Value=app/payflow-alb-prod/abc123 \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum

# RDS metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnections \
  --dimensions Name=DBInstanceIdentifier,Value=payflow-rds-postgres-prod \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum
```

---

## Disaster Recovery Testing

### Simulate Instance Failure

```bash
# Terminate instance (ASG will replace)
aws ec2 terminate-instances --instance-ids i-abc123

# Watch ASG launch replacement
watch -n 5 'aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names payflow-asg-app-prod \
  --query "AutoScalingGroups[0].Instances[*].[InstanceId,LifecycleState]" \
  --output table'
```

### Simulate AZ Failure

```bash
# Suspend processes in one AZ (simulation)
aws autoscaling suspend-processes \
  --auto-scaling-group-name payflow-asg-app-prod \
  --scaling-processes Launch

# Terminate all instances in one AZ
aws ec2 describe-instances \
  --filters "Name=tag:aws:autoscaling:groupName,Values=payflow-asg-app-prod" \
            "Name=availability-zone,Values=us-east-1a" \
  --query 'Reservations[*].Instances[*].InstanceId' \
  --output text | xargs aws ec2 terminate-instances --instance-ids

# Resume processes
aws autoscaling resume-processes \
  --auto-scaling-group-name payflow-asg-app-prod
```

### Test RDS Failover

```bash
# Initiate manual failover
aws rds reboot-db-instance \
  --db-instance-identifier payflow-rds-postgres-prod \
  --force-failover

# Monitor failover
watch -n 5 'aws rds describe-db-instances \
  --db-instance-identifier payflow-rds-postgres-prod \
  --query "DBInstances[0].[DBInstanceStatus,AvailabilityZone]" \
  --output table'
```

---

## Cost Troubleshooting

### Identify Cost Drivers

```bash
# Enable Cost Explorer API
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=SERVICE

# Check for unattached resources
# Unattached EBS volumes
aws ec2 describe-volumes \
  --filters "Name=status,Values=available" \
  --query 'Volumes[*].[VolumeId,Size,VolumeType]' \
  --output table

# Unattached Elastic IPs
aws ec2 describe-addresses \
  --query 'Addresses[?AssociationId==null].[PublicIp,AllocationId]' \
  --output table

# Idle NAT Gateways (check CloudWatch metrics)
aws cloudwatch get-metric-statistics \
  --namespace AWS/NATGateway \
  --metric-name BytesOutToDestination \
  --dimensions Name=NatGatewayId,Value=nat-abc123 \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 \
  --statistics Sum
```

---

## Emergency Procedures

### Rollback Terraform Changes

```bash
# 1. View state history
terraform state pull > current-state.json

# 2. Download previous state from S3
aws s3api list-object-versions \
  --bucket payflow-terraform-state-prod \
  --prefix infrastructure/terraform.tfstate

# 3. Restore previous version
aws s3api get-object \
  --bucket payflow-terraform-state-prod \
  --key infrastructure/terraform.tfstate \
  --version-id VERSION_ID \
  previous-state.json

# 4. Push to Terraform
terraform state push previous-state.json

# 5. Re-plan and apply
terraform plan
terraform apply
```

### Complete Infrastructure Teardown

```bash
# WARNING: This will destroy EVERYTHING

# 1. Disable deletion protection (if enabled)
aws rds modify-db-instance \
  --db-instance-identifier payflow-rds-postgres-prod \
  --no-deletion-protection

# 2. Destroy infrastructure
terraform destroy -auto-approve

# 3. Clean up state bucket (optional)
aws s3 rm s3://payflow-terraform-state-prod --recursive
aws s3 rb s3://payflow-terraform-state-prod
```

---

## Getting Help

### Terraform Community
- [Terraform Discuss](https://discuss.hashicorp.com/)
- [Terraform GitHub Issues](https://github.com/hashicorp/terraform/issues)

### AWS Support
```bash
# Create support case
aws support create-case \
  --subject "RDS Performance Issue" \
  --service-code "amazon-rds" \
  --severity-code "normal" \
  --category-code "performance" \
  --communication-body "Detailed description..."
```

### Internal Escalation
1. Check runbooks in `docs/runbooks/`
2. Review CloudWatch dashboards
3. Check #devops Slack channel
4. Page on-call engineer (PagerDuty)
5. Escalate to senior DevOps lead

---

## Next Steps

- Review [Use Cases & Scenarios](use-cases.md)
- Practice [Lab 01: VPC Networking](../labs/01-vpc-networking/README.md)
