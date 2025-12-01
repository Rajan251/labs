# Runbook Template

Use this template to create new runbooks for common incidents.

---

# [Alert Name] - [Service Name]

**Alert:** `AlertName`  
**Severity:** P0 / P1 / P2 / P3  
**Team:** Platform / Backend / Database / etc.

## Symptoms

Describe what users or systems are experiencing:
- What is broken or degraded?
- What metrics are out of range?
- What errors are being logged?

Example:
- P95 latency > 500ms for 5+ minutes
- 5xx error rate > 2%
- Users reporting slow page loads

## Impact

Describe the business and user impact:
- How many users are affected?
- What functionality is unavailable?
- What is the revenue/business impact?

Example:
- ~5,000 users experiencing slow response times
- Checkout flow degraded
- Estimated revenue impact: $X/hour

## Immediate Checks

Quick diagnostic steps to understand the issue:

1. **Check service health**
   ```bash
   kubectl get pods -n <namespace>
   kubectl describe pod <pod-name> -n <namespace>
   ```

2. **View recent logs**
   ```bash
   kubectl logs deployment/<service-name> -n <namespace> --tail=200
   kubectl logs deployment/<service-name> -n <namespace> --previous  # if pod restarted
   ```

3. **Check metrics dashboard**
   - [Service Dashboard](http://localhost:3000/d/service-overview)
   - [SLO Dashboard](http://localhost:3000/d/slo-tracking)

4. **Check dependencies**
   - Database: [DB Dashboard](http://localhost:3000/d/postgres)
   - Cache: [Redis Dashboard](http://localhost:3000/d/redis)
   - External APIs: [API Health](http://status.example.com)

## Automated Actions

List any automated remediation that may have already been attempted:

- ✅ **Auto-restart enabled**: Max 3 times per hour
- ✅ **Auto-scale enabled**: Triggers at 80% CPU
- ❌ **Auto-rollback disabled**: Requires manual approval

## Manual Remediation Steps

Step-by-step instructions to resolve the issue:

### Option 1: Restart Service
```bash
# Restart the deployment (logs action automatically)
kubectl rollout restart deployment/<service-name> -n <namespace>

# Watch the rollout
kubectl rollout status deployment/<service-name> -n <namespace>

# Verify pods are running
kubectl get pods -n <namespace> | grep <service-name>
```

### Option 2: Scale Up
```bash
# Increase replicas
kubectl scale deployment/<service-name> --replicas=5 -n <namespace>

# Verify scaling
kubectl get deployment <service-name> -n <namespace>
```

### Option 3: Rollback to Previous Version
```bash
# View rollout history
kubectl rollout history deployment/<service-name> -n <namespace>

# Rollback to previous version
kubectl rollout undo deployment/<service-name> -n <namespace>

# Or rollback to specific revision
kubectl rollout undo deployment/<service-name> --to-revision=<revision> -n <namespace>
```

### Option 4: Database-Specific Actions
```bash
# Check slow queries
kubectl exec -it <postgres-pod> -n <namespace> -- psql -U <user> -d <database> -c "SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# Check active connections
kubectl exec -it <postgres-pod> -n <namespace> -- psql -U <user> -d <database> -c "SELECT count(*) FROM pg_stat_activity;"

# Kill long-running queries (use with caution)
kubectl exec -it <postgres-pod> -n <namespace> -- psql -U <user> -d <database> -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'active' AND query_start < now() - interval '5 minutes';"
```

### Option 5: Clear Cache
```bash
# Clear Redis cache
kubectl exec -it <redis-pod> -n <namespace> -- redis-cli FLUSHALL

# Or clear specific keys
kubectl exec -it <redis-pod> -n <namespace> -- redis-cli DEL <key-pattern>
```

## Verification

After applying remediation, verify the issue is resolved:

1. **Check metrics**
   - Error rate back to normal (< 1%)
   - Latency within SLO (P95 < 500ms)
   - Service availability restored

2. **Check logs**
   ```bash
   kubectl logs deployment/<service-name> -n <namespace> --tail=50
   ```

3. **Test endpoint**
   ```bash
   curl -v https://<service-url>/health
   ```

4. **Monitor for 10-15 minutes**
   - Ensure issue doesn't recur
   - Watch for any new alerts

## Escalation

If the issue persists after attempting remediation:

1. **Primary escalation:** @platform-team in Slack
2. **Secondary escalation:** @engineering-manager
3. **Database issues:** @database-team
4. **External API issues:** Contact vendor support

**Escalate immediately if:**
- Issue affects > 50% of users
- Revenue-critical functionality down
- Data loss or security concern
- Issue persists > 30 minutes

## Post-Incident

After resolving the incident:

1. **Update incident record**
   - Mark as resolved in incident API
   - Add resolution notes

2. **Create postmortem** (for P0/P1)
   - Use automated template
   - Schedule review within 48 hours

3. **Create follow-up tasks**
   - Fix root cause
   - Improve monitoring/alerting
   - Update runbook if needed

## Related Links

- **Dashboard:** [Service Overview](http://localhost:3000/d/service-overview)
- **Logs:** [Kibana](http://kibana.example.com)
- **Metrics:** [Prometheus](http://localhost:9090)
- **Incident History:** [Incident API](http://localhost:8000/incidents)
- **Documentation:** [Service Docs](https://docs.example.com/services/<service-name>)

## Runbook Metadata

- **Owner:** @platform-team
- **Last Updated:** 2025-12-01
- **Version:** 1.0
- **Tested:** Yes / No
- **Auto-remediation:** Partial (restart only)

## Notes

Add any additional context, known issues, or tips:

- This issue typically occurs during peak traffic hours
- Recent deployment may have introduced regression
- Check #incidents channel for similar recent issues
- Consider increasing resource limits if recurring
