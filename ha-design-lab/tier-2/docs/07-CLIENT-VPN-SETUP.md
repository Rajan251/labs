# 🔐 Step 7: Client VPN Setup - Web UI Guide

> **Setting Up AWS Client VPN for Secure Access to Private Instances**

---

## 📋 What We'll Create

- ✅ Server and client certificates for mutual authentication
- ✅ AWS Client VPN endpoint
- ✅ VPN authorization rules
- ✅ VPN subnet associations
- ✅ VPN client configuration file

---

## 🎯 Overview

**AWS Client VPN** provides secure access to resources in your VPC. It allows you to:
- SSH to EC2 instances in private subnets
- Access private resources without bastion hosts
- Use mutual certificate authentication (TLS)

**Cost**: ~$72/month for endpoint + ~$0.05/hour per connection

---

## 🚀 Part 1: Generate Certificates (Local Machine)

### Step 7.1: Install OpenSSL

**Linux/Mac** (usually pre-installed):
```bash
openssl version
```

**Windows**:
- Download from: https://slproweb.com/products/Win32OpenSSL.html
- Or use Git Bash (includes OpenSSL)

---

### Step 7.2: Generate Certificates

Run these commands on your **local machine**:

```bash
# Create directory for certificates
mkdir ~/tier2-vpn-certs
cd ~/tier2-vpn-certs

# 1. Generate CA (Certificate Authority) key
openssl genrsa -out ca-key.pem 2048

# 2. Generate CA certificate
openssl req -new -x509 -days 3650 -key ca-key.pem -out ca-cert.pem \
  -subj "/C=US/ST=State/L=City/O=Organization/OU=IT/CN=tier2-vpn-ca"

# 3. Generate server key
openssl genrsa -out server-key.pem 2048

# 4. Generate server certificate signing request (CSR)
openssl req -new -key server-key.pem -out server-csr.pem \
  -subj "/C=US/ST=State/L=City/O=Organization/OU=IT/CN=tier2-vpn-server"

# 5. Sign server certificate with CA
openssl x509 -req -days 3650 -in server-csr.pem -CA ca-cert.pem \
  -CAkey ca-key.pem -CAcreateserial -out server-cert.pem

# 6. Generate client key
openssl genrsa -out client-key.pem 2048

# 7. Generate client certificate signing request
openssl req -new -key client-key.pem -out client-csr.pem \
  -subj "/C=US/ST=State/L=City/O=Organization/OU=IT/CN=tier2-vpn-client"

# 8. Sign client certificate with CA
openssl x509 -req -days 3650 -in client-csr.pem -CA ca-cert.pem \
  -CAkey ca-key.pem -CAcreateserial -out client-cert.pem
```

**Verify certificates created**:
```bash
ls -la ~/tier2-vpn-certs/
# Should see: ca-cert.pem, ca-key.pem, server-cert.pem, server-key.pem,
#             client-cert.pem, client-key.pem, and .csr files
```

---

## 🚀 Part 2: Import Certificates to AWS Certificate Manager

### Step 7.3: Import Server Certificate

1. **Open AWS Certificate Manager**
   - Go to https://console.aws.amazon.com/acm/
   - Ensure you're in **us-east-1** region

2. **Import Certificate**
   - Click **"Import certificate"** button

3. **Paste Certificate Contents**

   **Certificate body**:
   ```bash
   # Copy content of server-cert.pem
   cat ~/tier2-vpn-certs/server-cert.pem
   # Paste the entire output (including BEGIN/END lines)
   ```

   **Certificate private key**:
   ```bash
   # Copy content of server-key.pem
   cat ~/tier2-vpn-certs/server-key.pem
   # Paste the entire output
   ```

   **Certificate chain**:
   ```bash
   # Copy content of ca-cert.pem
   cat ~/tier2-vpn-certs/ca-cert.pem
   # Paste the entire output
   ```

4. **Add Tags** (optional):
   - **Key**: `Name`, **Value**: `tier2-vpn-server-cert`

5. **Import**
   - Click **"Next"**
   - Click **"Import"**
   - Note the **Certificate ARN**: `arn:aws:acm:us-east-1:xxxx:certificate/xxxx`

---

### Step 7.4: Import Client Certificate

Repeat the same process for client certificate:

1. **Import certificate** again
2. **Paste**:
   - **Certificate body**: Content of `client-cert.pem`
   - **Certificate private key**: Content of `client-key.pem`
   - **Certificate chain**: Content of `ca-cert.pem`
3. **Tag**: `Name` = `tier2-vpn-client-cert`
4. **Import** and note the ARN

---

## 🚀 Part 3: Create Client VPN Endpoint

### Step 7.5: Navigate to Client VPN

1. **Open VPC Dashboard**
   - Go to https://console.aws.amazon.com/vpc/
   - In the left sidebar, under **"Virtual private network (VPN)"**
   - Click **"Client VPN endpoints"**

---

### Step 7.6: Create VPN Endpoint

1. **Start Creation**
   - Click **"Create Client VPN endpoint"** button

2. **Configure Endpoint**

   **Name tag**: `tier2-vpn-endpoint`

   **Description**: `Client VPN for tier-2 architecture`

   **Client IPv4 CIDR**: `172.16.0.0/22`
   - This is the IP range assigned to VPN clients
   - Must NOT overlap with VPC CIDR (10.0.0.0/16)
   - /22 provides 1024 IPs for VPN clients

   **Server certificate ARN**:
   - Select the server certificate you imported
   - Should show: `tier2-vpn-server-cert`

   **Authentication options**:
   - Select **"Use mutual authentication"**
   - **Client certificate ARN**: Select `tier2-vpn-client-cert`

   **Connection logging** (optional but recommended):
   - Check **"Enable log details on client connections"**
   - **CloudWatch Logs log group**: Create new or select existing
   - **CloudWatch Logs log stream**: Create new

   **DNS servers** (optional):
   - Leave blank or enter: `10.0.0.2` (VPC DNS server)

   **Transport protocol**: **UDP** (recommended for better performance)

   **VPN port**: **443** (works through most firewalls)

   **Split tunnel**: **Enable** (only VPC traffic goes through VPN)

   **VPC ID**: Select **tier2-vpc**

   **Security group**: Select **tier2-ec2-sg** (or create VPN-specific SG)

   **Self-service portal**: **Disable** (or enable if you want users to download config)

3. **Create**
   - Click **"Create Client VPN endpoint"**
   - Wait for status to change from **"Pending-associate"** to **"Available"**
   - This takes 5-10 minutes ☕

4. **Note VPN Endpoint ID**
   - **Client VPN endpoint ID**: `cvpn-endpoint-xxxxxxxxxxxxxxxxx`

---

## 🚀 Part 4: Associate VPN with Subnets

### Step 7.7: Associate Target Network

1. **Select VPN Endpoint**
   - Click on **tier2-vpn-endpoint**

2. **Associate Subnet**
   - Click the **"Target network associations"** tab
   - Click **"Associate target network"**

3. **Select Subnet**
   - **VPC**: tier2-vpc (auto-filled)
   - **Subnet to associate**: Select **tier2-private-subnet-1** (10.0.3.0/24)
   - Click **"Associate target network"**

4. **Wait for Association**
   - Status will change from **"Associating"** to **"Associated"**
   - Takes 2-3 minutes

5. **Optional: Associate Second Subnet** (for high availability)
   - Repeat for **tier2-private-subnet-2**
   - This provides VPN access even if one AZ fails

---

## 🚀 Part 5: Add Authorization Rules

### Step 7.8: Authorize VPN Access

1. **Go to Authorization Rules**
   - Still in VPN endpoint details
   - Click the **"Authorization rules"** tab
   - Click **"Add authorization rule"**

2. **Configure Rule**
   - **Destination network**: `10.0.0.0/16` (entire VPC)
   - **Grant access to**: Select **"Allow access to all users"**
   - **Description**: `Allow VPN access to entire VPC`

3. **Add Rule**
   - Click **"Add authorization rule"**
   - Status should show **"Active"**

---

## 🚀 Part 6: Download and Configure VPN Client

### Step 7.9: Download Client Configuration

1. **Download Config**
   - In VPN endpoint details
   - Click **"Download client configuration"** button
   - Save the file: `downloaded-client-config.ovpn`

2. **Modify Configuration File**

   Open `downloaded-client-config.ovpn` in a text editor and add these lines at the end:

   ```
   <cert>
   [Paste entire content of client-cert.pem here]
   </cert>

   <key>
   [Paste entire content of client-key.pem here]
   </key>
   ```

   **Example**:
   ```bash
   # Get client certificate content
   cat ~/tier2-vpn-certs/client-cert.pem

   # Get client key content
   cat ~/tier2-vpn-certs/client-key.pem
   ```

3. **Save Modified Config**
   - Save as: `tier2-vpn-client.ovpn`

---

### Step 7.10: Install AWS VPN Client

**Download AWS VPN Client**:
- **Windows**: https://d20adtppz83p9s.cloudfront.net/WPF/latest/AWS_VPN_Client.msi
- **macOS**: https://d20adtppz83p9s.cloudfront.net/OSX/latest/AWS_VPN_Client.pkg
- **Linux**: https://d20adtppz83p9s.cloudfront.net/GTK/latest/awsvpnclient_amd64.deb

**Install the client** following the installer prompts.

---

### Step 7.11: Connect to VPN

1. **Open AWS VPN Client**

2. **Add Profile**
   - Click **"File"** → **"Manage Profiles"**
   - Click **"Add Profile"**
   - **Display Name**: `Tier-2 VPN`
   - **VPN Configuration File**: Browse and select `tier2-vpn-client.ovpn`
   - Click **"Add Profile"**

3. **Connect**
   - Select **"Tier-2 VPN"** from the dropdown
   - Click **"Connect"**
   - Wait for connection (10-30 seconds)
   - Status should show **"Connected"**

4. **Verify Connection**
   - You should see your assigned VPN IP (172.16.0.x)
   - You can now access private instances!

---

## 🚀 Part 7: Test SSH Access

### Step 7.12: SSH to Private Instance

```bash
# Get your private instance IP from EC2 console
# Example: 10.0.3.45

# SSH to instance (while connected to VPN)
ssh -i ~/Downloads/tier2-ec2-key.pem ec2-user@10.0.3.45
```

**If successful**, you should see:
```
[ec2-user@ip-10-0-3-45 ~]$
```

**Test internet access from instance**:
```bash
ping -c 4 8.8.8.8
curl http://checkip.amazonaws.com
# Should return NAT Gateway's Elastic IP
```

---

## ✅ Verification Checklist

### Certificates
- [ ] Server certificate imported to ACM
- [ ] Client certificate imported to ACM
- [ ] Certificate ARNs noted

### VPN Endpoint
- [ ] VPN endpoint created: `cvpn-endpoint-xxx`
- [ ] Status: **Available**
- [ ] Client CIDR: 172.16.0.0/22
- [ ] Authentication: Mutual (certificates)

### Network Associations
- [ ] Associated with tier2-private-subnet-1
- [ ] (Optional) Associated with tier2-private-subnet-2

### Authorization Rules
- [ ] Rule for 10.0.0.0/16 created
- [ ] Status: **Active**

### Client Connection
- [ ] AWS VPN Client installed
- [ ] Profile added with modified config
- [ ] Successfully connected
- [ ] Assigned VPN IP: 172.16.0.x
- [ ] Can SSH to private instances
- [ ] Can ping internet from instances

---

## 🔧 Troubleshooting

### Issue: "Certificate import failed"

**Solution**:
1. Ensure you copied entire certificate including BEGIN/END lines
2. Check no extra spaces or line breaks
3. Verify certificate chain is correct (CA cert)

### Issue: "VPN endpoint stuck in Pending"

**Solution**:
1. Wait up to 10 minutes
2. Check CloudWatch logs for errors
3. Verify certificates are valid
4. Delete and recreate if stuck >15 minutes

### Issue: "Cannot connect to VPN"

**Solution**:
1. Verify client config has cert and key embedded
2. Check VPN endpoint status is "Available"
3. Verify authorization rules exist
4. Check security group allows VPN traffic
5. Try different transport protocol (TCP instead of UDP)

### Issue: "Connected to VPN but cannot SSH"

**Solution**:
1. Verify authorization rule for 10.0.0.0/16
2. Check security group allows SSH from VPN CIDR
3. Verify route tables are correct
4. Test with ping first: `ping 10.0.3.x`
5. Check instance is running

### Issue: "SSH connection timeout"

**Solution**:
1. Verify you're connected to VPN
2. Check instance private IP is correct
3. Verify security group allows SSH from 10.0.0.0/16
4. Check key pair permissions: `chmod 400 key.pem`
5. Try: `ssh -v` for verbose output

---

## 💡 Best Practices

### Security
- ✅ Use mutual authentication (certificates)
- ✅ Enable connection logging
- ✅ Rotate certificates annually
- ✅ Use split tunnel to minimize VPN traffic
- ✅ Restrict authorization rules to specific CIDRs

### Cost Optimization
- 💰 VPN endpoint: ~$72/month (always running)
- 💰 Connection: ~$0.05/hour per user
- 💡 Disconnect when not in use
- 💡 Consider AWS Systems Manager Session Manager as free alternative
- 💡 Use VPN only for development/testing if cost is concern

### High Availability
- ✅ Associate VPN with subnets in multiple AZs
- ✅ Use UDP for better performance
- ✅ Enable connection logging for troubleshooting

---

## 📝 Save Your Configuration

```
Client VPN Configuration - Tier 2 Architecture
===============================================

Certificates:
  Server Cert ARN: arn:aws:acm:us-east-1:xxxx:certificate/xxxx
  Client Cert ARN: arn:aws:acm:us-east-1:xxxx:certificate/xxxx
  Local Path: ~/tier2-vpn-certs/

VPN Endpoint:
  Name:       tier2-vpn-endpoint
  ID:         cvpn-endpoint-xxxxxxxxxxxxxxxxx
  Client CIDR: 172.16.0.0/22
  Protocol:   UDP
  Port:       443
  Status:     Available

Target Networks:
  - tier2-private-subnet-1 (10.0.3.0/24)
  - tier2-private-subnet-2 (10.0.4.0/24) [optional]

Authorization Rules:
  - Destination: 10.0.0.0/16
  - Access: All users
  - Status: Active

Client Config:
  File: tier2-vpn-client.ovpn
  Profile Name: Tier-2 VPN
```

---

## 🎯 Next Steps

✅ **VPN is configured and working!**

Now proceed to:
- **[Step 8: Testing & Verification](./08-TESTING-VERIFICATION.md)** - Comprehensive testing of the entire architecture

---

## 📖 Additional Resources

- [AWS Client VPN Documentation](https://docs.aws.amazon.com/vpn/latest/clientvpn-admin/)
- [Client VPN Authentication](https://docs.aws.amazon.com/vpn/latest/clientvpn-admin/client-authentication.html)
- [Troubleshooting Client VPN](https://docs.aws.amazon.com/vpn/latest/clientvpn-admin/troubleshooting.html)
- [AWS VPN Client Download](https://aws.amazon.com/vpn/client-vpn-download/)

---

**Client VPN setup complete! 🎉 Continue to [Testing & Verification](./08-TESTING-VERIFICATION.md)**
