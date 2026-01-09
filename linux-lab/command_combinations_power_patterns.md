# Command Combinations & Power Patterns

**Level:** Expert / SRE / Power User  
**Focus:** Powerful command chains, one-liners, and context-aware troubleshooting

---

## 1. THE ART OF COMMAND CHAINING

### 1.1 System Health Snapshot
```bash
# Complete system state in one command
{
    echo "=== $(date) ==="
    uptime
    echo
    free -h
    echo
    df -h
    echo
    ss -tlnp
    echo
    journalctl --since "5 minutes ago" -p err
} > /tmp/health_$(date +%s).log
```

### 1.2 Process Investigation Chain
```bash
# Find and investigate problematic processes
pid=$(ps aux | grep -v grep | grep nginx | awk '{print $2}')
[ -n "$pid" ] && echo "Found PID: $pid" && \
    cat /proc/$pid/status && \
    lsof -p $pid | head -20 && \
    strace -p $pid -c 2>&1 | tail -5
```

---

## 2. ARGUMENT COMBINATION PATTERNS

### 2.1 The "Reveal Everything" Pattern
```bash
# Progression of verbosity
command              # Basic output
command -v           # Verbose
command -vv          # More verbose
command -vvv         # Maximum verbose
command --debug      # Debug mode
strace command       # System call trace
```

### 2.2 The "Filter & Format" Pattern
```bash
# Complete data pipeline
command [action] | \
    grep [filter] | \
    awk '{print $2,$5}' | \
    sort | \
    uniq -c | \
    sort -rn

# Example: Top CPU processes
ps aux | \
    grep -v grep | \
    awk '{print $3, $11}' | \
    sort -rn | \
    head -10
```

### 2.3 The "Compare & Contrast" Pattern
```bash
# Before/After comparison
command > /tmp/before.txt
# [make change]
command > /tmp/after.txt
diff -u /tmp/before.txt /tmp/after.txt | colordiff

# Or use process substitution
diff -u <(command --before) <(command --after)
```

---

## 3. SPECIALIZED TROUBLESHOOTING COMBINATIONS

### 3.1 Network Diagnostics Stack
```bash
# Layer-by-layer network test
{
    echo "1. Interface: $(ip addr show eth0 | grep 'state')"
    echo "2. Route: $(ip route get 8.8.8.8)"
    echo "3. Ping: $(ping -c 2 -W 1 8.8.8.8 2>&1 | tail -1)"
    echo "4. DNS: $(dig +short google.com A | head -1)"
    echo "5. TCP: $(timeout 2 bash -c '</dev/tcp/google.com/80' && echo 'OK' || echo 'FAIL')"
    echo "6. HTTP: $(curl -sI http://google.com | head -1)"
} 2>&1
```

### 3.2 Filesystem Issue Isolation
```bash
# Top disk/inode consumers
echo "=== Top 10 directories by size ==="
du -h --max-depth=1 / 2>/dev/null | sort -rh | head -10

echo -e "\n=== Top 10 directories by inode count ==="
find / -xdev -printf '%h\n' 2>/dev/null | \
    sort | uniq -c | sort -rn | head -10
```

### 3.3 Performance Bottleneck Identification
```bash
# Real-time correlation view
watch -n1 -d '
    echo "CPU: $(uptime)"
    echo "Memory: $(free -h | grep Mem)"
    echo "IO: $(iostat -x 1 2 | tail -5)"
'
```

---

## 4. TIME-BASED ARGUMENT MAGIC

### 4.1 Temporal Analysis
```bash
# Last hour's errors
journalctl --since "1 hour ago" -p err..alert

# Errors between specific times
journalctl --since "today 09:00" --until "today 17:00" -p err

# Real-time with timestamp
tail -f /var/log/syslog | \
    while read line; do
        echo "$(date '+%H:%M:%S') $line"
    done
```

### 4.2 Process Timeline Reconstruction
```bash
# Process history
ps -eo pid,comm,lstart,etime | grep nginx

# Processes started in last 10 minutes
ps -eo pid,comm,lstart | \
    awk -v limit="$(date -d '10 minutes ago' +'%a %b %d %H:%M:%S %Y')" \
    '$3" "$4" "$5" "$6" "$7 >= limit'
```

---

## 5. ADVANCED OUTPUT MANIPULATION

### 5.1 Column Magic
```bash
# Clean tabular output
command | column -t -s $'\t'

# Fixed width columns
command | awk '{printf "%-20s %-10s %-15s\n", $1, $2, $3}'

# Multi-line to single line
command | paste -sd ','
```

### 5.2 Color Coding
```bash
# Highlight errors and warnings
command 2>&1 | \
    grep --color -E '(ERROR|error|Error)|(WARNING|warning|Warning)'

# AWK color coding
command | awk '
    /ERROR/ {print "\033[31m" $0 "\033[0m"}
    /WARNING/ {print "\033[33m" $0 "\033[0m"}
    !/ERROR|WARNING/ {print}
'
```

### 5.3 JSON Processing
```bash
# Parse and format JSON
command --json | \
    jq -r '.items[] | select(.status == "error") | "\(.timestamp): \(.message)"'
```

---

## 6. CONTEXT-AWARE TROUBLESHOOTING

### 6.1 Environment Detection
```bash
# Auto-detect environment
detect_environment() {
    # Distribution
    if [[ -f /etc/redhat-release ]]; then
        echo "RHEL/CentOS: $(cat /etc/redhat-release)"
    elif [[ -f /etc/debian_version ]]; then
        echo "Debian/Ubuntu: $(cat /etc/debian_version)"
    fi
    
    # Cloud provider
    if curl -s --connect-timeout 2 http://169.254.169.254/latest/meta-data/ 2>/dev/null; then
        echo "AWS EC2"
    fi
    
    # Container
    if [[ -f /.dockerenv ]] || grep -q docker /proc/1/cgroup 2>/dev/null; then
        echo "Container environment"
    fi
}
```

### 6.2 Memory-Constrained Environments
```bash
# Check available memory
AVAIL_MEM=$(free -m | awk '/^Mem:/ {print $7}')
if [[ $AVAIL_MEM -lt 100 ]]; then
    echo "Low memory - use lightweight commands"
    # Use awk instead of grep -P
    # Use find -exec instead of xargs
fi
```

---

## 7. TROUBLESHOOTING RECIPES

### 7.1 What Changed?
```bash
what_changed() {
    local since="$1"
    local until="${2:-now}"
    
    echo "=== Files changed ==="
    find /etc -type f -newermt "$since" ! -newermt "$until" 2>/dev/null
    
    echo -e "\n=== Packages installed ==="
    rpm -qa --last | head -20
    
    echo -e "\n=== System logs ==="
    journalctl --since "$since" --until "$until" -p warning..emerg
}

# Usage: what_changed "2 hours ago"
```

### 7.2 Quick Performance Check
```bash
quick_perf() {
    echo "Load: $(uptime)"
    echo "Memory: $(free -h | awk '/^Mem:/ {print $3"/"$2 " ("$3/$2*100"%)"}')"
    echo "Disk: $(df -h / | awk 'NR==2 {print $3"/"$2 " ("$5")"}')"
    echo "Top CPU: $(ps aux --sort=-%cpu | head -2 | tail -1 | awk '{print $11}')"
}
```

### 7.3 Network Connectivity Test
```bash
network_test() {
    local host=$1
    echo "Testing $host"
    echo -n "Ping: " && ping -c2 -W1 $host >/dev/null 2>&1 && echo "OK" || echo "FAIL"
    echo -n "DNS: " && host $host >/dev/null 2>&1 && echo "OK" || echo "FAIL"
    echo -n "Port 80: " && nc -z -w2 $host 80 2>/dev/null && echo "OK" || echo "FAIL"
}
```

---

## 8. SAFETY-FIRST PATTERNS

### 8.1 Dry Run Everywhere
```bash
# Standard dry-run flags
rsync --dry-run -av source/ dest/
apt-get --simulate upgrade
ansible-playbook --check playbook.yml
terraform plan  # Not apply

# Universal safety check
if [[ "$1" != "--dry-run" ]]; then
    echo "Add --dry-run to test first"
    exit 1
fi
```

### 8.2 Confirmation Prompts
```bash
# Interactive confirmation
rm -i file.txt          # Prompt before delete
cp -i source dest       # Prompt before overwrite

# Force without prompt (use carefully!)
rm -f file.txt          # Force, no questions
yes | command           # Auto-yes to all prompts
```

---

## 9. CONTEXT-SPECIFIC GOTCHAS

### 9.1 Virtual Machine Issues
```bash
# Check if in VM
if [[ $(systemd-detect-virt 2>/dev/null) != "none" ]]; then
    echo "Running in $(systemd-detect-virt)"
    
    # VM-specific checks
    chronyc sources || ntpq -p  # Clock drift
    cat /proc/meminfo | grep -i balloon  # Balloon driver
fi
```

### 9.2 Container-Specific
```bash
# Container detection
if [[ -f /.dockerenv ]] || grep -q docker /proc/1/cgroup 2>/dev/null; then
    echo "Container detected"
    
    # Check resource limits
    cat /sys/fs/cgroup/memory/memory.limit_in_bytes
    cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us
fi
```

---

## 10. MEMORIZATION TECHNIQUES

### 10.1 Flag Families
```
-v, -vv, -vvv   : Increasing verbosity
-q, -qq, -qqq   : Increasing quietness
-f, -F          : File-related
-r, -R          : Recursive
-i, -I          : Interactive or ignore
```

### 10.2 Common Patterns
```
-h/--help       : Help
-v/--version    : Version
-V/--verbose    : Verbose
-q/--quiet      : Quiet
-f/--file       : File input/output
-o/--output     : Output file
```

---

## 11. QUICK REFERENCE: FIRST 60 SECONDS

```bash
# Run these immediately when investigating
uptime                    # Load average
dmesg | tail             # Kernel messages
vmstat 1 5               # System stats
mpstat -P ALL 1          # CPU per core
pidstat 1                # Process stats
iostat -xz 1             # Disk I/O
free -m                  # Memory
sar -n DEV 1             # Network
top                      # Overview
```

---

## 12. CONTEXT-AWARE SCRIPT TEMPLATE

```bash
#!/bin/bash
# context_aware_troubleshoot.sh

# Gather context
CONTEXT_FILE="/tmp/context_$(date +%s).txt"
{
    echo "=== Context ==="
    echo "Time: $(date)"
    echo "User: $(whoami)"
    echo "Host: $(hostname)"
    echo "Distro: $(cat /etc/os-release 2>/dev/null | grep PRETTY_NAME)"
    echo "Uptime: $(uptime)"
    echo "Load: $(cat /proc/loadavg)"
    echo "Memory: $(free -h | grep Mem:)"
    echo "Disk: $(df -h / | grep -v Filesystem)"
} > "$CONTEXT_FILE"

echo "Context saved to $CONTEXT_FILE"

# Suggest commands based on problem
read -p "Describe problem (slow/error/connection): " problem

case $problem in
    *slow*)
        echo "Suggested: top, vmstat 1 10, iostat -x 1 10"
        ;;
    *error*)
        echo "Suggested: journalctl -p err, dmesg | tail, grep -i error /var/log/*.log"
        ;;
    *connection*)
        echo "Suggested: ss -tlnp, netstat -s, ping"
        ;;
esac
```

---

## 13. SMART ALIASES

```bash
# Context-adaptive aliases
alias psg='ps aux --sort=-%mem | head -20'
alias dfl='df -hT | grep -v tmpfs'
alias ports='ss -tulpn'
alias errors='journalctl -p err -n 50'
alias load='uptime && free -h && df -h /'

# Function aliases
helpme() {
    case $1 in
        network) ip addr show; ss -tlnp ;;
        disk) df -hT | grep -v tmpfs ;;
        memory) free -h; ps aux --sort=-%mem | head -10 ;;
        *) echo "Usage: helpme [network|disk|memory]" ;;
    esac
}
```
