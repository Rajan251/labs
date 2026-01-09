# Layer 3-4: Network and Transport Troubleshooting

Complete guide to IP routing, connectivity, TCP/UDP, and firewall troubleshooting.

---

## Layer 3: Network Layer

### IP Configuration

```bash
# View IP addresses
ip addr show

# Add IP address
ip addr add 192.168.1.100/24 dev eth0

# Remove IP address
ip addr del 192.168.1.100/24 dev eth0

# Detect IP conflicts
arping -D -I eth0 -c 5 192.168.1.100
```

### Routing

```bash
# View routing table
ip route show

# Test route to destination
ip route get 8.8.8.8

# Add static route
ip route add 10.0.0.0/8 via 192.168.1.254

# Add default route
ip route add default via 192.168.1.1

# Delete route
ip route del 10.0.0.0/8
```

### Connectivity Testing

```bash
# Basic ping
ping -c 4 8.8.8.8

# MTU testing
ping -M do -s 1472 8.8.8.8    # Should work (1500 MTU)
ping -M do -s 1473 8.8.8.8    # Fails if MTU=1500

# Traceroute
traceroute -n 8.8.8.8         # No DNS
traceroute -I 8.8.8.8         # ICMP
tcptraceroute 8.8.8.8 443     # TCP

# MTR (continuous monitoring)
mtr --report --report-cycles 100 8.8.8.8
```

### NAT & Forwarding

```bash
# Enable IP forwarding
echo 1 > /proc/sys/net/ipv4/ip_forward

# Make persistent
echo "net.ipv4.ip_forward = 1" >> /etc/sysctl.conf
sysctl -p

# View NAT rules
iptables -t nat -L -n -v
nft list ruleset | grep -A 10 nat

# Add MASQUERADE rule
iptables -t nat -A POSTROUTING -s 192.168.1.0/24 -o eth0 -j MASQUERADE

# Monitor NAT connections
conntrack -L
conntrack -E    # Real-time events
```

---

## Layer 4: Transport Layer

### Port & Service Checking

```bash
# List listening ports
ss -tlnp          # TCP
ss -ulnp          # UDP
ss -tunap         # All with process info

# Check specific port
ss -tlnp | grep :80

# Test port connectivity
nc -zv host 80
telnet host 80
timeout 2 bash -c "</dev/tcp/host/80" && echo "Open" || echo "Closed"
```

### TCP Connection States

```bash
# View connections by state
ss -tan state established
ss -tan state syn-sent
ss -tan state time-wait

# Count connections by state
ss -tan | awk '{print $1}' | sort | uniq -c

# Monitor connection attempts
tcpdump -i any 'tcp[tcpflags] & tcp-syn != 0'
```

### Firewall Troubleshooting

```bash
# View firewall rules
iptables -L -n -v
iptables -L INPUT -n -v --line-numbers
nft list ruleset

# Check default policies
iptables -L | grep policy

# Add allow rule
iptables -A INPUT -p tcp --dport 80 -j ACCEPT

# Test with logging
iptables -I INPUT -p tcp --dport 22 -j LOG --log-prefix "SSH: "
journalctl -f | grep SSH

# Connection tracking
sysctl net.netfilter.nf_conntrack_max
sysctl net.netfilter.nf_conntrack_count
```

### TCP Performance

```bash
# View TCP info for connections
ss -tin

# Key metrics:
# - rtt: Round trip time
# - cwnd: Congestion window
# - ssthresh: Slow start threshold
# - retrans: Retransmissions

# Check TCP parameters
sysctl -a | grep tcp

# Important tunables:
sysctl net.ipv4.tcp_rmem          # Receive buffer
sysctl net.ipv4.tcp_wmem          # Send buffer
sysctl net.ipv4.tcp_window_scaling
sysctl net.ipv4.tcp_timestamps
```

---

## Troubleshooting Workflows

### Workflow 1: Cannot Connect to Service

```bash
#!/bin/bash
# Layer 3-4 connectivity diagnostic

HOST="$1"
PORT="$2"

echo "=== Testing connectivity to $HOST:$PORT ==="

# Step 1: DNS resolution
echo -n "DNS resolution: "
if IP=$(dig +short "$HOST" | head -1); then
    echo "✓ $HOST → $IP"
else
    echo "✗ DNS failed"
    exit 1
fi

# Step 2: Ping test
echo -n "ICMP ping: "
if ping -c 2 -W 2 "$IP" &>/dev/null; then
    echo "✓ Host reachable"
else
    echo "✗ Host unreachable"
    echo "→ Check routing: ip route get $IP"
    exit 1
fi

# Step 3: Port test
echo -n "Port $PORT: "
if nc -zv -w 2 "$IP" "$PORT" 2>&1 | grep -q succeeded; then
    echo "✓ Port open"
else
    echo "✗ Port closed/filtered"
    echo "→ Check: firewall, service status"
    exit 1
fi

# Step 4: TCP handshake
echo -n "TCP handshake: "
if timeout 5 bash -c "</dev/tcp/$IP/$PORT" 2>/dev/null; then
    echo "✓ Connection successful"
else
    echo "✗ Connection failed"
    echo "→ Capture traffic: tcpdump -i any host $IP and port $PORT"
fi
```

### Workflow 2: High Latency/Packet Loss

```bash
#!/bin/bash
# Network performance diagnostic

TARGET="$1"

echo "=== Network Performance Test to $TARGET ==="

# Ping test
echo "Running ping test (100 packets)..."
ping -c 100 -i 0.2 "$TARGET" | tail -3

# MTR test
echo ""
echo "Running MTR (50 cycles)..."
mtr --report --report-cycles 50 "$TARGET"

# Check local interface
echo ""
echo "Local interface statistics:"
ip -s link show | grep -A 3 "state UP"
```

---

## Quick Reference

### Layer 3 Commands

| Task | Command |
|------|---------|
| Show IPs | `ip addr show` |
| Show routes | `ip route show` |
| Test route | `ip route get 8.8.8.8` |
| Ping | `ping -c 4 host` |
| Traceroute | `traceroute -n host` |
| MTR | `mtr --report host` |
| MTU test | `ping -M do -s 1472 host` |

### Layer 4 Commands

| Task | Command |
|------|---------|
| Listening ports | `ss -tlnp` |
| All connections | `ss -tunap` |
| Port test | `nc -zv host port` |
| Firewall rules | `iptables -L -n -v` |
| Connection states | `ss -tan state established` |
| TCP info | `ss -tin` |

### Common Issues

| Symptom | Layer | First Check |
|---------|-------|-------------|
| Cannot ping | L3 | `ip route get IP` |
| Ping works, port closed | L4 | `ss -tlnp \| grep PORT` |
| Connection timeout | L3/L4 | `traceroute`, `tcpdump` |
| High latency | L3 | `mtr --report` |
| Packet loss | L3 | `ping -c 100` |
| Port filtered | L4 | `iptables -L -n -v` |
