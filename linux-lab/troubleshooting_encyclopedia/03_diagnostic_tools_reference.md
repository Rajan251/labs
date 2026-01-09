# Advanced Diagnostic Tools Reference

Comprehensive guide to Linux diagnostic and performance analysis tools.

---

## System Health Tools

### Quick Assessment (< 30 seconds)

```bash
# System overview
uptime                    # Load average and uptime
dmesg -T | tail -20      # Recent kernel messages
journalctl --since "5 minutes ago" -p err  # Recent errors

# Resource snapshot
free -h                   # Memory usage
df -h                     # Disk usage
ip -s link               # Network interface stats
ss -s                    # Socket statistics
```

### CPU Monitoring

| Tool | Best For | Command Example |
|------|----------|-----------------|
| `top` | Interactive overview | `top -b -n 1` |
| `htop` | Colorful interactive | `htop` |
| `mpstat` | Per-core statistics | `mpstat -P ALL 1 5` |
| `pidstat` | Per-process CPU | `pidstat -u 1 10` |
| `perf` | Deep profiling | `perf top` |

```bash
# CPU usage by core
mpstat -P ALL 1 5

# Top CPU consumers
ps aux --sort=-%cpu | head -10

# CPU info
lscpu
cat /proc/cpuinfo
```

### Memory Monitoring

```bash
# Memory overview
free -h

# Detailed memory info
cat /proc/meminfo

# Per-process memory
ps aux --sort=-%mem | head -10
pmap -x PID

# Memory trends
vmstat 1 10

# Kernel memory
slabtop -o
```

### Disk I/O Monitoring

```bash
# I/O statistics
iostat -x 1 5

# Per-process I/O
iotop -o

# Disk usage
df -h
df -i                    # Inodes

# Large files
du -sh /* | sort -rh | head -10
find / -xdev -type f -size +100M -exec ls -lh {} \;

# I/O wait
vmstat 1 5 | awk '{print $16}'  # wa column
```

---

## Network Diagnostic Tools

### Connectivity Testing

```bash
# Basic connectivity
ping -c 4 host

# Continuous monitoring
mtr --report --report-cycles 100 host

# Path discovery
traceroute -n host
tcptraceroute host 443

# Bandwidth testing
iperf3 -c server -t 30
```

### Socket Analysis

```bash
# Modern socket statistics
ss -tunap                 # All TCP/UDP with processes
ss -tlnp                  # Listening TCP ports
ss -tan state established # Established connections
ss -tin                   # TCP with internal info

# Legacy netstat
netstat -tunap
netstat -s                # Statistics
```

### Packet Capture

```bash
# Basic capture
tcpdump -i eth0 -w capture.pcap

# Specific traffic
tcpdump -i eth0 'host 192.168.1.100 and port 80'
tcpdump -i eth0 'tcp port 443'
tcpdump -i eth0 icmp

# Read capture
tcpdump -r capture.pcap -n
tcpdump -r capture.pcap 'tcp port 80' -A

# Capture with snaplen
tcpdump -i eth0 -s 65535 -w full-capture.pcap

# Rotate captures
tcpdump -i eth0 -w capture.pcap -G 300 -W 12
```

### Bandwidth Monitoring

```bash
# Real-time bandwidth
iftop -i eth0
nload eth0
bmon

# Per-process bandwidth
nethogs eth0

# Interface statistics
sar -n DEV 1 10
ip -s link show eth0

# Network throughput
iperf3 -c server -t 60 -i 5
```

---

## Performance Profiling Tools

### perf - CPU Profiling

```bash
# System-wide statistics
perf stat -a sleep 10

# CPU profiling
perf record -F 99 -ag -- sleep 30
perf report --stdio

# Real-time top
perf top

# Specific events
perf list                 # List available events
perf record -e cpu-cycles -ag -- sleep 10

# Flame graph generation
perf record -F 99 -ag -- sleep 30
perf script | stackcollapse-perf.pl | flamegraph.pl > perf.svg
```

### strace - System Call Tracing

```bash
# Trace command
strace ls -l

# Attach to running process
strace -p PID

# Follow forks
strace -f command

# Filter system calls
strace -e trace=file command      # File operations
strace -e trace=network command   # Network operations
strace -e trace=process command   # Process operations

# Summary statistics
strace -c command

# Time spent in syscalls
strace -T command

# Output to file
strace -o output.txt command
```

### ltrace - Library Call Tracing

```bash
# Trace library calls
ltrace command

# Attach to process
ltrace -p PID

# Count calls
ltrace -c command

# Filter specific libraries
ltrace -l libssl.so command
```

### eBPF/BCC Tools

```bash
# Process execution
execsnoop-bpfcc

# File opens
opensnoop-bpfcc

# TCP connections
tcpconnect-bpfcc
tcplife-bpfcc

# Block I/O
biosnoop-bpfcc
biolatency-bpfcc

# Network latency
tcpretrans-bpfcc
```

---

## Log Analysis Tools

### journalctl

```bash
# Recent logs
journalctl -n 50

# Follow logs
journalctl -f

# Time-based filtering
journalctl --since "2024-01-01"
journalctl --since "1 hour ago"
journalctl --since yesterday
journalctl --until "10 minutes ago"

# Priority filtering
journalctl -p err
journalctl -p warning..emerg

# Unit filtering
journalctl -u nginx
journalctl -u docker.service --since today

# Boot-specific
journalctl -b           # Current boot
journalctl -b -1        # Previous boot
journalctl --list-boots

# Output formats
journalctl -o json
journalctl -o json-pretty
journalctl -o cat       # Only messages

# Field filtering
journalctl _PID=1234
journalctl _UID=1000
```

### Log Parsing

```bash
# grep for patterns
grep -E "ERROR|FATAL" /var/log/app.log
grep -c "pattern" *.log

# awk for field extraction
awk '/ERROR/ {print $1, $2, $5}' app.log
awk '{sum+=$10} END {print sum}' access.log

# sed for transformation
sed -n '/ERROR/,/END/p' app.log

# Count occurrences
sort | uniq -c | sort -rn

# Time-based analysis
awk '{print $1}' access.log | sort | uniq -c
```

---

## Troubleshooting Workflows

### 5-Minute Quick Diagnostic

```bash
#!/bin/bash
echo "=== 5-Minute System Diagnostic ==="

# Minute 1: System overview
echo "1. System Overview:"
uptime
dmesg -T | tail -5

# Minute 2: Resources
echo "2. Resource Usage:"
free -h | grep Mem:
df -h / | tail -1
mpstat 1 3 | tail -1

# Minute 3: Network
echo "3. Network Status:"
ip addr show | grep "inet "
ss -s

# Minute 4: Services
echo "4. Critical Services:"
systemctl is-active sshd nginx mysql 2>/dev/null

# Minute 5: Recent errors
echo "5. Recent Errors:"
journalctl --since "5 minutes ago" -p err --no-pager | tail -10
```

### Performance Baseline Collection

```bash
#!/bin/bash
BASELINE_DIR="/var/log/baselines"
DATE=$(date +%Y%m%d-%H%M%S)
mkdir -p "$BASELINE_DIR"

echo "Collecting performance baseline..."

# CPU
mpstat 1 60 > "$BASELINE_DIR/cpu-$DATE.log" &

# Memory
vmstat 1 60 > "$BASELINE_DIR/memory-$DATE.log" &

# Disk I/O
iostat -x 1 60 > "$BASELINE_DIR/io-$DATE.log" &

# Network
sar -n DEV 1 60 > "$BASELINE_DIR/network-$DATE.log" &

wait
echo "Baseline saved to $BASELINE_DIR"
```

---

## Quick Reference

### Tool Selection Guide

| Symptom | Tool | Command |
|---------|------|---------|
| High load | `top`, `htop` | `top` |
| CPU spike | `perf`, `pidstat` | `perf top` |
| Memory leak | `ps`, `pmap` | `ps aux --sort=-%mem` |
| Disk slow | `iostat`, `iotop` | `iostat -x 1 5` |
| Network slow | `iftop`, `nethogs` | `iftop -i eth0` |
| Service down | `systemctl`, `journalctl` | `systemctl status service` |
| Port closed | `ss`, `netstat` | `ss -tlnp` |
| DNS issues | `dig`, `nslookup` | `dig example.com` |

### Essential One-Liners

```bash
# Top 10 CPU processes
ps aux --sort=-%cpu | head -10

# Top 10 memory processes
ps aux --sort=-%mem | head -10

# Disk usage by directory
du -sh /* | sort -rh | head -10

# Network connections by state
ss -tan | awk '{print $1}' | sort | uniq -c

# Recent errors
journalctl --since "10 minutes ago" -p err --no-pager

# Active connections count
ss -tan | grep ESTAB | wc -l

# Check all listening ports
ss -tlnp | grep LISTEN

# Find deleted but open files
lsof | grep deleted
```
