# Advanced Concepts Made Simple

## Table of Contents
1. [SLOs and Error Budgets Deep Dive](#slos-and-error-budgets-deep-dive)
2. [Multi-Burn-Rate Alerts](#multi-burn-rate-alerts)
3. [Distributed Tracing](#distributed-tracing)
4. [Chaos Engineering](#chaos-engineering)
5. [Canary Deployments](#canary-deployments)
6. [Circuit Breakers](#circuit-breakers)
7. [Rate Limiting](#rate-limiting)
8. [Blue-Green Deployments](#blue-green-deployments)
9. [Feature Flags](#feature-flags)
10. [Incident Command System](#incident-command-system)

---

## SLOs and Error Budgets Deep Dive

### The Restaurant Analogy

Imagine you own a restaurant:

**Your Promise (SLO):**
"We will serve your food within 30 minutes, 99% of the time"

**What This Means:**
- Out of 100 customers, you can be late for 1 customer
- That 1 late customer is your "error budget"

**Monthly Math:**
```
Total customers per month: 3,000
SLO: 99% on-time delivery
Error budget: 1% = 30 customers can get late food

Week 1: 10 customers got late food (used 33% of budget)
Week 2: 15 customers got late food (used 50% of budget)
Week 3: 3 customers got late food (used 10% of budget)
Week 4: 2 customers got late food (used 7% of budget)

Total: 30 customers = 100% of error budget used ⚠️
```

**What Happens When Budget is Gone:**
```
Option 1: Stop taking risks
  - No new menu items this month
  - No kitchen experiments
  - Focus on consistency

Option 2: Break your promise
  - Keep trying new things
  - More customers get late food
  - Customers lose trust
```

---

### In Software: Real Example

**Your SLO:**
```
Service: Payment API
SLO: 99.9% of requests must succeed
Time Window: 30 days
Error Budget: 0.1% = 43 minutes of downtime per month
```

**Tracking Your Budget:**

```
Day 1: Deploy new feature
  - Caused 5 minutes of errors
  - Budget used: 5/43 = 11.6%
  - Remaining: 38 minutes

Day 7: Database hiccup
  - Caused 10 minutes of errors
  - Budget used: 10/43 = 23.3%
  - Remaining: 28 minutes

Day 15: Bad deployment
  - Caused 20 minutes of errors
  - Budget used: 20/43 = 46.5%
  - Remaining: 8 minutes ⚠️

Day 16: FREEZE! 🛑
  - Only 8 minutes left
  - No more risky deployments
  - Focus on stability
```

---

### SLO Types Explained

#### 1. Availability SLO

**Simple:** "How often is my service working?"

**Example:**
```
SLO: Service must be up 99.95% of the time
Math: 
  - 30 days = 43,200 minutes
  - 99.95% uptime = 21.6 minutes downtime allowed
  
Reality Check:
  - 1 minute outage = 4.6% of monthly budget
  - 5 minute outage = 23% of monthly budget
  - 20 minute outage = 92% of monthly budget
```

**How to Measure:**
```promql
# Prometheus query
avg_over_time(up{service="payment-api"}[30d]) >= 0.9995
```

---

#### 2. Latency SLO

**Simple:** "How fast does my service respond?"

**Example:**
```
SLO: 95% of requests must complete in under 500ms

What this means:
  - Out of 100 requests, 95 must be fast
  - 5 can be slow (your error budget)
  
Reality:
  Request 1: 100ms ✅
  Request 2: 200ms ✅
  Request 3: 450ms ✅
  Request 4: 800ms ❌ (counts against budget)
  Request 5: 150ms ✅
  ...
  Request 100: 300ms ✅
  
  Result: 6 slow requests = 94% fast = FAILED SLO ❌
```

**How to Measure:**
```promql
# Prometheus query
histogram_quantile(0.95, 
  rate(http_request_duration_seconds_bucket[30d])
) < 0.5
```

---

#### 3. Error Rate SLO

**Simple:** "How many requests succeed?"

**Example:**
```
SLO: 99.9% of requests must succeed (not return errors)

Math:
  - 1,000,000 requests per month
  - 99.9% success = 1,000 requests can fail
  
Tracking:
  Week 1: 200 failures (20% of budget)
  Week 2: 500 failures (50% of budget)
  Week 3: 100 failures (10% of budget)
  Week 4: 150 failures (15% of budget)
  
  Total: 950 failures = 95% of budget used ⚠️
```

---

## Multi-Burn-Rate Alerts

### The Problem with Simple Alerts

**Bad Alert:**
```
Alert: IF error_rate > 1% THEN page on-call

Problem:
  - 1.1% error rate for 1 minute → PAGES ❌ (false alarm)
  - 0.9% error rate for 24 hours → NO ALERT ❌ (missed real problem)
```

---

### The Solution: Multi-Window Multi-Burn-Rate

**Think of it like a car's warning lights:**

1. **Check Engine Light** (Slow burn)
   - "Something's wrong, but you can drive to the mechanic tomorrow"
   - Like: 2x error budget burn over 6 hours

2. **Oil Pressure Light** (Fast burn)
   - "STOP THE CAR NOW!"
   - Like: 14x error budget burn over 1 hour

---

### Real Example

**Your SLO:**
```
Error Budget: 0.1% errors allowed per month
Normal Burn: 0.1% over 30 days
```

**Multi-Burn-Rate Alerts:**

#### Alert 1: Fast Burn (Critical)
```
Window: 1 hour
Burn Rate: 14.4x normal
Math: At this rate, you'll burn entire month's budget in 2 days!

Example:
  Normal: 0.1% errors over 30 days
  Current: 1.44% errors over 1 hour
  
  Action: PAGE ON-CALL IMMEDIATELY 🚨
  Why: You're burning budget 14x faster than allowed
```

#### Alert 2: Slow Burn (Warning)
```
Window: 6 hours
Burn Rate: 6x normal
Math: At this rate, you'll burn entire month's budget in 5 days

Example:
  Normal: 0.1% errors over 30 days
  Current: 0.6% errors over 6 hours
  
  Action: Slack warning, investigate during business hours
  Why: Concerning trend, but not immediate crisis
```

---

### Why This Works

**Scenario 1: Brief Spike**
```
Time: 10:00 - Error rate spikes to 5% for 2 minutes
Fast Burn Alert: Evaluating... (needs 1 hour of data)
Slow Burn Alert: Evaluating... (needs 6 hours of data)
Time: 10:02 - Error rate back to normal
Result: NO ALERTS (spike too brief) ✅ Avoided false alarm
```

**Scenario 2: Sustained Problem**
```
Time: 10:00 - Error rate increases to 2%
Time: 10:30 - Still 2%
Time: 11:00 - Still 2%
Fast Burn Alert: FIRES! 🚨 (1 hour of 2% errors)
Action: Page on-call
Result: Caught real problem ✅
```

**Scenario 3: Slow Degradation**
```
Time: 08:00 - Error rate 0.5%
Time: 10:00 - Error rate 0.6%
Time: 12:00 - Error rate 0.7%
Time: 14:00 - Error rate 0.8%
Slow Burn Alert: FIRES! ⚠️ (6 hours of elevated errors)
Action: Slack warning, investigate
Result: Caught gradual problem ✅
```

---

## Distributed Tracing

### The Pizza Delivery Analogy

**Without Tracing:**
```
Customer: "My pizza took 45 minutes!"
You: "Uh... let me check..."
*checks 5 different systems*
*still don't know where the delay was*
```

**With Tracing:**
```
Customer: "My pizza took 45 minutes!"
You: *looks at trace*

Order received: 10:00:00 (0 seconds)
  ↓
Kitchen started: 10:00:05 (5 seconds) ✅
  ↓
Pizza cooking: 10:00:10 to 10:15:10 (15 minutes) ✅
  ↓
Waiting for driver: 10:15:10 to 10:35:10 (20 minutes) ❌ PROBLEM!
  ↓
Delivery: 10:35:10 to 10:45:00 (10 minutes) ✅

You: "The delay was waiting for a driver. We need more drivers!"
```

---

### In Software: Microservices

**The Request Journey:**

```
User clicks "Buy Now"
  ↓
1. Web Frontend (10ms)
   ↓
2. Authentication Service (50ms)
   ↓
3. Payment Service (2000ms) ⚠️ SLOW!
   ↓ (Payment calls these in parallel)
   ├─> Credit Card API (1800ms) ⚠️ VERY SLOW!
   └─> Fraud Check API (200ms) ✅
   ↓
4. Inventory Service (30ms)
   ↓
5. Email Service (100ms)
   ↓
Total: 2,190ms

Trace shows: Credit Card API is the bottleneck!
```

---

### How Tracing Works

**Step 1: Generate Trace ID**
```
User makes request
System generates unique ID: trace-12345
This ID follows the request everywhere
```

**Step 2: Each Service Adds a Span**
```
Span = One step in the journey

Web Frontend creates span:
  Trace ID: trace-12345
  Span ID: span-001
  Service: web-frontend
  Duration: 10ms
  
Payment Service creates span:
  Trace ID: trace-12345  (same trace!)
  Span ID: span-003
  Parent Span: span-001  (came from web frontend)
  Service: payment-service
  Duration: 2000ms
```

**Step 3: Visualize the Trace**
```
trace-12345:
├─ web-frontend (10ms)
│  └─ auth-service (50ms)
│     └─ payment-service (2000ms)
│        ├─ credit-card-api (1800ms) ⚠️
│        └─ fraud-check-api (200ms)
│     └─ inventory-service (30ms)
│     └─ email-service (100ms)

Total: 2190ms
Bottleneck: credit-card-api (82% of total time)
```

---

### When to Use Tracing

**Use Tracing When:**
- ✅ You have multiple services calling each other
- ✅ You need to find which service is slow
- ✅ You're debugging a complex request flow
- ✅ You want to understand dependencies

**Don't Need Tracing When:**
- ❌ You have a single monolithic application
- ❌ You just want to know "is it slow" (use metrics)
- ❌ You want to see all errors (use logs)

---

## Chaos Engineering

### What is Chaos Engineering?

**Simple Explanation:**
Intentionally breaking things to make sure you can handle it when they break for real.

**Fire Drill Analogy:**
```
Bad Approach:
  - Wait for real fire
  - Panic
  - Don't know what to do
  - People get hurt

Good Approach:
  - Practice fire drill monthly
  - Everyone knows what to do
  - When real fire happens, everyone is calm
  - Everyone gets out safely
```

---

### Chaos Engineering in Software

**The Idea:**
```
Instead of waiting for production to break,
We intentionally break things in a controlled way,
To make sure we can handle it.
```

**Example Experiments:**

#### Experiment 1: Kill Random Pods

**Hypothesis:**
"If we kill one pod, Kubernetes will restart it and users won't notice"

**Test:**
```
1. Start monitoring error rate
2. Kill one random pod
3. Observe:
   - Did Kubernetes restart it? ✅
   - Did users see errors? ❌ (good!)
   - How long did it take to recover? 30 seconds ✅
   
Result: System is resilient! ✅
```

**What if it failed:**
```
3. Observe:
   - Did Kubernetes restart it? ✅
   - Did users see errors? ✅ (bad!)
   - Error rate spiked to 10% ❌
   
Result: We need more pods! (found a problem before real outage)
Action: Increase minimum pods from 3 to 5
```

---

#### Experiment 2: Slow Down Database

**Hypothesis:**
"If database is slow, our app will timeout gracefully and show user a nice error"

**Test:**
```
1. Add 2 second delay to all database queries
2. Observe:
   - Do requests timeout? ✅
   - Do users see nice error message? ❌ (shows ugly stack trace!)
   - Does app crash? ❌ (good!)
   
Result: Timeout works, but error message is bad
Action: Improve error handling to show user-friendly message
```

---

#### Experiment 3: Network Partition

**Hypothesis:**
"If our app can't reach the database, it will use cached data"

**Test:**
```
1. Block network traffic between app and database
2. Observe:
   - Does app use cache? ❌ (crashes instead!)
   - Do users see errors? ✅ (bad!)
   
Result: Cache fallback doesn't work!
Action: Fix cache fallback logic
```

---

### Chaos Engineering Best Practices

**1. Start Small**
```
❌ Don't: Kill entire production database
✅ Do: Kill one pod in staging environment
```

**2. Have a Kill Switch**
```
Always be able to stop the experiment immediately
Like a fire extinguisher for your chaos!
```

**3. Run During Business Hours**
```
❌ Don't: Run chaos at 3 AM when no one is watching
✅ Do: Run chaos at 2 PM when team is available
```

**4. Measure Everything**
```
Before experiment: Error rate = 0.1%
During experiment: Error rate = 0.1% ✅ (no impact)
After experiment: Error rate = 0.1% ✅ (recovered)
```

**5. Automate It**
```
Manual chaos: Run once, forget about it
Automated chaos: Runs weekly, catches regressions
```

---

### Chaos Tools

**1. Chaos Monkey (Netflix)**
```
What: Randomly kills instances in production
When: During business hours
Why: Ensures system can handle instance failures
```

**2. Chaos Mesh (Kubernetes)**
```
What: Injects various failures into Kubernetes
Examples:
  - Pod failures
  - Network delays
  - Disk failures
  - CPU stress
```

**3. Gremlin**
```
What: Commercial chaos engineering platform
Features:
  - Scheduled experiments
  - Safety controls
  - Detailed reporting
```

---

## Canary Deployments

### The Coal Mine Analogy

**Old Days:**
Miners brought canaries into coal mines. If there was poison gas, the canary would die first, warning the miners to evacuate.

**In Software:**
Deploy new code to a small group of users first. If they have problems, you know the code is bad before it affects everyone!

---

### How Canary Deployments Work

**Traditional Deployment (Risky):**
```
Old Version: 100% of users
  ↓
Deploy new version to ALL servers
  ↓
New Version: 100% of users

Problem: If new version is broken, ALL users are affected! ❌
```

**Canary Deployment (Safe):**
```
Step 1: Old Version: 100% of users
  ↓
Step 2: Old Version: 95% of users
        Canary (New): 5% of users
  ↓
  Monitor for 30 minutes:
  - Error rate OK? ✅
  - Latency OK? ✅
  - User complaints? ❌
  ↓
Step 3: Old Version: 50% of users
        Canary (New): 50% of users
  ↓
  Monitor for 30 minutes:
  - Still OK? ✅
  ↓
Step 4: Old Version: 0% of users
        New Version: 100% of users ✅

If ANY step shows problems → ROLLBACK immediately!
```

---

### Real Example

**Deploying Payment Service v2.0:**

```
10:00 AM - Deploy to 5% of users (canary)
  Users affected: 500 out of 10,000
  Monitoring:
    - Error rate: 0.1% ✅ (same as before)
    - Latency P95: 200ms ✅ (same as before)
    - Payment success rate: 99.9% ✅
  
10:30 AM - Looks good! Deploy to 25%
  Users affected: 2,500 out of 10,000
  Monitoring:
    - Error rate: 0.1% ✅
    - Latency P95: 205ms ✅ (slightly higher, but OK)
    - Payment success rate: 99.9% ✅
  
11:00 AM - Deploy to 50%
  Users affected: 5,000 out of 10,000
  Monitoring:
    - Error rate: 2.5% ❌ (PROBLEM!)
    - Latency P95: 800ms ❌ (VERY SLOW!)
    - Payment success rate: 97.5% ❌
  
11:05 AM - ROLLBACK! 🚨
  Action: Revert to old version for all users
  Impact: Only 5,000 users saw the problem for 5 minutes
  Avoided: 10,000 users seeing the problem for hours!
```

---

### Canary Metrics to Watch

**1. Error Rate**
```
Old Version: 0.1% errors
Canary: 0.1% errors ✅ GOOD
Canary: 2.0% errors ❌ ROLLBACK!
```

**2. Latency**
```
Old Version: P95 = 200ms
Canary: P95 = 210ms ✅ GOOD (within 10% is OK)
Canary: P95 = 500ms ❌ ROLLBACK!
```

**3. Business Metrics**
```
Old Version: 99.9% payment success
Canary: 99.9% payment success ✅ GOOD
Canary: 95% payment success ❌ ROLLBACK!
```

**4. User Complaints**
```
Old Version: 2 support tickets/hour
Canary: 2 support tickets/hour ✅ GOOD
Canary: 20 support tickets/hour ❌ ROLLBACK!
```

---

### Automated Canary Analysis

**Instead of watching manually:**

```yaml
canary_rules:
  - metric: error_rate
    threshold: 1%  # Max 1% errors
    comparison: old_version
    
  - metric: latency_p95
    threshold: 10%  # Max 10% slower than old version
    comparison: old_version
    
  - metric: payment_success_rate
    threshold: 99%  # Min 99% success
    comparison: absolute

auto_rollback:
  enabled: true
  if: any_rule_fails
  notification: slack + pagerduty
```

**What Happens:**
```
System automatically:
1. Deploys canary to 5%
2. Waits 10 minutes
3. Checks all metrics
4. If OK → deploy to 25%
5. If NOT OK → automatic rollback + alert team
```

---

## Circuit Breakers

### The Electrical Circuit Breaker Analogy

**Your House:**
```
Too much electricity flowing → Circuit breaker trips
Why? Prevents fire!
You flip the breaker back after fixing the problem
```

**In Software:**
```
Too many failed requests to a service → Circuit breaker "trips"
Why? Prevents cascading failures!
System automatically retries after a timeout
```

---

### The Problem: Cascading Failures

**Without Circuit Breaker:**

```
Your Service → Payment API (down) → 💥

What happens:
1. User tries to pay
2. Your service calls Payment API
3. Payment API is down, request times out after 30 seconds
4. User waits 30 seconds, sees error
5. User retries
6. Another 30 second timeout
7. Meanwhile, 1000 other users are doing the same
8. Your service has 1000 threads waiting 30 seconds each
9. Your service runs out of resources
10. Your service crashes! 💥💥

Result: Payment API being down caused YOUR service to crash too!
```

---

### With Circuit Breaker

**How It Works:**

```
Circuit Breaker States:

1. CLOSED (Normal)
   ├─ Requests flow normally
   ├─ Tracking failures
   └─ If failures > threshold → OPEN

2. OPEN (Tripped)
   ├─ Requests fail immediately (no waiting!)
   ├─ Return cached data or error message
   ├─ After timeout (e.g., 30 seconds) → HALF-OPEN
   └─ Prevents cascading failures

3. HALF-OPEN (Testing)
   ├─ Allow one test request through
   ├─ If success → CLOSED (back to normal)
   └─ If failure → OPEN (still broken)
```

---

### Real Example

**Your Service → Payment API:**

```
10:00:00 - Circuit: CLOSED ✅
  Request 1: Success ✅
  Request 2: Success ✅
  Request 3: Success ✅
  Failure count: 0

10:00:10 - Payment API goes down
  Request 4: Fail (timeout 30s) ❌
  Request 5: Fail (timeout 30s) ❌
  Request 6: Fail (timeout 30s) ❌
  Failure count: 3/5 = 60% ⚠️

10:00:15 - Circuit: OPEN 🚨
  Threshold reached (50% failures)
  Request 7: REJECTED immediately (no 30s wait!)
  Request 8: REJECTED immediately
  Request 9: REJECTED immediately
  
  Users see: "Payment service temporarily unavailable. Please try again in 1 minute."
  
  Your service: Still healthy! ✅
  (Not wasting resources on timeouts)

10:00:45 - Circuit: HALF-OPEN 🔄
  (30 seconds have passed)
  Request 10: Let's try one request...
  Result: Still failing ❌
  Circuit: OPEN again 🚨
  Wait another 30 seconds...

10:01:15 - Circuit: HALF-OPEN 🔄
  Request 11: Let's try again...
  Result: Success! ✅
  Circuit: CLOSED ✅
  
  All requests flow normally again!
```

---

### Circuit Breaker Configuration

```python
circuit_breaker = CircuitBreaker(
    failure_threshold=5,      # Open after 5 failures
    success_threshold=2,      # Close after 2 successes
    timeout=30,               # Wait 30s before retry
    expected_exception=TimeoutError
)

@circuit_breaker
def call_payment_api():
    response = requests.post(
        'https://payment-api.example.com/charge',
        timeout=5
    )
    return response
```

**What This Does:**
```
1. Tracks failures
2. After 5 failures → Opens circuit
3. Waits 30 seconds
4. Tries 1 request
5. If success → Tries 1 more
6. If both succeed → Closes circuit (back to normal)
```

---

### Benefits

**1. Fail Fast**
```
Without: Wait 30 seconds for timeout
With: Fail immediately (0.001 seconds)
```

**2. Prevent Cascading Failures**
```
Without: Your service crashes when dependency is down
With: Your service stays healthy, shows graceful error
```

**3. Automatic Recovery**
```
Without: Manual intervention needed
With: Automatically retries and recovers
```

**4. Better User Experience**
```
Without: User waits 30 seconds, sees cryptic error
With: User sees immediate, friendly error message
```

---

## Summary: How Everything Fits Together

```
1. 🎯 Set SLOs (Your promises to users)
   ↓
2. 📊 Monitor with Metrics, Logs, Traces
   ↓
3. 🚨 Alert when SLO at risk (Multi-burn-rate)
   ↓
4. 🛡️ Protect with Circuit Breakers
   ↓
5. 🚀 Deploy safely with Canaries
   ↓
6. 💥 Test with Chaos Engineering
   ↓
7. 📈 Measure MTTD/MTTA/MTTR
   ↓
8. 📝 Learn from Postmortems
   ↓
9. 🔄 Improve and repeat!
```

**The Goal:**
Build systems that are:
- **Observable** (you can see what's happening)
- **Resilient** (they handle failures gracefully)
- **Reliable** (they meet their SLOs)
- **Improvable** (they get better over time)

All explained in simple terms! 🎉
