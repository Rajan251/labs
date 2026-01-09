# Layer 1-2: Physical and Data Link Troubleshooting

Complete guide to diagnosing and resolving physical and data link layer network issues.

---

## Layer 1: Physical Layer

### Quick Diagnostic Commands

```bash
# Check interface status
ip link show eth0

# Check physical link
ethtool eth0 | grep "Link detected"

# Check for errors
ethtool -S eth0 | grep -E "error|crc|collision"

# Check kernel messages
dmesg | grep -i eth0 | tail -20
```

### Common Symptoms & Solutions

| Symptom | Command | Fix |
|---------|---------|-----|
| No link light | `ethtool eth0` | Check cable, try different port |
| Slow speed | `ethtool eth0 \| grep Speed` | Fix duplex mismatch |
| High errors | `ethtool -S eth0` | Replace cable |
| Interface flapping | `dmesg -w` | Check physical connection |

### Speed/Duplex Configuration

```bash
# Check current settings
ethtool eth0 | grep -E "Speed|Duplex|Auto"

# Enable auto-negotiation (recommended)
ethtool -s eth0 autoneg on

# Manual configuration
ethtool -s eth0 speed 1000 duplex full autoneg off

# Make persistent (Debian/Ubuntu)
cat >> /etc/network/interfaces <<EOF
post-up /sbin/ethtool -s eth0 speed 1000 duplex full
EOF
```

---

## Layer 2: Data Link Layer

### ARP Troubleshooting

```bash
# View ARP table
ip neigh show

# Test ARP resolution
arping -I eth0 -c 3 192.168.1.1

# Detect IP conflicts
arping -D -I eth0 -c 2 192.168.1.100

# Clear ARP cache
ip neigh flush all

# Monitor ARP traffic
tcpdump -i eth0 arp -n
```

### VLAN Configuration

```bash
# Create VLAN interface
ip link add link eth0 name eth0.100 type vlan id 100
ip addr add 192.168.100.10/24 dev eth0.100
ip link set dev eth0.100 up

# Verify VLAN
ip -d link show eth0.100

# Test connectivity
ping -I eth0.100 192.168.100.1

# Remove VLAN
ip link del eth0.100
```

### Bonding/LACP

```bash
# Check bonding status
cat /proc/net/bonding/bond0

# Key metrics to check:
# - MII Status: up
# - Speed/Duplex: matching
# - Aggregator ID: same for all slaves
# - Link Failure Count: 0 or low

# Add slave to bond
ifenslave bond0 eth1

# Remove slave from bond
ifenslave -d bond0 eth1
```

---

## Troubleshooting Workflows

### Workflow 1: No Connectivity

```bash
#!/bin/bash
# Physical layer diagnostic

IFACE="eth0"

echo "=== Layer 1/2 Diagnostic for $IFACE ==="

# Step 1: Interface exists and up?
if ! ip link show "$IFACE" | grep -q "state UP"; then
    echo "✗ Interface is DOWN"
    echo "→ Try: ip link set $IFACE up"
    exit 1
fi
echo "✓ Interface is UP"

# Step 2: Physical link detected?
if ! ethtool "$IFACE" | grep -q "Link detected: yes"; then
    echo "✗ No physical link"
    echo "→ Check: cable, switch port, NIC"
    exit 1
fi
echo "✓ Physical link detected"

# Step 3: Check for errors
ERRORS=$(ethtool -S "$IFACE" | grep -E "rx_errors|tx_errors" | awk '{sum+=$2} END {print sum}')
if [ "$ERRORS" -gt 100 ]; then
    echo "⚠️  High error count: $ERRORS"
    echo "→ Check: cable quality, interference"
fi

# Step 4: Speed/Duplex check
SPEED=$(ethtool "$IFACE" | grep Speed | awk '{print $2}')
DUPLEX=$(ethtool "$IFACE" | grep Duplex | awk '{print $2}')
echo "✓ Speed: $SPEED, Duplex: $DUPLEX"

# Step 5: ARP test to gateway
GATEWAY=$(ip route show default | awk '{print $3}')
if [ -n "$GATEWAY" ]; then
    if arping -I "$IFACE" -c 2 "$GATEWAY" &>/dev/null; then
        echo "✓ Can reach gateway via ARP"
    else
        echo "✗ Cannot reach gateway via ARP"
        echo "→ Check: VLAN, switch configuration"
    fi
fi
```

### Workflow 2: Intermittent Issues

```bash
# Monitor for interface flapping
ip monitor link dev eth0 &
MONITOR_PID=$!

# Watch for errors increasing
watch -n 5 'ethtool -S eth0 | grep -E "error|crc"'

# Kill monitor when done
kill $MONITOR_PID
```

---

## Quick Reference

### Essential Commands

| Task | Command |
|------|---------|
| Interface status | `ip link show` |
| Physical link | `ethtool eth0` |
| Error stats | `ethtool -S eth0` |
| ARP table | `ip neigh show` |
| Test ARP | `arping -I eth0 IP` |
| Create VLAN | `ip link add link eth0 name eth0.100 type vlan id 100` |
| Bonding status | `cat /proc/net/bonding/bond0` |

### Common Error Patterns

| Error Type | Meaning | Action |
|------------|---------|--------|
| rx_crc_errors | Bad cable/interference | Replace cable |
| collisions | Duplex mismatch | Fix duplex settings |
| rx_missed_errors | NIC overwhelmed | Increase ring buffer |
| tx_carrier_errors | Cable disconnected | Check physical connection |
