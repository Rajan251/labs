#!/bin/bash
# VPN Server User Data Script
# This script installs and configures OpenVPN on Amazon Linux 2

set -e

# Update system
yum update -y

# Install OpenVPN and Easy-RSA
yum install -y openvpn easy-rsa

# Install CloudWatch Agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
rpm -U ./amazon-cloudwatch-agent.rpm

# Enable IP forwarding
echo "net.ipv4.ip_forward = 1" >> /etc/sysctl.conf
sysctl -p

# Create OpenVPN directory
mkdir -p /etc/openvpn/easy-rsa

# Copy Easy-RSA files
cp -r /usr/share/easy-rsa/3/* /etc/openvpn/easy-rsa/

# Initialize PKI
cd /etc/openvpn/easy-rsa
./easyrsa init-pki
./easyrsa build-ca nopass <<EOF
VPN-CA
EOF

# Generate server certificate
./easyrsa gen-req server nopass <<EOF
server
EOF

./easyrsa sign-req server server <<EOF
yes
EOF

# Generate DH parameters
./easyrsa gen-dh

# Generate TLS auth key
openvpn --genkey secret /etc/openvpn/ta.key

# Copy certificates
cp pki/ca.crt /etc/openvpn/
cp pki/issued/server.crt /etc/openvpn/
cp pki/private/server.key /etc/openvpn/
cp pki/dh.pem /etc/openvpn/

# Create OpenVPN server configuration
cat > /etc/openvpn/server.conf <<'EOF'
port 1194
proto udp
dev tun
ca ca.crt
cert server.crt
key server.key
dh dh.pem
tls-auth ta.key 0
server 10.8.0.0 255.255.255.0
ifconfig-pool-persist ipp.txt
push "route 10.0.0.0 255.255.0.0"
push "dhcp-option DNS 10.0.0.2"
keepalive 10 120
cipher AES-256-CBC
user nobody
group nobody
persist-key
persist-tun
status openvpn-status.log
log-append /var/log/openvpn.log
verb 3
EOF

# Configure firewall
iptables -t nat -A POSTROUTING -s 10.8.0.0/24 -o eth0 -j MASQUERADE
iptables-save > /etc/sysconfig/iptables

# Enable and start OpenVPN
systemctl enable openvpn@server
systemctl start openvpn@server

# Create client configuration template
mkdir -p /root/client-configs
cat > /root/client-configs/base.conf <<'EOF'
client
dev tun
proto udp
remote REPLACE_WITH_VPN_PUBLIC_IP 1194
resolv-retry infinite
nobind
user nobody
group nobody
persist-key
persist-tun
remote-cert-tls server
cipher AES-256-CBC
verb 3
EOF

echo "VPN Server setup complete!"
