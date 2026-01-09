#!/bin/bash

# ============================================
# VPN Certificate Generation Script
# Tier-2 AWS Architecture
# ============================================

set -e

echo "=================================================="
echo "AWS Client VPN - Certificate Generation Script"
echo "=================================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Certificate directory
CERT_DIR="$HOME/tier2-vpn-certs"

echo "This script will generate certificates for AWS Client VPN"
echo "Certificates will be saved to: $CERT_DIR"
echo ""

# Check if OpenSSL is installed
if ! command -v openssl &> /dev/null; then
    echo -e "${YELLOW}Error: OpenSSL is not installed${NC}"
    echo "Please install OpenSSL first:"
    echo "  - Ubuntu/Debian: sudo apt-get install openssl"
    echo "  - macOS: brew install openssl"
    echo "  - Windows: Download from https://slproweb.com/products/Win32OpenSSL.html"
    exit 1
fi

echo -e "${GREEN}✓${NC} OpenSSL is installed ($(openssl version))"
echo ""

# Create certificate directory
if [ -d "$CERT_DIR" ]; then
    echo -e "${YELLOW}Warning: Directory $CERT_DIR already exists${NC}"
    read -p "Do you want to overwrite existing certificates? (yes/no): " OVERWRITE
    if [ "$OVERWRITE" != "yes" ]; then
        echo "Exiting without generating certificates"
        exit 0
    fi
    echo "Removing existing certificates..."
    rm -rf "$CERT_DIR"
fi

mkdir -p "$CERT_DIR"
cd "$CERT_DIR"

echo -e "${GREEN}✓${NC} Created directory: $CERT_DIR"
echo ""

# Certificate details
COUNTRY="US"
STATE="State"
CITY="City"
ORG="Organization"
OU="IT"

echo "Certificate Details:"
echo "  Country: $COUNTRY"
echo "  State: $STATE"
echo "  City: $CITY"
echo "  Organization: $ORG"
echo "  Organizational Unit: $OU"
echo ""

read -p "Press Enter to continue or Ctrl+C to cancel..."
echo ""

# Generate CA key
echo "1. Generating CA private key..."
openssl genrsa -out ca-key.pem 2048 2>/dev/null
echo -e "${GREEN}✓${NC} CA private key generated: ca-key.pem"

# Generate CA certificate
echo "2. Generating CA certificate..."
openssl req -new -x509 -days 3650 -key ca-key.pem -out ca-cert.pem \
  -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/OU=$OU/CN=tier2-vpn-ca" 2>/dev/null
echo -e "${GREEN}✓${NC} CA certificate generated: ca-cert.pem (valid for 10 years)"

# Generate server key
echo "3. Generating server private key..."
openssl genrsa -out server-key.pem 2048 2>/dev/null
echo -e "${GREEN}✓${NC} Server private key generated: server-key.pem"

# Generate server CSR
echo "4. Generating server certificate signing request..."
openssl req -new -key server-key.pem -out server-csr.pem \
  -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/OU=$OU/CN=tier2-vpn-server" 2>/dev/null
echo -e "${GREEN}✓${NC} Server CSR generated: server-csr.pem"

# Sign server certificate
echo "5. Signing server certificate with CA..."
openssl x509 -req -days 3650 -in server-csr.pem -CA ca-cert.pem \
  -CAkey ca-key.pem -CAcreateserial -out server-cert.pem 2>/dev/null
echo -e "${GREEN}✓${NC} Server certificate signed: server-cert.pem (valid for 10 years)"

# Generate client key
echo "6. Generating client private key..."
openssl genrsa -out client-key.pem 2048 2>/dev/null
echo -e "${GREEN}✓${NC} Client private key generated: client-key.pem"

# Generate client CSR
echo "7. Generating client certificate signing request..."
openssl req -new -key client-key.pem -out client-csr.pem \
  -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/OU=$OU/CN=tier2-vpn-client" 2>/dev/null
echo -e "${GREEN}✓${NC} Client CSR generated: client-csr.pem"

# Sign client certificate
echo "8. Signing client certificate with CA..."
openssl x509 -req -days 3650 -in client-csr.pem -CA ca-cert.pem \
  -CAkey ca-key.pem -CAcreateserial -out client-cert.pem 2>/dev/null
echo -e "${GREEN}✓${NC} Client certificate signed: client-cert.pem (valid for 10 years)"

echo ""
echo "=================================================="
echo "Certificate Generation Complete!"
echo "=================================================="
echo ""
echo "Generated files in $CERT_DIR:"
ls -lh "$CERT_DIR"
echo ""

# Verify certificates
echo "Verifying certificates..."
echo ""

echo "CA Certificate:"
openssl x509 -in ca-cert.pem -noout -subject -dates
echo ""

echo "Server Certificate:"
openssl x509 -in server-cert.pem -noout -subject -dates -issuer
echo ""

echo "Client Certificate:"
openssl x509 -in client-cert.pem -noout -subject -dates -issuer
echo ""

echo "=================================================="
echo "Next Steps:"
echo "=================================================="
echo ""
echo "1. Import server certificate to AWS Certificate Manager:"
echo "   - Certificate body: server-cert.pem"
echo "   - Private key: server-key.pem"
echo "   - Certificate chain: ca-cert.pem"
echo ""
echo "2. Import client certificate to AWS Certificate Manager:"
echo "   - Certificate body: client-cert.pem"
echo "   - Private key: client-key.pem"
echo "   - Certificate chain: ca-cert.pem"
echo ""
echo "3. Use these certificates when creating Client VPN endpoint"
echo ""
echo "4. When downloading VPN client config, add these to the .ovpn file:"
echo "   <cert>"
echo "   [Content of client-cert.pem]"
echo "   </cert>"
echo ""
echo "   <key>"
echo "   [Content of client-key.pem]"
echo "   </key>"
echo ""
echo "=================================================="
echo ""
echo "To view certificate contents:"
echo "  cat $CERT_DIR/server-cert.pem"
echo "  cat $CERT_DIR/server-key.pem"
echo "  cat $CERT_DIR/ca-cert.pem"
echo "  cat $CERT_DIR/client-cert.pem"
echo "  cat $CERT_DIR/client-key.pem"
echo ""
echo "=================================================="
echo -e "${GREEN}Certificate generation successful!${NC}"
echo "=================================================="
