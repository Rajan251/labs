# Real-World Scenarios & Solutions

## Table of Contents
1. [Scenario 1: The Midnight Page](#scenario-1-the-midnight-page)
2. [Scenario 2: The Slow Deployment](#scenario-2-the-slow-deployment)
3. [Scenario 3: The Database Meltdown](#scenario-3-the-database-meltdown)
4. [Scenario 4: The Silent Failure](#scenario-4-the-silent-failure)
5. [Scenario 5: The Alert Storm](#scenario-5-the-alert-storm)
6. [Scenario 6: The Cascading Failure](#scenario-6-the-cascading-failure)

---

## Scenario 1: The Midnight Page

### The Story

**Time:** 2:00 AM  
**You:** Sleeping peacefully 😴  
**Phone:** RING RING RING! 📞

**PagerDuty Alert:**
```
🚨 CRITICAL: HighErrorRate - Payment API
Error rate: 15% (threshold: 5%)
Started: 1:58 AM
Dashboard: https://grafana.example.com/payment-api
Runbook: https://runbooks.example.com/high-error-rate
```

### What Actually Happened

**1:55 AM:** Marketing team deployed a new feature  
**1:58 AM:** Error rate spiked to 15%  
**2:00 AM:** You got paged

---

### Step-by-Step Resolution (Like a Baby Would Understand)

#### Step 1: Wake Up and Acknowledge
```
You: *groggily grabs phone*
You: *clicks "Acknowledge" in PagerDuty*
System: "Acknowledged at 2:01 AM"
```

**Why this matters:**
- Team knows you're on it
- Stops escalating to your manager
- Starts the MTTA clock (Mean Time to Acknowledge)

---

#### Step 2: Open the Dashboard (Still in Bed)

**On your phone:**
1. Click the Grafana link
2. See the error rate graph:

```
Error Rate:
2:00 AM: ████████████████ 15% 🔴
1:55 AM: ██ 1% 🟢
1:50 AM: ██ 1% 🟢
```

**What you notice:**
- Error rate was fine before 1:55 AM
- Sudden spike at 1:55 AM
- Something changed!

---

#### Step 3: Check Recent Deployments

**In Slack #deployments channel:**
```
1:55 AM - deploy-bot:
✅ Deployed payment-api v2.3.0 to production
Changes: Added new payment method validation
Deployed by: @marketing-team
```

**Aha! 💡**
- Deployment at 1:55 AM
- Errors started at 1:58 AM
- Deployment is the likely culprit!

---

#### Step 4: Check the Logs (Now You're Sitting Up)

**On laptop:**
```bash
kubectl logs deployment/payment-api -n production --tail=100 | grep ERROR
```

**What you see:**
```
ERROR: NullPointerException in PaymentValidator.validateNewMethod()
ERROR: NullPointerException in PaymentValidator.validateNewMethod()
ERROR: NullPointerException in PaymentValidator.validateNewMethod()
... (repeating)
```

**Translation:**
- New code has a bug
- It crashes when validating new payment methods
- 15% of users are trying the new payment method
- Those 15% are getting errors!

---

#### Step 5: Make a Decision

**Your options:**

**Option A: Fix the bug (risky at 2 AM)**
- Pro: Keeps new feature
- Con: Takes time, might make it worse
- Time: 30+ minutes

**Option B: Rollback deployment (safe)**
- Pro: Immediate fix, proven to work
- Con: Loses new feature
- Time: 2 minutes

**You choose:** Option B (rollback)

**Why:**
- 2 AM is not the time to debug
- Users are suffering NOW
- Can fix properly tomorrow

---

#### Step 6: Execute Rollback

```bash
# Check deployment history
kubectl rollout history deployment/payment-api -n production

# Output:
REVISION  CHANGE-CAUSE
1         v2.2.0 (stable)
2         v2.3.0 (current, broken)

# Rollback to previous version
kubectl rollout undo deployment/payment-api -n production

# Output:
deployment.apps/payment-api rolled back
```

**Wait 1 minute...**

---

#### Step 7: Verify Fix

**Check dashboard:**
```
Error Rate:
2:05 AM: ██ 0.5% 🟢 (back to normal!)
2:03 AM: ████ 5% 🟡 (decreasing)
2:00 AM: ████████████████ 15% 🔴
```

**Check logs:**
```bash
kubectl logs deployment/payment-api -n production --tail=50
```

**What you see:**
```
INFO: Successfully processed payment
INFO: Successfully processed payment
INFO: Successfully processed payment
```

No more errors! ✅

---

#### Step 8: Update Incident

**In PagerDuty:**
```
Status: Resolved
Resolution: Rolled back to v2.2.0
Root Cause: Bug in v2.3.0 payment validation
Duration: 7 minutes (1:58 AM - 2:05 AM)
```

**In Slack #incidents:**
```
🟢 RESOLVED: Payment API error rate spike

What happened: v2.3.0 deployment had a bug
What I did: Rolled back to v2.2.0
Impact: ~15% of users saw errors for 7 minutes
Next steps: 
  - Marketing team: fix bug in v2.3.0
  - Add tests for new payment validation
  - Redeploy during business hours
```

---

#### Step 9: Go Back to Sleep 😴

**Time:** 2:10 AM  
**You:** Back in bed  
**Metrics:**
- MTTD: 3 minutes (1:58 to 2:01)
- MTTA: 1 minute (2:00 to 2:01)
- MTTR: 7 minutes (1:58 to 2:05)

**All under SLA! ✅**

---

### What We Learned

**What Went Well:**
- ✅ Alert fired quickly (2 minutes)
- ✅ Dashboard showed clear spike
- ✅ Deployment history was tracked
- ✅ Rollback was fast and easy
- ✅ Problem resolved in 7 minutes

**What Could Be Better:**
- ❌ Deployment at 1:55 AM (should be during business hours)
- ❌ No automated tests caught the bug
- ❌ No gradual rollout (canary deployment)

**Action Items:**
1. Add rule: No deployments after 6 PM
2. Add integration tests for payment validation
3. Implement canary deployments (5% → 25% → 100%)

---

## Scenario 2: The Slow Deployment

### The Story

**Time:** 2:00 PM (business hours)  
**You:** At your desk  
**Slack:** New message in #deployments

```
deploy-bot: Starting deployment of user-service v3.0.0
Strategy: Canary (5% → 25% → 50% → 100%)
Estimated time: 30 minutes
```

**You:** *sips coffee* ☕ "This should be fine..."

---

### The Timeline

#### 2:00 PM - Deploy to 5% of Users

```
Canary: 5% of traffic
Old version: 95% of traffic

Metrics after 5 minutes:
  Error rate: 0.1% ✅ (same as before)
  Latency P95: 210ms ✅ (was 200ms, within 10% threshold)
  User complaints: 0 ✅
  
Decision: Proceed to 25%
```

---

#### 2:10 PM - Deploy to 25% of Users

```
Canary: 25% of traffic
Old version: 75% of traffic

Metrics after 5 minutes:
  Error rate: 0.1% ✅
  Latency P95: 450ms ⚠️ (was 200ms, 125% increase!)
  User complaints: 3 ⚠️ ("App is slow")
  
Decision: PAUSE! Something's wrong.
```

---

### Investigation

**You check the dashboard:**

```
Latency by Version:
Old (v2.9.0): ████ 200ms 🟢
New (v3.0.0): ████████████ 450ms 🔴
```

**You check the logs:**

```bash
kubectl logs deployment/user-service -l version=v3.0.0 --tail=100
```

**What you see:**
```
WARN: Database query took 400ms (expected: 50ms)
WARN: Database query took 380ms (expected: 50ms)
WARN: Database query took 420ms (expected: 50ms)
```

**Aha! Database queries are slow in the new version.**

---

### Root Cause Analysis

**You check the code changes:**

```diff
# Old version (v2.9.0)
def get_user(user_id):
    return db.query("SELECT * FROM users WHERE id = ?", user_id)

# New version (v3.0.0)
def get_user(user_id):
    user = db.query("SELECT * FROM users WHERE id = ?", user_id)
    # NEW: Also fetch user's posts
    posts = db.query("SELECT * FROM posts WHERE user_id = ?", user_id)
    return {**user, "posts": posts}
```

**The problem:**
- New version makes 2 database queries instead of 1
- Second query is slow (no index on `user_id` in posts table!)
- This adds 400ms to every request

---

### The Decision

**Options:**

**Option A: Rollback**
- Pro: Immediate fix
- Con: Lose new feature
- Time: 2 minutes

**Option B: Add database index**
- Pro: Keeps new feature
- Con: Risky to change database during incident
- Time: 10 minutes

**Option C: Make second query optional**
- Pro: Keeps feature for those who need it
- Con: Requires code change
- Time: 20 minutes

**You choose:** Option A (rollback)

**Why:**
- Users are experiencing slow app NOW
- Can optimize database and redeploy later
- Safety first!

---

### Resolution

```bash
# Rollback canary to 0%
kubectl patch deployment user-service -p '{"spec":{"replicas":0}}' -l version=v3.0.0

# Scale up old version to 100%
kubectl scale deployment user-service --replicas=10 -l version=v2.9.0
```

**Metrics after 2 minutes:**
```
Latency P95: 200ms 🟢 (back to normal!)
User complaints: 0 ✅
```

---

### Post-Incident Actions

**Immediate:**
```
1. Notify team in Slack
2. Create Jira ticket: "Add index to posts.user_id"
3. Update deployment with fix
```

**Next Day:**
```
1. Add index to database:
   CREATE INDEX idx_posts_user_id ON posts(user_id);

2. Test locally:
   Query time: 50ms ✅ (was 400ms)

3. Redeploy v3.0.1 with canary:
   5%: Latency 205ms ✅
   25%: Latency 210ms ✅
   100%: Success! ✅
```

---

### What We Learned

**What Went Well:**
- ✅ Canary deployment caught the problem early
- ✅ Only 25% of users affected
- ✅ Quick rollback prevented wider impact
- ✅ Root cause identified quickly

**What Could Be Better:**
- ❌ Database query performance not tested before deployment
- ❌ No index on frequently-queried column

**Action Items:**
1. Add performance tests to CI/CD
2. Review all database queries for missing indexes
3. Add query time monitoring per endpoint

---

## Scenario 3: The Database Meltdown

### The Story

**Time:** 10:00 AM  
**Alert:** 🚨 Multiple alerts firing simultaneously

```
PostgreSQLTooManyConnections
HighLatency
HighErrorRate
ServiceDown (for 3 services!)
```

**You:** "Oh no... this is bad." 😰

---

### The Cascade

**What happened (in order):**

```
9:58 AM: Database connection pool reaches 95%
9:59 AM: New requests start timing out
10:00 AM: Services retry failed requests
10:01 AM: Retry storm overwhelms database
10:02 AM: Database stops accepting connections
10:03 AM: All services depending on database fail
```

**This is a cascading failure!** 💥

---

### Step 1: Triage (What's the Root Cause?)

**Check the timeline:**

```
First alert: PostgreSQLTooManyConnections (9:58 AM)
Then: HighLatency (9:59 AM)
Then: HighErrorRate (10:00 AM)
Then: ServiceDown (10:03 AM)
```

**Root cause:** Database connection pool exhaustion  
**Symptoms:** Everything else failing

---

### Step 2: Stop the Bleeding

**Priority 1: Stop retry storms**

```bash
# Temporarily disable retries in all services
kubectl set env deployment/user-service ENABLE_RETRIES=false
kubectl set env deployment/payment-service ENABLE_RETRIES=false
kubectl set env deployment/order-service ENABLE_RETRIES=false
```

**Why:** Retries are making it worse!

---

### Step 3: Free Up Database Connections

```bash
# Connect to database
kubectl exec -it postgres-0 -n database -- psql -U admin

# Check active connections
SELECT count(*), state FROM pg_stat_activity GROUP BY state;

# Output:
 count | state
-------+--------
   95  | active
    5  | idle

# Kill idle connections
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'idle' 
AND query_start < now() - interval '5 minutes';

# Output: 5 connections terminated
```

**Now:** 90/100 connections used (was 100/100)

---

### Step 4: Increase Connection Pool (Temporary Fix)

```bash
# Edit database config
kubectl edit configmap postgres-config -n database

# Change:
max_connections: 100  # Old
max_connections: 200  # New (temporary)

# Restart database (scary but necessary)
kubectl rollout restart statefulset/postgres -n database
```

**Wait 2 minutes for database to restart...**

---

### Step 5: Verify Recovery

**Check metrics:**
```
Database connections: 45/200 🟢 (was 100/100)
Service latency: 200ms 🟢 (was 5000ms)
Error rate: 0.5% 🟢 (was 80%)
```

**Check services:**
```bash
kubectl get pods -A | grep -v Running

# Output: (empty - all pods running!)
```

**All services recovered!** ✅

---

### Step 6: Re-enable Retries

```bash
# Turn retries back on
kubectl set env deployment/user-service ENABLE_RETRIES=true
kubectl set env deployment/payment-service ENABLE_RETRIES=true
kubectl set env deployment/order-service ENABLE_RETRIES=true
```

---

### Root Cause Analysis (The Next Day)

**What caused the connection pool to fill up?**

**Investigation:**
```sql
-- Check slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Found:
query: SELECT * FROM orders WHERE user_id = ? AND status = ?
mean_exec_time: 2500ms  (2.5 seconds!)
calls: 50,000 per hour
```

**The problem:**
- Slow query taking 2.5 seconds
- Each query holds a connection for 2.5 seconds
- 50,000 queries/hour = 35 queries/second
- 35 queries × 2.5 seconds = 87 connections needed
- Pool only had 100 connections!

**Why was the query slow?**
```sql
-- Missing index!
EXPLAIN SELECT * FROM orders WHERE user_id = 123 AND status = 'pending';

-- Output:
Seq Scan on orders  (cost=0.00..10000.00 rows=100)
-- Translation: Scanning entire table (slow!)
```

---

### The Fix

```sql
-- Add composite index
CREATE INDEX idx_orders_user_status 
ON orders(user_id, status);

-- Test query again
EXPLAIN SELECT * FROM orders WHERE user_id = 123 AND status = 'pending';

-- Output:
Index Scan using idx_orders_user_status  (cost=0.00..8.50 rows=100)
-- Translation: Using index (fast!)

-- Query time: 2500ms → 15ms ✅
```

---

### What We Learned

**What Went Well:**
- ✅ Identified root cause quickly (database connections)
- ✅ Stopped retry storms
- ✅ Increased connection pool temporarily
- ✅ All services recovered

**What Could Be Better:**
- ❌ No alert for slow queries
- ❌ No connection pool usage monitoring
- ❌ Missing database index

**Action Items:**
1. Add alert: "Database connection pool > 80%"
2. Add alert: "Slow query detected (> 1 second)"
3. Review all tables for missing indexes
4. Add circuit breakers to prevent retry storms
5. Implement connection pool per service (not shared)

---

## Key Lessons from All Scenarios

### 1. **Alerts Should Tell a Story**

**Bad:**
```
Alert: Something is wrong
```

**Good:**
```
Alert: HighErrorRate
Context: 15% error rate (threshold: 5%)
Timeline: Started 3 minutes ago
Impact: 15% of users affected
Runbook: https://runbooks.example.com/high-error-rate
Dashboard: https://grafana.example.com/payment-api
```

---

### 2. **Always Have a Rollback Plan**

**Every deployment should answer:**
- How do I rollback?
- How long does rollback take?
- What data might be lost?

**Example:**
```
Deployment: user-service v3.0.0
Rollback command: kubectl rollout undo deployment/user-service
Rollback time: 2 minutes
Data impact: None (backward compatible)
```

---

### 3. **Cascading Failures Need Circuit Breakers**

**Without circuit breaker:**
```
Database slow → Services retry → More load on database → Database crashes → All services crash
```

**With circuit breaker:**
```
Database slow → Circuit opens → Services fail fast → Database recovers → Circuit closes → Services recover
```

---

### 4. **Monitor the Monitors**

**Meta-alerts:**
```
- Alert: Prometheus is down
- Alert: Alertmanager is down
- Alert: Too many alerts firing (alert storm)
```

**Why:** If monitoring is broken, you won't know about real problems!

---

### 5. **Practice Makes Perfect**

**Monthly fire drills:**
```
1. Intentionally break something (in staging)
2. See if alerts fire
3. Follow runbook
4. Measure MTTD/MTTA/MTTR
5. Update runbook with learnings
```

---

## Summary: The Incident Response Checklist

**When you get paged:**

```
☐ 1. Acknowledge alert (stop escalation)
☐ 2. Check dashboard (understand scope)
☐ 3. Check recent changes (deployments, config)
☐ 4. Check logs (find errors)
☐ 5. Make decision (fix vs rollback)
☐ 6. Execute action (carefully!)
☐ 7. Verify fix (metrics back to normal?)
☐ 8. Update incident (status, resolution)
☐ 9. Notify team (Slack, email)
☐ 10. Schedule postmortem (learn from it)
```

**Remember:**
- 🎯 **Speed matters** - Every minute counts
- 🛡️ **Safety first** - Don't make it worse
- 📝 **Document everything** - Future you will thank you
- 🤝 **Ask for help** - Escalate if stuck
- 🧠 **Learn from it** - Every incident is a lesson

**You've got this!** 💪
