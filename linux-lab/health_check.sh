#!/bin/bash

# ==============================================================================
# Production System Health Check Script
# Role: Linux Administrator
# Description: Monitors vital system metrics and reports issues with context.
# Metrics: Load, Memory, Disk, Inodes, Zombies, Services, Security, Swap.
# ==============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}======================================================${NC}"
echo -e "${CYAN}   Production System Health Check Report   ${NC}"
echo -e "${CYAN}   Date: $(date)   ${NC}"
echo -e "${CYAN}======================================================${NC}"
echo ""

# ------------------------------------------------------------------------------
# 1. Load Averages
# ------------------------------------------------------------------------------
echo -e "${YELLOW}[+] Checking Load Averages...${NC}"
CORES=$(nproc)
LOAD_15=$(uptime | awk -F'load average:' '{ print $2 }' | awk -F, '{ print $3 }' | xargs)
LIMIT=$CORES

echo "    Cores: $CORES"
echo "    15m Load: $LOAD_15"

if (( $(echo "$LOAD_15 > $LIMIT" | bc -l) )); then
    echo -e "    ${RED}CRITICAL:${NC} Load average ($LOAD_15) exceeds core count ($CORES)."
    echo "    REMEDIATION: Check 'top' for CPU hogs. Consider scaling up CPU."
else
    echo -e "    ${GREEN}OK:${NC} Load is within limits."
fi
echo ""

# ------------------------------------------------------------------------------
# 2. Memory Usage
# ------------------------------------------------------------------------------
echo -e "${YELLOW}[+] Checking Memory Usage...${NC}"
# Use free command to get metrics in MB
TOTAL_MEM=$(free -m | awk '/^Mem:/{print $2}')
USED_MEM=$(free -m | awk '/^Mem:/{print $3}')
FREE_MEM=$(free -m | awk '/^Mem:/{print $4}')
CACHE_MEM=$(free -m | awk '/^Mem:/{print $6}')
AVAILABLE_MEM=$(free -m | awk '/^Mem:/{print $7}')

PERCENT_USED=$(awk "BEGIN {printf \"%.2f\", 100 * ($TOTAL_MEM - $AVAILABLE_MEM) / $TOTAL_MEM}")

echo "    Total: ${TOTAL_MEM}MB | Used (App): $((TOTAL_MEM - AVAILABLE_MEM))MB | Cache: ${CACHE_MEM}MB | Available: ${AVAILABLE_MEM}MB"
echo "    Usage: ${PERCENT_USED}%"

if (( $(echo "$PERCENT_USED > 90" | bc -l) )); then
    echo -e "    ${RED}WARNING:${NC} Memory usage is high (>90%)."
    echo "    REMEDIATION: Check for memory leaks. Validate resident set size (RSS) of top processes."
else
    echo -e "    ${GREEN}OK:${NC} Memory usage is normal."
fi
echo ""

# ------------------------------------------------------------------------------
# 3. Swap Activity
# ------------------------------------------------------------------------------
echo -e "${YELLOW}[+] Checking Swap Activity...${NC}"
SWAP_TOTAL=$(free -m | awk '/^Swap:/{print $2}')
SWAP_USED=$(free -m | awk '/^Swap:/{print $3}')

if [ "$SWAP_TOTAL" -gt 0 ]; then
    SWAP_PERCENT=$(awk "BEGIN {printf \"%.2f\", 100 * $SWAP_USED / $SWAP_TOTAL}")
    echo "    Swap Total: ${SWAP_TOTAL}MB | Used: ${SWAP_USED}MB ($SWAP_PERCENT%)"
    if (( $(echo "$SWAP_PERCENT > 20" | bc -l) )); then
        echo -e "    ${RED}WARNING:${NC} Significant swap usage detected."
        echo "    REMEDIATION: System is swapping. Performance will degrade. Add RAM or reduce load."
    else
        echo -e "    ${GREEN}OK:${NC} Swap usage is acceptable."
    fi
else
    echo "    Swap not enabled."
fi
echo ""

# ------------------------------------------------------------------------------
# 4. Disk Usage & Inodes
# ------------------------------------------------------------------------------
echo -e "${YELLOW}[+] Checking Disk Usage & Inodes...${NC}"

# Loop through real filesystems only
df -hP | grep '^/' | while read -r line; do
    FS=$(echo "$line" | awk '{print $1}')
    MOUNT=$(echo "$line" | awk '{print $6}')
    USAGE=$(echo "$line" | awk '{print $5}' | sed 's/%//')
    INODE_USAGE=$(df -iP "$FS" | awk 'NR==2 {print $5}' | sed 's/%//')

    if [ "$USAGE" -gt 85 ]; then
        echo -e "    ${RED}CRITICAL (Space):${NC} $MOUNT is at ${USAGE}% capacity."
        echo "    REMEDIATION: Clean up log files, remove old backups, or expand volume."
    elif [[ "$INODE_USAGE" =~ ^[0-9]+$ ]] && [ "$INODE_USAGE" -gt 85 ]; then
        echo -e "    ${RED}CRITICAL (Inodes):${NC} $MOUNT is at ${INODE_USAGE}% inode usage."
        echo "    REMEDIATION: Too many small files. Check session files or mail queues."
    else
        echo -e "    ${GREEN}OK:${NC} $MOUNT (Space: ${USAGE}%, Inodes: ${INODE_USAGE}%)"
    fi
done
echo ""

# ------------------------------------------------------------------------------
# 5. Zombie Processes
# ------------------------------------------------------------------------------
echo -e "${YELLOW}[+] Checking Zombie Processes...${NC}"
ZOMBIE_COUNT=$(ps aux | awk '{print $8}' | grep -c Z)
echo "    Count: $ZOMBIE_COUNT"

if [ "$ZOMBIE_COUNT" -gt 0 ]; then
    echo -e "    ${RED}WARNING:${NC} Zombie processes found."
    # Show parent PID of zombies
    ps -eo ppid,stat,cmd | grep 'Z' | grep -v grep | head -5
    echo "    REMEDIATION: Identify the parent process (PPID) above and kill/restart it if it fails to reap children."
else
    echo -e "    ${GREEN}OK:${NC} No zombies found."
fi
echo ""

# ------------------------------------------------------------------------------
# 6. Systemd Failed Services (Last 24h)
# ------------------------------------------------------------------------------
echo -e "${YELLOW}[+] Checking Failed Systemd Services...${NC}"
FAILED_SERVICES=$(systemctl list-units --state=failed --no-legend)

if [ -n "$FAILED_SERVICES" ]; then
    echo -e "    ${RED}CRITICAL:${NC} The following services are in a failed state:"
    echo "$FAILED_SERVICES"
    echo "    REMEDIATION: Run 'systemctl status <service>' and 'journalctl -u <service>' to investigate."
else
    echo -e "    ${GREEN}OK:${NC} No failed services detected."
fi
echo ""

# ------------------------------------------------------------------------------
# 7. Security: Failed Logins
# ------------------------------------------------------------------------------
echo -e "${YELLOW}[+] Checking Failed Login Attempts (Last 24h)...${NC}"
# Detect log file
if [ -f /var/log/auth.log ]; then
    LOG_FILE="/var/log/auth.log" # Debian/Ubuntu
elif [ -f /var/log/secure ]; then
    LOG_FILE="/var/log/secure"   # RHEL/CentOS
else
    LOG_FILE=""
fi

if [ -n "$LOG_FILE" ] && [ -r "$LOG_FILE" ]; then
    FAILED_COUNT=$(grep "Failed password" "$LOG_FILE" | grep "$(date +'%b %e')" | wc -l)
    echo "    Failed Attempts Today: $FAILED_COUNT"
    if [ "$FAILED_COUNT" -gt 50 ]; then
        echo -e "    ${RED}WARNING:${NC} High number of failed logins detected!"
        echo "    REMEDIATION: Check IPs in $LOG_FILE. Consider installing Fail2Ban and disabling password auth."
    else
        echo -e "    ${GREEN}OK:${NC} Failed login count is within normal range."
    fi
else
    echo "    SKIP: Auth log not found or unreadable."
fi
echo ""

# ------------------------------------------------------------------------------
# 8. Top Resource Consumers
# ------------------------------------------------------------------------------
echo -e "${YELLOW}[+] Top 5 CPU Consumers...${NC}"
ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%cpu | head -6 | awk 'NR==1; NR>1 {print $0}'

echo ""
echo -e "${YELLOW}[+] Top 5 Memory Consumers...${NC}"
ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%mem | head -6 | awk 'NR==1; NR>1 {print $0}'

echo ""
echo -e "${CYAN}======================================================${NC}"
echo -e "${CYAN}   Health Check Complete   ${NC}"
echo -e "${CYAN}======================================================${NC}"
