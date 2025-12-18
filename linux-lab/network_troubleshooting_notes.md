# Network Troubleshooting Methodology

**Level:** Expert / Network Engineer / SRE
**Focus:** Systematic diagnosis of production network outages using OSI model.

---

## 1. Symptoms Classification

### 1.1 Symptom Types
*   **Complete Loss**: No connectivity at all.
*   **Intermittent**: Connectivity drops randomly.
*   **Slow Performance**: High latency, low throughput.
*   **Packet Loss**: Packets dropped in transit.

---

## 2. Layered Troubleshooting Approach

### Layer 1: Physical
```bash
# Check interface status
ip link show eth0

# Check cable/port with ethtool
ethtool eth0
# Look for: Link detected: yes

# Check errors
ethtool -S eth0 | grep -i error
```

**Common Issues:**
- Unplugged cable
- Bad cable (CRC errors)
- Switch port disabled

---

### Layer 2: Data Link
```bash
# Check MAC address table
ip neigh show

# ARP cache
arp -n

# VLAN configuration
ip link show | grep vlan
```

**Common Issues:**
- MAC address conflicts
- VLAN mismatch
- Spanning Tree blocking port

---

### Layer 3: Network
```bash
# Routing table
ip route show

# Test connectivity
ping 8.8.8.8

# Trace route
traceroute google.com
mtr google.com  # Better than traceroute
```

**Common Issues:**
- IP address conflict
- Wrong subnet mask
- Missing default gateway
- Routing loop

---

### Layer 4: Transport
```bash
# Check listening ports
ss -tulpn

# Test port connectivity
nc -zv 192.168.1.10 80
telnet 192.168.1.10 80

# Check firewall
iptables -L -n -v
```

**Common Issues:**
- Firewall blocking
- Port not listening
- MTU mismatch

---

### Layer 5+: Application
```bash
# DNS resolution
dig google.com
nslookup google.com

# HTTP test
curl -v http://example.com

# Check service
systemctl status nginx
```

**Common Issues:**
- DNS failure
- Service down
- Authentication failure

---

## 3. Diagnostic Tools by Layer

### Layer 1/2 Tools
```bash
# Interface details
ethtool eth0

# ARP ping (Layer 2)
arping 192.168.1.1

# Check duplex/speed
mii-tool eth0
```

### Layer 3 Tools
```bash
# Continuous ping
ping -c 10 8.8.8.8

# MTR (better traceroute)
mtr --report google.com

# Route verification
ip route get 8.8.8.8
```

### Layer 4 Tools
```bash
# Port scan
nmap -p 80,443 example.com

# Socket statistics
ss -s

# Test TCP connection
nc -zv example.com 443
```

### Layer 5+ Tools
```bash
# DNS lookup
dig +trace example.com

# HTTP headers
curl -I https://example.com

# SSL/TLS test
openssl s_client -connect example.com:443
```

---

## 4. Common Issues & Solutions

### 4.1 Duplicate IP Addresses
```bash
# Symptom: Intermittent connectivity
# Check ARP cache
arp -n | grep 192.168.1.100

# If two MACs for same IP = conflict
# Solution: Change IP on one device
```

### 4.2 DNS Problems
```bash
# Symptom: "Cannot resolve hostname"
# Test DNS
dig google.com @8.8.8.8

# If works with 8.8.8.8 but not default = local DNS issue
# Fix: Update /etc/resolv.conf
```

### 4.3 MTU Mismatch
```bash
# Symptom: SSH works, but large transfers fail
# Test MTU
ping -M do -s 1472 8.8.8.8

# If fails, MTU too large
# Fix: Lower MTU
ip link set eth0 mtu 1400
```

### 4.4 Firewall Blocks
```bash
# Silent drop vs Connection refused
# Drop: No response (timeout)
# Refused: RST packet (port closed)

# Test
telnet example.com 80
# Timeout = firewall drop
# Connection refused = port not listening
```

---

## 5. Enterprise Scenarios

### Scenario 1: Office to Datacenter Loss
```bash
# 1. Test local network
ping 192.168.1.1  # Gateway

# 2. Test ISP
ping 8.8.8.8

# 3. Test datacenter
ping datacenter-ip

# 4. Traceroute to find where it fails
mtr datacenter-ip
```

### Scenario 2: VPN Connectivity
```bash
# 1. Check VPN service
systemctl status openvpn

# 2. Check routes
ip route | grep tun0

# 3. Test through VPN
ping -I tun0 10.0.0.1

# 4. Check firewall
iptables -L -n -v | grep tun0
```

### Scenario 3: Load Balancer Health Check Failure
```bash
# 1. Check backend directly
curl http://backend-ip:8080/health

# 2. Check from LB
curl http://lb-ip/health

# 3. Check LB logs
tail -f /var/log/haproxy.log

# 4. Verify health check config
# HAProxy: check inter 2000 rise 2 fall 3
```

---

## 6. Documentation Requirements

### Network Diagram Example
```
Internet
   |
[Firewall]
   |
[Core Switch] --- [DMZ Switch]
   |                    |
[Server VLAN]      [Web Servers]
```

### IP Allocation Record
```
Network: 192.168.1.0/24
Gateway: 192.168.1.1
DHCP Range: 192.168.1.100-200
Servers: 192.168.1.10-50
```

---

## 7. Troubleshooting Flowchart

```
Network Issue
    |
    v
Can ping gateway? 
    |
    +-- NO --> Layer 1/2 (cable, switch)
    |
    +-- YES --> Can ping 8.8.8.8?
                    |
                    +-- NO --> Layer 3 (routing)
                    |
                    +-- YES --> Can resolve DNS?
                                    |
                                    +-- NO --> DNS issue
                                    |
                                    +-- YES --> Layer 4+ (firewall, app)
```
