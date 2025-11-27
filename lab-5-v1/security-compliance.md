## 8. Security & Compliance

### 8.1 Security Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS                               │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Layer 7: Governance & Compliance                        │   │
│  │  • Policy enforcement • Audit logging • Compliance       │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Layer 6: Identity & Access Management                   │   │
│  │  • SSO • MFA • RBAC • Service accounts                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Layer 5: Data Protection                                │   │
│  │  • Encryption at rest • Encryption in transit • KMS      │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Layer 4: Application Security                           │   │
│  │  • WAF • API Gateway • Rate limiting • Input validation  │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Layer 3: Network Security                               │   │
│  │  • VPC isolation • Security groups • NACLs • Firewalls   │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Layer 2: Infrastructure Security                        │   │
│  │  • Patch management • Hardening • Vulnerability scanning │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Layer 1: Physical & Environmental                       │   │
│  │  • Cloud provider security • Compliance certifications   │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 Encryption Standards

#### Encryption at Rest

**AWS KMS Configuration:**

```hcl
# terraform/security/kms.tf
resource "aws_kms_key" "dr_encryption" {
  description             = "DR infrastructure encryption key"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  multi_region            = true  # Critical for DR

  tags = {
    Name        = "dr-encryption-key"
    Environment = "production"
  }
}

resource "aws_kms_alias" "dr_encryption" {
  name          = "alias/dr-encryption"
  target_key_id = aws_kms_key.dr_encryption.key_id
}

# Grant access to services
resource "aws_kms_grant" "rds" {
  name              = "rds-encryption-grant"
  key_id            = aws_kms_key.dr_encryption.key_id
  grantee_principal = "rds.amazonaws.com"
  operations        = ["Encrypt", "Decrypt", "GenerateDataKey"]
}

resource "aws_kms_grant" "s3" {
  name              = "s3-encryption-grant"
  key_id            = aws_kms_key.dr_encryption.key_id
  grantee_principal = "s3.amazonaws.com"
  operations        = ["Encrypt", "Decrypt", "GenerateDataKey"]
}
```

**Azure Key Vault:**

```bash
# Create Key Vault
az keyvault create \
  --name prod-dr-keyvault \
  --resource-group prod-rg-eastus \
  --location eastus \
  --enabled-for-disk-encryption true \
  --enabled-for-deployment true \
  --enabled-for-template-deployment true \
  --enable-soft-delete true \
  --soft-delete-retention-days 90 \
  --enable-purge-protection true

# Create encryption key
az keyvault key create \
  --vault-name prod-dr-keyvault \
  --name dr-encryption-key \
  --protection software \
  --size 4096 \
  --ops encrypt decrypt wrapKey unwrapKey

# Enable automatic key rotation
az keyvault key rotation-policy update \
  --vault-name prod-dr-keyvault \
  --name dr-encryption-key \
  --value '{
    "lifetimeActions": [{
      "trigger": {"timeAfterCreate": "P90D"},
      "action": {"type": "Rotate"}
    }],
    "attributes": {"expiryTime": "P2Y"}
  }'
```

**GCP KMS:**

```bash
# Create key ring
gcloud kms keyrings create dr-keyring \
  --location us-central1

# Create encryption key
gcloud kms keys create dr-encryption-key \
  --location us-central1 \
  --keyring dr-keyring \
  --purpose encryption \
  --rotation-period 90d \
  --next-rotation-time $(date -d '+90 days' +%Y-%m-%dT%H:%M:%S%z)

# Grant access to service accounts
gcloud kms keys add-iam-policy-binding dr-encryption-key \
  --location us-central1 \
  --keyring dr-keyring \
  --member serviceAccount:gke-service-account@PROJECT_ID.iam.gserviceaccount.com \
  --role roles/cloudkms.cryptoKeyEncrypterDecrypter
```

#### Encryption in Transit

**TLS/SSL Configuration:**

```nginx
# nginx/ssl.conf
server {
    listen 443 ssl http2;
    server_name api.example.com;

    # TLS 1.3 only (most secure)
    ssl_protocols TLSv1.3;
    ssl_prefer_server_ciphers off;

    # Certificate and key
    ssl_certificate /etc/nginx/ssl/api.example.com.crt;
    ssl_certificate_key /etc/nginx/ssl/api.example.com.key;

    # OCSP stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/nginx/ssl/ca-bundle.crt;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Disable SSL session tickets
    ssl_session_tickets off;

    location / {
        proxy_pass http://backend;
        proxy_ssl_verify on;
        proxy_ssl_trusted_certificate /etc/nginx/ssl/backend-ca.crt;
    }
}
```

**Database Connection Encryption:**

```python
# app/database.py
import psycopg2
import ssl

# PostgreSQL with SSL
conn = psycopg2.connect(
    host="prod-db-us-east-1.xxxxx.rds.amazonaws.com",
    port=5432,
    database="proddb",
    user="app_user",
    password="SecurePassword123",
    sslmode="verify-full",
    sslrootcert="/etc/ssl/certs/rds-ca-bundle.pem"
)

# Verify SSL connection
cursor = conn.cursor()
cursor.execute("SELECT ssl_is_used();")
print(f"SSL enabled: {cursor.fetchone()[0]}")
```

### 8.3 IAM Cross-Cloud Strategy

**Centralized Identity with Okta/Auth0:**

```yaml
# okta/dr-app-config.yaml
applications:
  - name: "DR Management Console"
    sign_on_mode: "SAML_2_0"
    settings:
      saml:
        audience: "https://dr-console.example.com"
        recipient: "https://dr-console.example.com/saml/acs"
        destination: "https://dr-console.example.com/saml/acs"
        idp_issuer: "http://www.okta.com/${org.externalKey}"
    
    # Map to cloud providers
    provisioning:
      - provider: "AWS"
        role_arn: "arn:aws:iam::ACCOUNT_ID:role/OktaDRAdmin"
        session_duration: 3600
      
      - provider: "Azure"
        tenant_id: "TENANT_ID"
        app_id: "APP_ID"
        role: "DR Administrator"
      
      - provider: "GCP"
        project_id: "PROJECT_ID"
        service_account: "okta-dr-admin@PROJECT_ID.iam.gserviceaccount.com"

    # Group assignments
    groups:
      - name: "DR-Admins"
        permissions:
          - "dr:failover:execute"
          - "dr:config:modify"
          - "dr:monitoring:view"
      
      - name: "DR-Operators"
        permissions:
          - "dr:monitoring:view"
          - "dr:tests:execute"
      
      - name: "DR-Viewers"
        permissions:
          - "dr:monitoring:view"
```

**AWS IAM Roles for Cross-Account Access:**

```hcl
# terraform/iam/cross-account-roles.tf
# Primary account role
resource "aws_iam_role" "dr_admin" {
  name = "DRAdministrator"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = "arn:aws:iam::ACCOUNT_ID:saml-provider/Okta"
      }
      Action = "sts:AssumeRoleWithSAML"
      Condition = {
        StringEquals = {
          "SAML:aud" = "https://signin.aws.amazon.com/saml"
        }
      }
    }]
  })
}

# Attach policies
resource "aws_iam_role_policy_attachment" "dr_admin_policies" {
  for_each = toset([
    "arn:aws:iam::aws:policy/AmazonRDSFullAccess",
    "arn:aws:iam::aws:policy/AmazonS3FullAccess",
    "arn:aws:iam::aws:policy/AmazonEC2FullAccess",
    "arn:aws:iam::aws:policy/AmazonRoute53FullAccess"
  ])

  role       = aws_iam_role.dr_admin.name
  policy_arn = each.value
}

# Custom DR policy
resource "aws_iam_policy" "dr_operations" {
  name        = "DROperations"
  description = "Custom policy for DR operations"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "rds:PromoteReadReplica",
          "rds:ModifyDBInstance",
          "route53:ChangeResourceRecordSets",
          "autoscaling:SetDesiredCapacity",
          "elbv2:ModifyTargetGroup"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "aws:RequestedRegion" = ["us-east-1", "us-west-2"]
          }
        }
      },
      {
        Effect = "Deny"
        Action = [
          "rds:DeleteDBInstance",
          "s3:DeleteBucket",
          "ec2:TerminateInstances"
        ]
        Resource = "*"
        Condition = {
          StringNotEquals = {
            "aws:MultiFactorAuthPresent" = "true"
          }
        }
      }
    ]
  })
}
```

**Service Account Management:**

```bash
# GCP service account for DR automation
gcloud iam service-accounts create dr-automation \
  --display-name="DR Automation Service Account" \
  --description="Service account for automated DR operations"

# Grant necessary roles
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:dr-automation@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/compute.instanceAdmin.v1"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:dr-automation@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/cloudsql.admin"

# Create and download key
gcloud iam service-accounts keys create dr-automation-key.json \
  --iam-account=dr-automation@PROJECT_ID.iam.gserviceaccount.com

# Store in HashiCorp Vault
vault kv put secret/gcp/dr-automation \
  credentials=@dr-automation-key.json

# Securely delete local key
shred -vfz -n 10 dr-automation-key.json
```

### 8.4 Secrets Management with HashiCorp Vault

**Vault Cluster Setup:**

```hcl
# terraform/vault/cluster.tf
resource "aws_instance" "vault" {
  count         = 3
  ami           = data.aws_ami.vault.id
  instance_type = "t3.medium"
  subnet_id     = var.private_subnet_ids[count.index]

  vpc_security_group_ids = [aws_security_group.vault.id]

  iam_instance_profile = aws_iam_instance_profile.vault.name

  user_data = templatefile("${path.module}/vault-init.sh", {
    vault_version = "1.15.0"
    kms_key_id    = aws_kms_key.vault_unseal.id
  })

  tags = {
    Name = "vault-${count.index + 1}"
    Role = "secrets-management"
  }
}

# Auto-unseal with AWS KMS
resource "aws_kms_key" "vault_unseal" {
  description             = "Vault auto-unseal key"
  deletion_window_in_days = 30
  enable_key_rotation     = true
}

# Vault configuration
resource "local_file" "vault_config" {
  filename = "${path.module}/vault-config.hcl"
  content  = <<-EOT
    storage "raft" {
      path    = "/opt/vault/data"
      node_id = "vault-${count.index + 1}"
    }

    listener "tcp" {
      address     = "0.0.0.0:8200"
      tls_cert_file = "/etc/vault/tls/vault.crt"
      tls_key_file  = "/etc/vault/tls/vault.key"
    }

    seal "awskms" {
      region     = "us-east-1"
      kms_key_id = "${aws_kms_key.vault_unseal.id}"
    }

    api_addr = "https://vault-${count.index + 1}.example.com:8200"
    cluster_addr = "https://vault-${count.index + 1}.example.com:8201"

    ui = true
  EOT
}
```

**Store DR Secrets in Vault:**

```bash
# Enable KV secrets engine
vault secrets enable -path=dr kv-v2

# Store database credentials
vault kv put dr/database/primary \
  host="prod-db-us-east-1.xxxxx.rds.amazonaws.com" \
  port="5432" \
  username="admin" \
  password="SecurePassword123"

vault kv put dr/database/secondary \
  host="prod-db-us-west-2.xxxxx.rds.amazonaws.com" \
  port="5432" \
  username="admin" \
  password="SecurePassword456"

# Store cloud provider credentials
vault kv put dr/aws/credentials \
  access_key_id="AKIAIOSFODNN7EXAMPLE" \
  secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

vault kv put dr/azure/credentials \
  tenant_id="TENANT_ID" \
  client_id="CLIENT_ID" \
  client_secret="CLIENT_SECRET"

vault kv put dr/gcp/credentials \
  project_id="PROJECT_ID" \
  service_account_key=@/path/to/key.json

# Create policy for DR automation
vault policy write dr-automation - <<EOF
path "dr/*" {
  capabilities = ["read", "list"]
}

path "dr/database/*" {
  capabilities = ["read", "list", "update"]
}
EOF

# Create token for DR automation
vault token create \
  -policy=dr-automation \
  -period=24h \
  -renewable=true \
  -display-name="dr-automation-token"
```

**Application Integration:**

```python
# app/vault_client.py
import hvac
import os

class VaultClient:
    def __init__(self):
        self.client = hvac.Client(
            url=os.getenv('VAULT_ADDR', 'https://vault.example.com:8200'),
            token=os.getenv('VAULT_TOKEN')
        )
        
        # Verify authentication
        if not self.client.is_authenticated():
            raise Exception("Vault authentication failed")
    
    def get_database_credentials(self, environment='primary'):
        """Retrieve database credentials from Vault"""
        secret = self.client.secrets.kv.v2.read_secret_version(
            path=f'database/{environment}',
            mount_point='dr'
        )
        
        return {
            'host': secret['data']['data']['host'],
            'port': secret['data']['data']['port'],
            'username': secret['data']['data']['username'],
            'password': secret['data']['data']['password']
        }
    
    def rotate_database_password(self, environment='primary'):
        """Rotate database password"""
        import secrets
        import string
        
        # Generate new password
        alphabet = string.ascii_letters + string.digits + string.punctuation
        new_password = ''.join(secrets.choice(alphabet) for _ in range(32))
        
        # Update in database
        # ... (database password update logic)
        
        # Update in Vault
        current_secret = self.get_database_credentials(environment)
        current_secret['password'] = new_password
        
        self.client.secrets.kv.v2.create_or_update_secret(
            path=f'database/{environment}',
            secret=current_secret,
            mount_point='dr'
        )
        
        return new_password

# Usage
vault = VaultClient()
db_creds = vault.get_database_credentials('primary')
```

### 8.5 Audit Logging and SIEM Integration

**CloudWatch Logs to Splunk:**

```python
# lambda/cloudwatch-to-splunk.py
import json
import gzip
import base64
import urllib3
import os

http = urllib3.PoolManager()

SPLUNK_HEC_URL = os.environ['SPLUNK_HEC_URL']
SPLUNK_HEC_TOKEN = os.environ['SPLUNK_HEC_TOKEN']

def lambda_handler(event, context):
    # Decode and decompress CloudWatch Logs
    compressed_payload = base64.b64decode(event['awslogs']['data'])
    uncompressed_payload = gzip.decompress(compressed_payload)
    log_data = json.loads(uncompressed_payload)
    
    # Transform to Splunk HEC format
    splunk_events = []
    for log_event in log_data['logEvents']:
        splunk_event = {
            'time': log_event['timestamp'] / 1000,
            'host': log_data['logGroup'],
            'source': log_data['logStream'],
            'sourcetype': 'aws:cloudwatch',
            'event': log_event['message']
        }
        splunk_events.append(json.dumps(splunk_event))
    
    # Send to Splunk
    payload = '\n'.join(splunk_events)
    
    response = http.request(
        'POST',
        SPLUNK_HEC_URL,
        body=payload,
        headers={
            'Authorization': f'Splunk {SPLUNK_HEC_TOKEN}',
            'Content-Type': 'application/json'
        }
    )
    
    return {
        'statusCode': response.status,
        'body': json.dumps('Logs sent to Splunk')
    }
```

**Unified Audit Dashboard:**

```yaml
# splunk/dashboards/dr-audit.xml
<dashboard>
  <label>DR Audit Dashboard</label>
  <row>
    <panel>
      <title>Failover Events</title>
      <table>
        <search>
          <query>
            index=dr_logs sourcetype=dr:failover
            | stats count by user, action, source_region, target_region, status
            | sort -_time
          </query>
        </search>
      </table>
    </panel>
  </row>
  <row>
    <panel>
      <title>Access Attempts</title>
      <table>
        <search>
          <query>
            index=dr_logs (sourcetype=aws:cloudtrail OR sourcetype=azure:activitylog OR sourcetype=gcp:audit)
            | stats count by user, action, resource, result
            | where result="failure"
          </query>
        </search>
      </table>
    </panel>
  </row>
  <row>
    <panel>
      <title>Configuration Changes</title>
      <table>
        <search>
          <query>
            index=dr_logs action=*modify* OR action=*update* OR action=*delete*
            | stats count by user, action, resource, _time
            | sort -_time
          </query>
        </search>
      </table>
    </panel>
  </row>
</dashboard>
```

### 8.6 Compliance Requirements

**Compliance Matrix:**

| Requirement | Implementation | Evidence |
|-------------|----------------|----------|
| **SOC 2 Type II** |
| Data encryption at rest | AWS KMS, Azure Key Vault, GCP KMS | Encryption configuration |
| Data encryption in transit | TLS 1.3, SSL certificates | SSL/TLS scan reports |
| Access controls | IAM, RBAC, MFA | IAM policies, access logs |
| Audit logging | CloudWatch, Azure Monitor, Cloud Logging | Audit trail reports |
| **PCI-DSS** |
| Network segmentation | VPC, Security Groups, Firewalls | Network diagrams |
| Regular vulnerability scans | AWS Inspector, Azure Security Center | Scan reports |
| Secure key management | KMS with rotation | Key rotation logs |
| **HIPAA** |
| Data residency | Regional data storage | Data flow diagrams |
| Backup encryption | Encrypted backups | Backup configuration |
| Access audit trails | Comprehensive logging | Audit logs |
| **GDPR** |
| Data portability | Export capabilities | Data export procedures |
| Right to erasure | Data deletion procedures | Deletion logs |
| Data protection impact assessment | DPIA documentation | DPIA reports |

**Automated Compliance Checking:**

```python
# compliance/checker.py
import boto3
import json

class ComplianceChecker:
    def __init__(self):
        self.ec2 = boto3.client('ec2')
        self.rds = boto3.client('rds')
        self.s3 = boto3.client('s3')
        self.findings = []
    
    def check_encryption_at_rest(self):
        """Check if all resources are encrypted"""
        # Check RDS encryption
        dbs = self.rds.describe_db_instances()
        for db in dbs['DBInstances']:
            if not db['StorageEncrypted']:
                self.findings.append({
                    'severity': 'HIGH',
                    'resource': db['DBInstanceIdentifier'],
                    'issue': 'Database not encrypted at rest',
                    'remediation': 'Enable encryption on RDS instance'
                })
        
        # Check S3 bucket encryption
        buckets = self.s3.list_buckets()
        for bucket in buckets['Buckets']:
            try:
                encryption = self.s3.get_bucket_encryption(Bucket=bucket['Name'])
            except:
                self.findings.append({
                    'severity': 'HIGH',
                    'resource': bucket['Name'],
                    'issue': 'S3 bucket not encrypted',
                    'remediation': 'Enable default encryption on S3 bucket'
                })
    
    def check_public_access(self):
        """Check for publicly accessible resources"""
        # Check for public S3 buckets
        buckets = self.s3.list_buckets()
        for bucket in buckets['Buckets']:
            try:
                acl = self.s3.get_bucket_acl(Bucket=bucket['Name'])
                for grant in acl['Grants']:
                    if grant['Grantee'].get('URI') == 'http://acs.amazonaws.com/groups/global/AllUsers':
                        self.findings.append({
                            'severity': 'CRITICAL',
                            'resource': bucket['Name'],
                            'issue': 'S3 bucket publicly accessible',
                            'remediation': 'Remove public access from S3 bucket'
                        })
            except:
                pass
    
    def check_mfa_enabled(self):
        """Check if MFA is enabled for privileged users"""
        iam = boto3.client('iam')
        users = iam.list_users()
        
        for user in users['Users']:
            mfa_devices = iam.list_mfa_devices(UserName=user['UserName'])
            if not mfa_devices['MFADevices']:
                # Check if user has admin permissions
                policies = iam.list_attached_user_policies(UserName=user['UserName'])
                for policy in policies['AttachedPolicies']:
                    if 'Admin' in policy['PolicyName']:
                        self.findings.append({
                            'severity': 'HIGH',
                            'resource': user['UserName'],
                            'issue': 'Admin user without MFA',
                            'remediation': 'Enable MFA for admin user'
                        })
    
    def generate_report(self):
        """Generate compliance report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_findings': len(self.findings),
            'critical': len([f for f in self.findings if f['severity'] == 'CRITICAL']),
            'high': len([f for f in self.findings if f['severity'] == 'HIGH']),
            'findings': self.findings
        }
        
        return json.dumps(report, indent=2)

if __name__ == "__main__":
    checker = ComplianceChecker()
    checker.check_encryption_at_rest()
    checker.check_public_access()
    checker.check_mfa_enabled()
    
    print(checker.generate_report())
```

### 8.7 Backup Immutability

**S3 Object Lock for Immutable Backups:**

```bash
# Enable versioning (required for Object Lock)
aws s3api put-bucket-versioning \
  --bucket dr-backups-immutable \
  --versioning-configuration Status=Enabled

# Enable Object Lock
aws s3api put-object-lock-configuration \
  --bucket dr-backups-immutable \
  --object-lock-configuration '{
    "ObjectLockEnabled": "Enabled",
    "Rule": {
      "DefaultRetention": {
        "Mode": "GOVERNANCE",
        "Days": 90
      }
    }
  }'

# Upload backup with legal hold
aws s3api put-object \
  --bucket dr-backups-immutable \
  --key backups/database-backup-20231127.sql.gz \
  --body database-backup-20231127.sql.gz \
  --object-lock-mode COMPLIANCE \
  --object-lock-retain-until-date "2024-02-27T00:00:00Z" \
  --object-lock-legal-hold-status ON
```

**Azure Immutable Blob Storage:**

```bash
# Create storage account with immutability support
az storage account create \
  --name drbackupsimmutable \
  --resource-group prod-rg \
  --location eastus \
  --sku Standard_LRS \
  --kind StorageV2 \
  --enable-hierarchical-namespace false

# Create container with immutability policy
az storage container create \
  --name backups \
  --account-name drbackupsimmutable \
  --public-access off

# Set immutability policy (WORM - Write Once Read Many)
az storage container immutability-policy create \
  --account-name drbackupsimmutable \
  --container-name backups \
  --period 90 \
  --allow-protected-append-writes false

# Lock the policy (cannot be modified or deleted)
az storage container immutability-policy lock \
  --account-name drbackupsimmutable \
  --container-name backups \
  --if-match "*"
```

