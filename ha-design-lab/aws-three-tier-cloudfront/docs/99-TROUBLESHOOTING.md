# Troubleshooting Guide

## Common Issues and Solutions

### VPC and Networking

#### Issue: Cannot create VPC
**Symptoms**: Error when creating VPC
**Causes**:
- VPC limit reached (default: 5 per region)
- Invalid CIDR block

**Solutions**:
```bash
# Check VPC limit
aws ec2 describe-account-attributes --attribute-names max-vpcs

# Request limit increase via AWS Support
```

#### Issue: Subnet CIDR conflicts
**Symptoms**: Error creating subnet
**Causes**: Overlapping CIDR blocks

**Solutions**:
- Ensure subnet CIDRs are within VPC CIDR
- Use non-overlapping ranges
- Use CIDR calculator: `10.0.0.0/16` → subnets `/24`

#### Issue: NAT Gateway not working
**Symptoms**: Private instances cannot access internet
**Diagnostics**:
```bash
# Check NAT Gateway status
aws ec2 describe-nat-gateways --filter "Name=state,Values=available"

# Check route table
aws ec2 describe-route-tables --route-table-ids rtb-xxxxx
```

**Solutions**:
- Verify NAT Gateway is in public subnet
- Check route table has `0.0.0.0/0` → NAT Gateway
- Verify Elastic IP is attached
- Check Security Groups allow outbound traffic

### Security Groups

#### Issue: Cannot SSH to instances
**Symptoms**: Connection timeout
**Diagnostics**:
```bash
# Check security group rules
aws ec2 describe-security-groups --group-ids sg-xxxxx

# Test connectivity
nc -zv <instance-ip> 22
```

**Solutions**:
- Add inbound rule: SSH (22) from your IP
- Verify instance is in correct subnet
- Check NACL rules
- Verify key pair is correct

#### Issue: ALB cannot reach instances
**Symptoms**: Unhealthy targets
**Diagnostics**:
```bash
# Check target health
aws elbv2 describe-target-health --target-group-arn <arn>
```

**Solutions**:
- Verify app security group allows traffic from ALB SG
- Check application is running on correct port
- Verify health check path is correct
- Check instance subnet routing

### Auto Scaling

#### Issue: Instances not launching
**Symptoms**: Desired capacity not met
**Diagnostics**:
```bash
# Check ASG activity
aws autoscaling describe-scaling-activities \
  --auto-scaling-group-name <asg-name> \
  --max-records 10
```

**Solutions**:
- Check launch template is valid
- Verify AMI exists and is accessible
- Check instance limits (vCPU, instance count)
- Verify IAM instance profile exists
- Check subnet has available IPs

#### Issue: Scaling not triggered
**Symptoms**: No scaling despite high CPU
**Diagnostics**:
```bash
# Check CloudWatch alarms
aws cloudwatch describe-alarms --alarm-names <alarm-name>

# Check alarm state
aws cloudwatch describe-alarm-history --alarm-name <alarm-name>
```

**Solutions**:
- Verify CloudWatch alarms are configured
- Check alarm thresholds and evaluation periods
- Verify scaling policies are attached
- Check cooldown periods

### Load Balancer

#### Issue: ALB returns 502/503 errors
**Symptoms**: Bad Gateway errors
**Diagnostics**:
```bash
# Check target health
aws elbv2 describe-target-health --target-group-arn <arn>

# Check ALB access logs
aws s3 ls s3://alb-logs-bucket/AWSLogs/
```

**Solutions**:
- Verify targets are healthy
- Check application is responding
- Increase health check interval
- Check security group rules
- Verify target deregistration delay

#### Issue: Health checks failing
**Symptoms**: Targets marked unhealthy
**Diagnostics**:
```bash
# Test health check endpoint
curl http://<instance-ip>:<port>/health
```

**Solutions**:
- Verify health check path exists
- Check application returns 200 status
- Adjust health check timeout/interval
- Check security group allows health check traffic

### CloudFront

#### Issue: 403 Forbidden errors
**Symptoms**: Access denied from CloudFront
**Diagnostics**:
```bash
# Check S3 bucket policy
aws s3api get-bucket-policy --bucket <bucket-name>

# Test direct S3 access
aws s3 ls s3://<bucket-name>/
```

**Solutions**:
- Update S3 bucket policy for CloudFront OAC
- Verify Origin Access Control is configured
- Check object permissions in S3
- Verify CloudFront distribution is deployed

#### Issue: Stale content served
**Symptoms**: Old content displayed
**Solutions**:
```bash
# Create invalidation
aws cloudfront create-invalidation \
  --distribution-id <id> \
  --paths "/*"

# Check invalidation status
aws cloudfront get-invalidation \
  --distribution-id <id> \
  --id <invalidation-id>
```

### Database (MongoDB)

#### Issue: Cannot connect to database
**Symptoms**: Connection timeout
**Diagnostics**:
```bash
# Test connectivity from app server
nc -zv <db-ip> 27017

# Check MongoDB status
sudo systemctl status mongod
```

**Solutions**:
- Verify DB security group allows app server SG
- Check MongoDB is listening on correct port
- Verify MongoDB bind IP is `0.0.0.0`
- Check NACL rules

#### Issue: Replica set not initializing
**Symptoms**: Replica set status shows errors
**Diagnostics**:
```bash
# Check replica set status
mongosh --eval "rs.status()"

# Check MongoDB logs
sudo tail -f /var/log/mongodb/mongod.log
```

**Solutions**:
- Verify all members can communicate
- Check hostnames are resolvable
- Ensure clocks are synchronized
- Verify replica set configuration

### VPN

#### Issue: Cannot connect to VPN
**Symptoms**: VPN connection fails
**Diagnostics**:
```bash
# Check VPN server status
ssh ec2-user@<vpn-ip> "sudo systemctl status openvpn@server"

# Check VPN logs
ssh ec2-user@<vpn-ip> "sudo tail -f /var/log/openvpn.log"
```

**Solutions**:
- Verify VPN security group allows UDP 1194
- Check OpenVPN service is running
- Verify client configuration is correct
- Check firewall rules on VPN server

### Terraform

#### Issue: Terraform apply fails
**Symptoms**: Error during apply
**Diagnostics**:
```bash
# Enable debug logging
export TF_LOG=DEBUG
terraform apply

# Validate configuration
terraform validate

# Check state
terraform show
```

**Solutions**:
- Check AWS credentials are valid
- Verify required variables are set
- Check for resource dependencies
- Review error message for specific issue
- Try `terraform refresh` and retry

#### Issue: State lock error
**Symptoms**: "Error acquiring the state lock"
**Solutions**:
```bash
# Force unlock (use with caution)
terraform force-unlock <lock-id>

# Or wait for lock to expire
```

### Monitoring

#### Issue: CloudWatch alarms not triggering
**Symptoms**: No notifications despite threshold breach
**Diagnostics**:
```bash
# Check alarm configuration
aws cloudwatch describe-alarms --alarm-names <alarm-name>

# Check SNS subscription
aws sns list-subscriptions-by-topic --topic-arn <arn>
```

**Solutions**:
- Verify alarm is enabled
- Check SNS topic subscription is confirmed
- Verify email subscription is confirmed
- Check alarm evaluation periods and datapoints

#### Issue: No metrics in CloudWatch
**Symptoms**: Missing metrics
**Solutions**:
- Verify CloudWatch agent is installed
- Check IAM role has CloudWatch permissions
- Verify agent configuration is correct
- Check agent is running: `sudo systemctl status amazon-cloudwatch-agent`

## Debugging Commands

### Network Debugging

```bash
# Test connectivity
ping <ip>
nc -zv <ip> <port>
telnet <ip> <port>

# DNS resolution
nslookup <domain>
dig <domain>

# Trace route
traceroute <ip>

# Check open ports
sudo netstat -tlnp
sudo ss -tlnp

# Check firewall
sudo iptables -L -n -v
```

### AWS CLI Debugging

```bash
# Describe instance
aws ec2 describe-instances --instance-ids i-xxxxx

# Check security groups
aws ec2 describe-security-groups --group-ids sg-xxxxx

# View VPC flow logs
aws ec2 describe-flow-logs

# Check CloudWatch logs
aws logs tail /aws/vpc/three-tier-app-dev --follow
```

### Application Debugging

```bash
# Check application logs
sudo journalctl -u app.service -f

# Check system resources
top
htop
free -h
df -h

# Check disk I/O
iostat -x 1

# Check network connections
sudo netstat -anp | grep ESTABLISHED
```

## Getting Help

### AWS Support

1. **AWS Support Console**: https://console.aws.amazon.com/support
2. **AWS Forums**: https://forums.aws.amazon.com
3. **AWS re:Post**: https://repost.aws

### Documentation

- [AWS VPC Documentation](https://docs.aws.amazon.com/vpc/)
- [AWS EC2 Documentation](https://docs.aws.amazon.com/ec2/)
- [AWS CloudFront Documentation](https://docs.aws.amazon.com/cloudfront/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

### Logs Location

- **VPC Flow Logs**: CloudWatch Logs `/aws/vpc/<name>`
- **ALB Access Logs**: S3 bucket
- **CloudTrail**: S3 bucket
- **Application Logs**: `/var/log/app/`
- **MongoDB Logs**: `/var/log/mongodb/mongod.log`
- **OpenVPN Logs**: `/var/log/openvpn.log`

## Prevention Best Practices

1. **Use Infrastructure as Code**: Terraform for reproducibility
2. **Enable Logging**: VPC Flow Logs, CloudTrail, ALB logs
3. **Set Up Monitoring**: CloudWatch alarms for critical metrics
4. **Test in Dev First**: Always test changes in dev environment
5. **Document Changes**: Keep runbooks updated
6. **Regular Backups**: Automated snapshots for databases
7. **Security Audits**: Regular security group reviews
8. **Cost Monitoring**: Set up billing alerts
