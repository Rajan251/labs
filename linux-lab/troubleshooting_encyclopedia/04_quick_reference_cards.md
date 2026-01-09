# Quick Reference Cards & Cheat Sheets

Essential commands and workflows for rapid troubleshooting.

---

## 🚨 Emergency Quick Diagnostic

```bash
# Run this first when troubleshooting any issue
echo "=== Emergency Diagnostic $(date) ==="
echo "Load: $(uptime | awk -F'load average:' '{print $2}')"
echo "Memory: $(free -h | grep Mem: | awk '{print $3"/"$2}')"
echo "Disk: $(df -h / | tail -1 | awk '{print $5" used"}')"
echo "Errors: $(journalctl --since "5 min ago" -p err --no-pager | wc -l) in last 5 min"
ss -s | grep TCP:
```

---

## Layer-by-Layer Quick Commands

### Layer 1-2: Physical/Data Link

```bash
ip link show eth0                    # Interface status
ethtool eth0 | grep "Link detected"  # Physical link
ethtool -S eth0 | grep error         # Error counters
ip neigh show                        # ARP table
arping -I eth0 -c 3 192.168.1.1     # Test ARP
```

### Layer 3: Network

```bash
ip addr show                         # IP addresses
ip route show                        # Routing table
ip route get 8.8.8.8                # Test route
ping -c 4 8.8.8.8                   # Connectivity
traceroute -n 8.8.8.8               # Path
mtr --report -c 50 8.8.8.8          # Continuous test
```

### Layer 4: Transport

```bash
ss -tlnp                            # Listening TCP ports
ss -tunap                           # All connections
ss -tan state established           # Active connections
nc -zv host 80                      # Port test
iptables -L -n -v                   # Firewall rules
```

### Layer 7: Application

```bash
dig example.com +short              # DNS lookup
curl -I http://example.com          # HTTP test
curl -v https://example.com         # HTTPS verbose
openssl s_client -connect host:443  # TLS test
systemctl status service            # Service status
journalctl -u service -n 50         # Service logs
```

---

## Common Problem Quick Fixes

### Cannot Connect to Server

```bash
# 1. Can you ping?
ping -c 3 server_ip
# No → Check Layer 1-3
# Yes → Continue

# 2. Is port open?
nc -zv server_ip port
# No → Check firewall/service
# Yes → Continue

# 3. Can you connect?
telnet server_ip port
curl -v http://server_ip:port
```

### High Load Average

```bash
# 1. Check what's causing load
uptime                              # Current load
mpstat 1 3                          # CPU usage
iostat -x 1 3                       # I/O wait
ps aux --sort=-%cpu | head -10      # CPU hogs
ps aux --sort=-%mem | head -10      # Memory hogs
```

### Disk Full

```bash
# 1. Check usage
df -h                               # Disk space
df -i                               # Inodes

# 2. Find large files
du -sh /* | sort -rh | head -10
find / -xdev -type f -size +100M

# 3. Find deleted but open files
lsof | grep deleted
```

### Network Slow

```bash
# 1. Test bandwidth
iperf3 -c server -t 30

# 2. Check latency
ping -c 100 server | tail -3
mtr --report -c 50 server

# 3. Check interface
ip -s link show eth0
ethtool -S eth0 | grep -E "error|drop"
```

### DNS Not Working

```bash
# 1. Check configuration
cat /etc/resolv.conf

# 2. Test DNS servers
dig @8.8.8.8 example.com
dig @1.1.1.1 example.com

# 3. Flush cache
resolvectl flush-caches
systemctl restart systemd-resolved
```

---

## One-Liner Diagnostics

```bash
# Top 10 CPU processes
ps aux --sort=-%cpu | head -10

# Top 10 memory processes
ps aux --sort=-%mem | head -10

# Disk usage by directory
du -sh /* 2>/dev/null | sort -rh | head -10

# Network connections by state
ss -tan | awk '{print $1}' | sort | uniq -c

# Recent errors (last 10 min)
journalctl --since "10 min ago" -p err --no-pager

# Listening ports
ss -tlnp | grep LISTEN

# Established connections count
ss -tan | grep ESTAB | wc -l

# Check all failed services
systemctl list-units --state=failed

# Find large files
find / -xdev -type f -size +100M -exec ls -lh {} \; 2>/dev/null

# Deleted but open files
lsof +L1

# Connection tracking usage
echo "$(cat /proc/sys/net/netfilter/nf_conntrack_count) / $(cat /proc/sys/net/netfilter/nf_conntrack_max)"
```

---

## Troubleshooting Decision Matrix

| Symptom | First Command | If Fails | If Passes |
|---------|---------------|----------|-----------|
| Cannot connect | `ping host` | Check L1-3 | Check port: `nc -zv host port` |
| Slow response | `mtr host` | Check path | Check app: `curl -w time_total` |
| High load | `uptime` | Check: `top`, `iostat` | Identify process |
| Out of memory | `free -h` | Check: `ps aux --sort=-%mem` | Check for leaks |
| Disk full | `df -h` | Find large: `du -sh /*` | Clean up |
| DNS fails | `dig host` | Check: `/etc/resolv.conf` | Try different DNS |
| Port closed | `ss -tlnp` | Start service | Check firewall |
| Service down | `systemctl status` | Check logs | Restart service |

---

## Performance Baseline Checklist

```bash
# CPU
echo "CPU: $(nproc) cores"
mpstat 1 3 | tail -1

# Memory
free -h | grep Mem:

# Disk
df -h /
iostat -x 1 3 | grep -v "^$" | tail -n +4

# Network
ip -s link show | grep -A 3 "state UP"
ss -s

# Load
uptime

# Processes
echo "Processes: $(ps aux | wc -l)"
echo "Threads: $(ps -eLf | wc -l)"
```

---

## Critical System Checks

```bash
#!/bin/bash
# Run this for comprehensive system health check

echo "=== CRITICAL SYSTEM CHECKS ==="

# 1. System resources
echo "1. Resources:"
echo "  Load: $(uptime | awk -F'load average:' '{print $2}')"
echo "  Memory: $(free -h | grep Mem: | awk '{print $3"/"$2" ("$5" available)"}')"
echo "  Disk: $(df -h / | tail -1 | awk '{print $3"/"$2" ("$5" used)"}')"

# 2. Network connectivity
echo "2. Network:"
if ping -c 2 -W 2 8.8.8.8 &>/dev/null; then
    echo "  ✓ Internet reachable"
else
    echo "  ✗ Internet unreachable"
fi

# 3. Critical services
echo "3. Services:"
for svc in sshd nginx mysql docker; do
    if systemctl is-active --quiet $svc 2>/dev/null; then
        echo "  ✓ $svc running"
    else
        echo "  ✗ $svc not running"
    fi
done

# 4. Recent errors
ERROR_COUNT=$(journalctl --since "5 min ago" -p err --no-pager 2>/dev/null | wc -l)
echo "4. Errors: $ERROR_COUNT in last 5 minutes"

# 5. Failed units
FAILED=$(systemctl list-units --state=failed --no-pager 2>/dev/null | grep -c failed)
echo "5. Failed services: $FAILED"
```

---

## Tool Selection Quick Guide

| Need | Tool | Command |
|------|------|---------|
| **Quick overview** | `uptime`, `free`, `df` | `uptime && free -h && df -h` |
| **CPU usage** | `top`, `htop` | `top` or `htop` |
| **Memory details** | `free`, `vmstat` | `free -h && vmstat 1 5` |
| **Disk I/O** | `iostat`, `iotop` | `iostat -x 1 5` |
| **Network bandwidth** | `iftop`, `nethogs` | `iftop -i eth0` |
| **Connections** | `ss`, `netstat` | `ss -tunap` |
| **Packet capture** | `tcpdump` | `tcpdump -i eth0 -w file.pcap` |
| **DNS lookup** | `dig`, `nslookup` | `dig example.com` |
| **HTTP test** | `curl`, `wget` | `curl -v http://example.com` |
| **Port test** | `nc`, `telnet` | `nc -zv host port` |
| **Process trace** | `strace`, `ltrace` | `strace -p PID` |
| **System logs** | `journalctl` | `journalctl -f` |

---

## Emergency Procedures

### Server Unresponsive

```bash
# 1. Check if you can login
ssh server

# 2. Check load
uptime

# 3. Check what's running
top -b -n 1 | head -20

# 4. Check disk
df -h

# 5. Check memory
free -h

# 6. Recent errors
journalctl --since "10 min ago" -p err --no-pager | tail -20
```

### Network Down

```bash
# 1. Check interface
ip link show

# 2. Bring up if down
ip link set eth0 up

# 3. Check IP
ip addr show eth0

# 4. Check gateway
ip route show default

# 5. Test connectivity
ping -c 3 $(ip route show default | awk '{print $3}')
```

### Service Crashed

```bash
# 1. Check status
systemctl status service_name

# 2. Check logs
journalctl -u service_name -n 100 --no-pager

# 3. Restart
systemctl restart service_name

# 4. Verify
systemctl status service_name
curl -I http://localhost:port
```

---

## Bookmarkable Commands

```bash
# Save these as aliases in ~/.bashrc

alias syshealth='echo "Load: $(uptime | awk -F"load average:" "{print \$2}") | Mem: $(free -h | grep Mem: | awk "{print \$3\"/\"\$2}") | Disk: $(df -h / | tail -1 | awk "{print \$5}")"'

alias topcpu='ps aux --sort=-%cpu | head -10'

alias topmem='ps aux --sort=-%mem | head -10'

alias netstat='ss -tunap'

alias ports='ss -tlnp | grep LISTEN'

alias errors='journalctl --since "10 min ago" -p err --no-pager'

alias diskusage='du -sh /* 2>/dev/null | sort -rh | head -10'
```

---

**Quick Tip**: Print this page and keep it near your workstation for rapid reference during incidents!
