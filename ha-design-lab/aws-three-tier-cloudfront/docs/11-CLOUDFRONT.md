# CloudFront CDN Setup Guide

## Overview

This guide covers setting up Amazon CloudFront as a Content Delivery Network (CDN) for global content delivery with low latency.

## Architecture

CloudFront distribution with:
- **S3 Origin**: Static content (images, CSS, JS)
- **ALB Origin**: Dynamic content (API endpoints)
- **Cache Behaviors**: Different caching for static vs dynamic
- **SSL/TLS**: HTTPS encryption
- **Global Edge Locations**: Low-latency worldwide

## Prerequisites

- S3 bucket created
- Application Load Balancer deployed
- (Optional) ACM certificate in us-east-1 region

## Web Console Setup

### Step 1: Create CloudFront Distribution

1. Navigate to **CloudFront** in AWS Console
2. Click **Create Distribution**

### Step 2: Configure Origins

#### Origin 1: S3 Bucket

1. **Origin Settings**:
   - **Origin domain**: Select your S3 bucket
   - **Origin path**: Leave empty
   - **Name**: `S3-three-tier-app-dev-static-content`
   - **Origin access**: Origin access control settings (recommended)
   
2. **Create OAC**:
   - Click **Create control setting**
   - **Name**: `three-tier-app-oac`
   - **Signing behavior**: Sign requests
   - Click **Create**

3. **S3 bucket policy**: Copy the policy shown and update your S3 bucket policy

#### Origin 2: Application Load Balancer

1. Click **Create origin**
2. **Origin Settings**:
   - **Origin domain**: Select your ALB DNS name
   - **Protocol**: HTTP only
   - **HTTP port**: 80
   - **Name**: `ALB-three-tier-app`
   - **Origin SSL protocols**: TLSv1.2

### Step 3: Configure Default Cache Behavior (S3)

1. **Path pattern**: Default (*)
2. **Viewer protocol policy**: Redirect HTTP to HTTPS
3. **Allowed HTTP methods**: GET, HEAD, OPTIONS
4. **Cache policy**: CachingOptimized
5. **Origin request policy**: None
6. **Compress objects**: Yes

### Step 4: Add Cache Behavior for Dynamic Content

1. Click **Create behavior**
2. **Path pattern**: `/api/*`
3. **Origin**: Select ALB origin
4. **Viewer protocol policy**: Redirect HTTP to HTTPS
5. **Allowed HTTP methods**: GET, HEAD, OPTIONS, PUT, POST, PATCH, DELETE
6. **Cache policy**: CachingDisabled
7. **Origin request policy**: AllViewer
8. **Compress objects**: Yes

### Step 5: Configure Distribution Settings

1. **Price class**: Use all edge locations (or select based on budget)
2. **Alternate domain names (CNAMEs)**: Add your domain (optional)
3. **Custom SSL certificate**: Select ACM certificate (optional)
4. **Default root object**: `index.html`
5. **Standard logging**: On (optional)
6. **IPv6**: On

### Step 6: Create Distribution

1. Review all settings
2. Click **Create distribution**
3. Wait for deployment (15-20 minutes)

## Terraform Setup

CloudFront is automatically created using the CDN module:

```hcl
module "cdn" {
  source = "../../modules/cdn"

  project_name        = "three-tier-app"
  environment         = "dev"
  alb_dns_name        = module.loadbalancer.alb_dns_name
  price_class         = "PriceClass_100"
  domain_aliases      = ["www.example.com"]
  ssl_certificate_arn = "arn:aws:acm:us-east-1:..."
}
```

### Deploy with Terraform

```bash
cd terraform/environments/dev
terraform apply
```

## Update S3 Bucket Policy

After creating the distribution, update your S3 bucket policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowCloudFrontOAI",
      "Effect": "Allow",
      "Principal": {
        "Service": "cloudfront.amazonaws.com"
      },
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::your-bucket-name/*",
      "Condition": {
        "StringEquals": {
          "AWS:SourceArn": "arn:aws:cloudfront::ACCOUNT-ID:distribution/DISTRIBUTION-ID"
        }
      }
    }
  ]
}
```

## Upload Static Content

```bash
# Upload files to S3
aws s3 sync ./static-content s3://three-tier-app-dev-static-content/

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id E1234567890ABC \
  --paths "/*"
```

## Testing

### Test Static Content

```bash
# Access via CloudFront
curl https://d1234567890abc.cloudfront.net/index.html

# Should return your static content
```

### Test Dynamic Content

```bash
# Access API via CloudFront
curl https://d1234567890abc.cloudfront.net/api/health

# Should return response from ALB
```

### Test Cache Headers

```bash
# Check cache status
curl -I https://d1234567890abc.cloudfront.net/image.jpg

# Look for headers:
# X-Cache: Hit from cloudfront (cached)
# X-Cache: Miss from cloudfront (not cached)
```

## Verification

### Console Verification

1. Go to **CloudFront** → **Distributions**
2. Verify status is "Deployed"
3. Check **Origins** tab - should see S3 and ALB
4. Check **Behaviors** tab - should see default and /api/*
5. Test distribution domain name

### CLI Verification

```bash
# Get distribution details
aws cloudfront get-distribution --id E1234567890ABC

# List distributions
aws cloudfront list-distributions

# Check distribution status
aws cloudfront get-distribution --id E1234567890ABC \
  --query 'Distribution.Status' --output text
```

### Terraform Verification

```bash
terraform output cloudfront_domain_name
terraform output cloudfront_distribution_id
```

## Performance Optimization

### Cache Settings

1. **Static Content**: Cache for 24 hours (86400 seconds)
2. **Dynamic Content**: No caching or short TTL (300 seconds)
3. **Images**: Cache for 7 days (604800 seconds)

### Compression

Enable compression for:
- HTML, CSS, JavaScript
- JSON, XML
- SVG images

### HTTP/2 and HTTP/3

- HTTP/2: Enabled by default
- HTTP/3: Enable in distribution settings

## Security Best Practices

1. **HTTPS Only**: Redirect HTTP to HTTPS
2. **OAC**: Use Origin Access Control for S3
3. **WAF**: Add AWS WAF for application protection
4. **Geo Restriction**: Enable if needed
5. **Signed URLs**: For private content

## Cost Optimization

1. **Price Class**: Use PriceClass_100 for dev (US, Canada, Europe)
2. **Cache Effectively**: Reduce origin requests
3. **Compression**: Reduce data transfer
4. **Invalidations**: Minimize (first 1000/month free)

## Monitoring

### CloudWatch Metrics

- **Requests**: Total requests
- **BytesDownloaded**: Data transfer
- **ErrorRate**: 4xx and 5xx errors
- **CacheHitRate**: Cache efficiency

### Create Alarms

```bash
# High error rate alarm
aws cloudwatch put-metric-alarm \
  --alarm-name cloudfront-high-errors \
  --metric-name 4xxErrorRate \
  --namespace AWS/CloudFront \
  --statistic Average \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
```

## Troubleshooting

### Issue: 403 Forbidden from S3
**Solution**: Check S3 bucket policy allows CloudFront OAC

### Issue: Stale content served
**Solution**: Create invalidation or wait for TTL expiration

### Issue: High latency
**Solution**: Check cache hit rate, optimize cache behaviors

### Issue: SSL certificate error
**Solution**: Ensure ACM certificate is in us-east-1 region

## Custom Domain Setup

1. **Create ACM Certificate** in us-east-1:
   ```bash
   aws acm request-certificate \
     --domain-name www.example.com \
     --validation-method DNS \
     --region us-east-1
   ```

2. **Add CNAME to Distribution**:
   - Alternate domain names: `www.example.com`
   - Custom SSL certificate: Select your ACM certificate

3. **Update Route 53**:
   - Create A record (Alias) pointing to CloudFront

## Cache Invalidation

### Invalidate All

```bash
aws cloudfront create-invalidation \
  --distribution-id E1234567890ABC \
  --paths "/*"
```

### Invalidate Specific Paths

```bash
aws cloudfront create-invalidation \
  --distribution-id E1234567890ABC \
  --paths "/images/*" "/css/*"
```

## Best Practices

1. **Use versioned filenames**: `app.v1.2.3.js` instead of `app.js`
2. **Set appropriate TTLs**: Long for static, short for dynamic
3. **Enable compression**: Reduce bandwidth costs
4. **Monitor cache hit rate**: Aim for >80%
5. **Use signed URLs**: For private content

## Next Steps

- [Route 53 DNS Setup](12-ROUTE53.md)
- [CloudWatch Monitoring](13-CLOUDWATCH.md)
- [S3 Bucket Configuration](10-S3-BUCKET.md)
