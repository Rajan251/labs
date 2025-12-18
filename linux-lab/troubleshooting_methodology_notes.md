# Troubleshooting Methodology for Linux Systems

**Level:** Expert / SRE / Systems Administrator
**Focus:** Systematic problem-solving and root cause analysis.

---

## 1. Structured Problem-Solving Framework

### The 7-Step Process
1.  **Problem Definition**: What is wrong? Observed vs Expected behavior.
2.  **Information Gathering**: Collect data WITHOUT changing system state.
3.  **Hypothesis Generation**: Brainstorm possible causes.
4.  **Testing**: Test hypotheses systematically (one at a time).
5.  **Solution Implementation**: Apply fix with rollback plan ready.
6.  **Verification**: Confirm problem is resolved.
7.  **Documentation**: Update runbooks and knowledge base.

---

## 2. Information Gathering Techniques

### 2.1 System State Capture
```bash
# Snapshot current state
ps aux > /tmp/ps.txt
netstat -tulpn > /tmp/netstat.txt
df -h > /tmp/df.txt
free -m > /tmp/free.txt
uptime > /tmp/uptime.txt
```

### 2.2 Configuration Review
*   **Recent Changes**: `rpm -qa --last | head -20` (packages installed recently).
*   **Modified Files**: `find /etc -mtime -1` (files changed in last 24h).

### 2.3 Log Analysis
*   **Time Correlation**: "Error started at 14:00. What happened at 13:55?"
*   **Pattern Recognition**: `grep -i error /var/log/messages | sort | uniq -c | sort -rn`.

---

## 3. Common Problem Patterns

### 3.1 Resource Exhaustion
| Resource | Symptom | Check Command |
| :--- | :--- | :--- |
| **Memory** | OOM kills, swapping | `free -m`, `dmesg \| grep -i oom` |
| **Disk Space** | "No space left" | `df -h` |
| **Inodes** | "No space left" (but df shows space) | `df -i` |
| **File Descriptors** | "Too many open files" | `lsof \| wc -l`, `ulimit -n` |
| **Processes** | Fork failures | `ps aux \| wc -l` |

### 3.2 Configuration Errors
*   **Syntax**: `nginx -t`, `apachectl configtest`.
*   **Permissions**: `ls -l`, `namei -l /path/to/file`.

### 3.3 Network Issues
*   **Connectivity**: `ping`, `telnet <ip> <port>`.
*   **DNS**: `dig example.com`, `nslookup`.
*   **Firewall**: `iptables -L -n`, `firewall-cmd --list-all`.

---

## 4. Diagnostic Tools Categorized

### 4.1 System Overview
*   **top/htop**: Real-time process view.
*   **glances**: All-in-one monitoring.

### 4.2 Process Analysis
*   **strace**: Trace system calls. `strace -p <PID>`.
*   **ltrace**: Trace library calls.
*   **perf**: CPU profiling. `perf top`.

### 4.3 Network Analysis
*   **tcpdump**: Packet capture. `tcpdump -i eth0 port 80`.
*   **ss**: Socket statistics. `ss -tulpn`.

### 4.4 Storage Analysis
*   **iostat**: Disk I/O stats. `iostat -x 1`.
*   **iotop**: Per-process I/O.

### 4.5 Memory Analysis
*   **vmstat**: Virtual memory stats. `vmstat 1`.
*   **slabtop**: Kernel slab allocator.

---

## 5. Escalation Procedures

### 5.1 When to Escalate
*   Problem exceeds your expertise.
*   Impact is critical and time is running out.
*   Multiple teams need coordination.

### 5.2 Information to Provide
*   **Problem Statement**: Clear, concise.
*   **Impact**: How many users affected?
*   **Timeline**: When did it start?
*   **Steps Taken**: What have you tried?
*   **Current State**: Stable or degrading?

---

## 6. Post-Mortem Culture

### 6.1 Blameless Post-Mortem
*   **Goal**: Learn, not punish.
*   **Focus**: What failed (process, system), not who failed.

### 6.2 Root Cause vs Contributing Factors
*   **Root Cause**: The fundamental reason.
*   **Contributing Factors**: Things that made it worse.

### 6.3 Action Items
*   **Preventive**: How to prevent recurrence.
*   **Detective**: How to detect faster next time.
*   **Corrective**: Immediate fixes applied.

---

## 7. Example Scenarios

### Scenario 1: Intermittent Website Slowness
1.  **Define**: Users report slow page loads (5s vs normal 200ms).
2.  **Gather**: Check `top` (CPU normal), `free` (RAM normal), `iostat` (disk wait high).
3.  **Hypothesis**: Disk I/O bottleneck.
4.  **Test**: `iotop` shows MySQL consuming I/O.
5.  **Implement**: Add index to slow query.
6.  **Verify**: Response time back to 200ms.
7.  **Document**: Update runbook with query optimization steps.

### Scenario 2: Database Connection Failures
1.  **Define**: App logs show "Too many connections".
2.  **Gather**: `mysql -e "SHOW PROCESSLIST"` shows 150/150 connections.
3.  **Hypothesis**: Connection leak in app.
4.  **Test**: Check app logs for unclosed connections.
5.  **Implement**: Fix app code to close connections properly.
6.  **Verify**: Connection count stays below 50.
7.  **Document**: Add monitoring alert for connection count >100.

### Scenario 3: Random Server Reboots
1.  **Define**: Server reboots without warning.
2.  **Gather**: Check `/var/log/messages` for kernel panic. Check hardware logs.
3.  **Hypothesis**: Hardware failure (RAM, PSU).
4.  **Test**: Run `memtest86+` overnight.
5.  **Implement**: Replace faulty RAM module.
6.  **Verify**: No reboots for 30 days.
7.  **Document**: Update hardware maintenance log.
