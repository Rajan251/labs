# Advanced Linux Troubleshooting: Mindset & Mental Models

**Level:** Expert / SRE / Systems Architect  
**Focus:** Cognitive approaches, biases, and systematic thinking for complex problems

---

## 1. THE TROUBLESHOOTER'S MINDSET

### 1.1 Assumption Checking

**What We Think We Know vs What We Actually Know**

| Assumption | Reality Check |
|------------|---------------|
| "The network is fine" | Have you actually tested it? `ping`, `traceroute` |
| "Nothing changed" | Check: `rpm -qa --last`, `git log`, change tickets |
| "It worked yesterday" | Verify: Check monitoring graphs, logs from yesterday |
| "Only this server is affected" | Confirm: Test other servers, check monitoring dashboard |

**Exercise**: Before investigating, write down 3 assumptions. Then verify each one.

### 1.2 Scientific Method for Systems

```
1. Observe → Document symptoms precisely
2. Question → Form specific, testable hypothesis
3. Hypothesize → "If X is the cause, then Y should be true"
4. Experiment → Test hypothesis with minimal system impact
5. Analyze → Compare results to prediction
6. Conclude → Accept, reject, or refine hypothesis
```

### 1.3 Cognitive Biases & Countermeasures

#### Confirmation Bias
**Problem**: Looking only for evidence that confirms your theory  
**Example**: You think it's a network issue, so you only check network stats  
**Counter**: Actively seek evidence that **disproves** your theory
```bash
# Instead of just checking network
ping google.com  # Confirms network works

# Also check what would disprove network theory
curl http://localhost:8080  # If this fails, it's NOT network
```

#### Anchoring Effect
**Problem**: Fixating on the first piece of information  
**Example**: First log entry mentions "timeout", so you assume everything is timeout-related  
**Counter**: List 3 possible causes before investigating
```
Symptom: Application slow
Possible causes:
1. Network latency
2. Database query performance
3. Memory pressure
Now investigate all three, not just #1
```

#### Availability Heuristic
**Problem**: Assuming common causes are always the culprit  
**Example**: "It's always DNS" or "It's always the database"  
**Counter**: Ask "When did this last work perfectly?" and check what changed since then
```bash
# Check recent changes
git log --since="2 days ago"
rpm -qa --last | head -20
journalctl --since "2 days ago" | grep -i error
```

---

## 2. SYSTEMATIC METHODOLOGY (6 Phases)

### Phase 1: Problem Definition

**Questions to Ask**:
1. **What exactly is happening?** (Observable symptoms)
   - ❌ "The server is slow"
   - ✅ "API response time is 5s, normally 200ms"

2. **What should be happening?** (Expected behavior)
   - ✅ "Response time should be <500ms per SLA"

3. **When did it start?** (Timeline)
   - ✅ "Started at 14:00 UTC today"

4. **What changed?** (Recent modifications)
   - ✅ "Deployment at 13:45 UTC"

5. **Who/what is affected?** (Scope)
   - ✅ "All users in EU region, US region unaffected"

### Phase 2: Information Gathering (Non-Invasive)

**Golden Rule**: Gather first, change later

```bash
# System state snapshot (read-only)
date > /tmp/investigation_$(date +%s).log
uptime >> /tmp/investigation_*.log
free -h >> /tmp/investigation_*.log
df -h >> /tmp/investigation_*.log
ps aux --sort=-%cpu | head -20 >> /tmp/investigation_*.log
ss -tulpn >> /tmp/investigation_*.log
```

**Baseline Comparison**:
```bash
# Compare current vs normal
vmstat 1 5  # Current
# vs historical data from monitoring (Grafana, Prometheus)
```

### Phase 3: Hypothesis Generation

**Ishikawa (Fishbone) Diagram for Systems**:
```
                    Problem: Slow API
                         |
    ┌────────────────────┼────────────────────┐
    |                    |                    |
Hardware          Software              Network
- CPU saturated   - Memory leak         - High latency
- Disk I/O wait   - Inefficient query   - Packet loss
- RAM exhausted   - Deadlock            - DNS issues
```

**5 Whys Method**:
```
Problem: Website down
Why? → Nginx not responding
Why? → Process crashed
Why? → Out of memory
Why? → Memory leak in application
Why? → Unclosed database connections
Root Cause: Connection pool misconfiguration
```

### Phase 4: Testing & Validation

**Safe Testing Principles**:
```bash
# ❌ WRONG: Make multiple changes at once
systemctl restart nginx
sysctl -w net.core.somaxconn=1024
iptables -F

# ✅ RIGHT: One change at a time
# Test 1: Restart nginx
systemctl restart nginx
# Verify: curl http://localhost
# Document: "Restart did not fix issue"

# Test 2: Increase connection queue
sysctl -w net.core.somaxconn=1024
# Verify: Check if issue resolved
```

### Phase 5: Solution Implementation

**Implementation Checklist**:
- [ ] Impact assessment: Who/what will be affected?
- [ ] Rollback procedure: How to undo this change?
- [ ] Communication: Stakeholders notified?
- [ ] Monitoring: Enhanced during change?
- [ ] Documentation: Change recorded?

### Phase 6: Verification & Documentation

```bash
# Verify problem is resolved (not just symptom masked)
# Before: Response time 5s
# After: Response time 200ms ✓

# Ensure no new problems
# Check error logs, monitoring dashboards

# Update runbook
echo "Issue: Slow API due to connection pool exhaustion" >> runbook.md
echo "Solution: Increased max_connections from 100 to 500" >> runbook.md
```

---

## 3. PROBLEM CATEGORIZATION MATRIX

| Symptom | Likely Layer | First Commands | Common Root Causes |
|---------|-------------|----------------|-------------------|
| **Slow response** | Application | `top`, `vmstat 1`, `iostat -x 1` | Memory pressure, I/O wait, CPU saturation |
| **Connection refused** | Network | `ss -tlnp`, `nc -zv`, `tcpdump` | Service down, firewall, port conflict |
| **Permission denied** | Filesystem | `ls -la`, `getfacl`, `audit2why` | SELinux, ACLs, ownership, mode bits |
| **Out of memory** | Kernel | `free -h`, `dmesg \| tail` | Memory leak, swap off, OOM killer |

---

## 4. DECISION TREES

### Server Unreachable
```
Can you ping it?
├─ NO → Layer 1-3 issue
│   ├─ Check physical connection
│   ├─ Check switch/router
│   └─ Check IP configuration
│
└─ YES → Can you SSH?
    ├─ NO → SSH service/firewall
    │   ├─ systemctl status sshd
    │   └─ iptables -L -n
    │
    └─ YES → Application responding?
        ├─ NO → Check application logs
        └─ YES → Performance issue (not availability)
```

### High Load Average
```
Check CPU usage (top)
├─ High (>80%) → CPU-bound
│   └─ Find process: ps aux --sort=-%cpu
│
└─ Low (<50%) → Check I/O wait
    ├─ High → I/O bottleneck
    │   └─ iostat -x 1
    │
    └─ Low → Check threads
        └─ ps -eLf | wc -l
```

---

## 5. TIME-SAVING TECHNIQUES

### The 5-Minute Rule
If you haven't found the cause in 5 minutes:
1. **Step back**: Re-define the problem
2. **Check assumptions**: Are you solving the right problem?
3. **Fresh perspective**: Ask a colleague
4. **Different approach**: Try a different layer

### Divide and Conquer (Binary Search)
```
Network issue between Client → Router → Switch → Server?

Test at Router: ✓ Works
Test at Switch: ✓ Works
Test at Server: ✗ Fails
→ Problem is between Switch and Server
```

### Rubber Duck Debugging
**Template**: "I expect X because Y, but I see Z instead..."

Example:
```
"I expect the API to return in 200ms because the database query 
takes 50ms and network latency is 10ms, but I see 5s response time 
instead. This suggests something else is adding 4.7s delay..."
```

---

## 6. DOCUMENTATION TEMPLATES

### Problem Statement
```
Problem ID: INC-2025-001
Reported: 2025-12-19 14:00 UTC
Reported by: Monitoring System
Affected: EU API endpoints
Impact: HIGH - 50% of users affected
SLA Clock: Started at 14:00 UTC

Current Status: Investigating
Root Cause: TBD
Next Update: 14:30 UTC
Escalation: Level 2 (Senior SRE)
```

### Investigation Log
```
14:05 - Checked system load
Command: uptime
Output: load average: 15.2, 12.8, 10.5
Observation: Load is 3x normal (normal: 5.0)
Next: Check what's consuming CPU

14:07 - Identified high CPU process
Command: ps aux --sort=-%cpu | head -5
Output: java process at 400% CPU
Observation: Application thread spinning
Next: Get thread dump
```

### Lessons Learned
```
What happened: API slowdown from 200ms to 5s
Timeline:
- 13:45: Deployment of v2.1.0
- 14:00: Monitoring alerts triggered
- 14:15: Root cause identified
- 14:20: Rollback initiated
- 14:25: Service restored

Root cause: Database connection pool exhausted
Contributing factors: Traffic spike + smaller pool size in new version
Detection gap: No alerting on connection pool usage
Resolution: Rollback to v2.0.9
Prevention: Add connection pool monitoring, increase pool size
Improvements: Pre-deployment load testing, gradual rollout
```

---

## 7. MENTAL MODELS

### Systems Thinking
**Interconnections**: Changing one thing affects others
```
Example: Increase web server threads
→ More database connections
→ Database connection pool exhausted
→ Application hangs
```

### Queueing Theory
**Little's Law**: L = λW
- L = Average number in system
- λ = Arrival rate
- W = Average time in system

**Application**: If requests are queuing, either reduce arrival rate or reduce processing time

### Reliability Engineering
**Failure Modes**:
- **Fail-fast**: Detect and report errors immediately
- **Fail-safe**: Default to safe state
- **Fail-silent**: Hide errors (dangerous!)

---

## 8. QUICK REFERENCE

### First 60 Seconds of Investigation
```bash
uptime                    # Load average
dmesg | tail             # Kernel messages
vmstat 1 5               # System stats
mpstat -P ALL 1          # CPU per core
pidstat 1                # Process stats
iostat -xz 1             # Disk I/O
free -m                  # Memory
sar -n DEV 1             # Network
sar -n TCP,ETCP 1        # TCP stats
top                      # Overview
```

### Common Gotchas
- **"It's always DNS"**: Actually check DNS: `dig example.com`
- **"Restart fixes everything"**: But doesn't tell you root cause
- **"Works on my machine"**: Environment differences matter
- **"It's a network issue"**: Test locally first: `curl localhost:8080`
