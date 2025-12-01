# High Error Rate - Service Investigation

**Alert:** `HighErrorRate`  
**Severity:** P1 (Page)  
**Team:** Backend

## Symptoms

- 5xx error rate > 5% for 5+ minutes
- Users experiencing failed requests
- Increased error logs in application
- Possible spike in error monitoring dashboards

## Impact

- **Users Affected:** Varies (5-100% depending on error type)
- **Functionality:** Service requests failing
- **Business Impact:** User frustration, potential revenue loss
- **SLO Impact:** Error budget consumption accelerated

## Immediate Checks

1. **Check service health and pod status**
   ```bash
   kubectl get pods -n <namespace>
   kubectl describe pod <pod-name> -n <namespace>
   ```

2. **View recent error logs**
   ```bash
   # Last 200 lines
   kubectl logs deployment/<service-name> -n <namespace> --tail=200 | grep -i error
   
   # If pod restarted, check previous logs
   kubectl logs deployment/<service-name> -n <namespace> --previous | grep -i error
   ```

3. **Check error rate in Prometheus**
   ```promql
   sum(rate(http_requests_total{status=~"5..", service="<service-name>"}[5m]))
   /
   sum(rate(http_requests_total{service="<service-name>"}[5m]))
   ```

4. **Check dashboards**
   - [Service Dashboard](http://localhost:3000/d/service-overview?var-service=<service-name>)
   - [Error Rate Dashboard](http://localhost:3000/d/error-tracking)

5. **Check dependencies**
   - **Database:** Check connection pool, slow queries
     ```bash
     kubectl exec -it <postgres-pod> -n <namespace> -- psql -U <user> -d <database> -c "SELECT count(*) FROM pg_stat_activity;"
     ```
   - **Redis:** Check connectivity and memory
     ```bash
     kubectl exec -it <redis-pod> -n <namespace> -- redis-cli ping
     kubectl exec -it <redis-pod> -n <namespace> -- redis-cli info memory
     ```
   - **External APIs:** Check status pages

## Automated Actions

- ✅ **Auto-restart enabled**: Triggers after 3 consecutive failures (max 3/hour)
- ✅ **Auto-scale enabled**: Triggers at 80% CPU or 1000 req/s
- ❌ **Auto-rollback disabled**: Requires manual approval

## Common Root Causes

1. **Recent Deployment**
   - New code introduced bugs
   - Configuration change
   - Dependency version change

2. **Database Issues**
   - Connection pool exhausted
   - Slow queries causing timeouts
   - Database down or degraded

3. **External API Failures**
   - Third-party service down
   - API rate limiting
   - Network connectivity issues

4. **Resource Exhaustion**
   - Memory leaks causing OOM
   - CPU throttling
   - Disk space full

5. **Traffic Spike**
   - Unexpected load increase
   - DDoS attack
   - Retry storms

## Manual Remediation Steps

### Step 1: Identify Error Type

Check logs for specific error patterns:
```bash
# Group errors by type
kubectl logs deployment/<service-name> -n <namespace> --tail=500 | grep -i error | sort | uniq -c | sort -rn | head -20
```

### Step 2: Quick Fixes Based on Error Type

#### If Database Connection Errors:
```bash
# Check database connectivity
kubectl exec -it <app-pod> -n <namespace> -- nc -zv <db-host> 5432

# Check connection pool
kubectl exec -it <postgres-pod> -n <namespace> -- psql -U <user> -d <database> -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

# If pool exhausted, restart app to reset connections
kubectl rollout restart deployment/<service-name> -n <namespace>
```

#### If Memory/OOM Errors:
```bash
# Check memory usage
kubectl top pods -n <namespace> | grep <service-name>

# Increase memory limits (temporary)
kubectl set resources deployment/<service-name> -n <namespace> --limits=memory=2Gi

# Restart to clear memory
kubectl rollout restart deployment/<service-name> -n <namespace>
```

#### If External API Errors:
```bash
# Check external API status
curl -v https://<external-api>/health

# Enable circuit breaker or fallback (if available)
# Update config map with circuit breaker enabled
kubectl edit configmap <service-config> -n <namespace>

# Restart to apply config
kubectl rollout restart deployment/<service-name> -n <namespace>
```

#### If Recent Deployment Issue:
```bash
# Check deployment history
kubectl rollout history deployment/<service-name> -n <namespace>

# Rollback to previous version
kubectl rollout undo deployment/<service-name> -n <namespace>

# Monitor error rate after rollback
watch -n 5 'kubectl logs deployment/<service-name> -n <namespace> --tail=50 | grep -c error'
```

### Step 3: Scale if Needed
```bash
# If errors due to load, scale up
kubectl scale deployment/<service-name> --replicas=10 -n <namespace>

# Verify scaling
kubectl get deployment <service-name> -n <namespace>
```

### Step 4: Clear Cache (if applicable)
```bash
# Clear Redis cache to force fresh data
kubectl exec -it <redis-pod> -n <namespace> -- redis-cli FLUSHDB

# Or clear specific cache keys
kubectl exec -it <redis-pod> -n <namespace> -- redis-cli --scan --pattern '<service-name>:*' | xargs kubectl exec -it <redis-pod> -n <namespace> -- redis-cli DEL
```

## Verification

1. **Check error rate metric**
   ```promql
   sum(rate(http_requests_total{status=~"5..", service="<service-name>"}[5m]))
   /
   sum(rate(http_requests_total{service="<service-name>"}[5m]))
   ```
   Should be < 0.01 (1%)

2. **Check recent logs**
   ```bash
   kubectl logs deployment/<service-name> -n <namespace> --tail=100
   ```
   Should show no errors

3. **Test endpoint**
   ```bash
   for i in {1..10}; do curl -s -o /dev/null -w "%{http_code}\n" https://<service-url>/health; done
   ```
   All should return 200

4. **Monitor for 15 minutes**
   - Watch error rate dashboard
   - Check for new alerts
   - Verify user reports stopped

## Escalation

**Escalate if:**
- Error rate > 10% after 10 minutes
- Database team needed (DB-related errors)
- External vendor needed (third-party API issues)
- Issue persists after rollback

**Escalation Path:**
1. **Primary:** @backend-team in #backend-alerts
2. **Database issues:** @database-team in #database-alerts
3. **After 20 min:** @engineering-manager
4. **After 30 min:** @on-call-director

## Post-Incident

1. **Document resolution** in incident record
2. **Create postmortem** (required for P1)
3. **Follow-up tasks:**
   - Fix root cause
   - Add better error handling
   - Improve monitoring/alerting
   - Update resource limits if needed
   - Add integration tests

## Related Links

- **Dashboard:** [Service Overview](http://localhost:3000/d/service-overview)
- **Error Tracking:** [Sentry/Error Monitoring](https://sentry.io)
- **Logs:** [Kibana](http://kibana.example.com)
- **Runbook:** [Database Slow](./database_slow.md)
- **Runbook:** [Pod Crashloop](./pod_crashloop.md)

## Runbook Metadata

- **Owner:** @backend-team
- **Last Updated:** 2025-12-01
- **Version:** 1.2
- **Tested:** Yes (2025-11-15)
- **Auto-remediation:** Partial (restart only)

## Notes

- Most common cause: Database connection pool exhaustion
- Check for recent deployments in #deployments channel
- If recurring, consider increasing connection pool size
- Error rate typically recovers within 5 minutes of remediation
- Document any new error patterns discovered
