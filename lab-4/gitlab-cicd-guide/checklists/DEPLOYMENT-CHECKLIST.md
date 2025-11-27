# Deployment Checklist

Pre-deployment and post-deployment checklist for production releases.

## Pre-Deployment Checklist

### Code & Testing

- [ ] All tests passing in CI/CD pipeline
- [ ] Code review completed and approved
- [ ] Security scans passed (SAST, Dependency, Container)
- [ ] Performance testing completed
- [ ] Load testing completed (if applicable)
- [ ] Regression testing completed

### Documentation

- [ ] Release notes prepared
- [ ] Changelog updated
- [ ] API documentation updated
- [ ] Runbook updated
- [ ] Rollback plan documented
- [ ] Known issues documented

### Infrastructure

- [ ] Infrastructure capacity verified
- [ ] Database backups verified
- [ ] Monitoring and alerting configured
- [ ] Log aggregation configured
- [ ] SSL certificates valid
- [ ] DNS records configured

### Database

- [ ] Database migrations tested in staging
- [ ] Migration rollback tested
- [ ] Database backup completed
- [ ] Migration execution time estimated
- [ ] Downtime window communicated (if applicable)

### Dependencies

- [ ] All external dependencies available
- [ ] Third-party API status verified
- [ ] CDN status verified
- [ ] DNS propagation completed

### Communication

- [ ] Stakeholders notified of deployment
- [ ] Maintenance window scheduled (if applicable)
- [ ] Status page updated
- [ ] Support team briefed
- [ ] On-call engineer assigned

### Approvals

- [ ] Product owner approval
- [ ] Technical lead approval
- [ ] Security team approval (if required)
- [ ] Change management approval (if required)

---

## Deployment Execution

### Pre-Deployment

- [ ] Verify current production version
- [ ] Take final database backup
- [ ] Put application in maintenance mode (if required)
- [ ] Notify users of maintenance (if applicable)

### Deployment

- [ ] Tag release in Git
- [ ] Trigger production deployment pipeline
- [ ] Monitor deployment progress
- [ ] Verify container image pulled successfully
- [ ] Verify pods/containers started successfully
- [ ] Run database migrations (if applicable)

### Verification

- [ ] Health check endpoint responding
- [ ] Application logs show no errors
- [ ] Database connections successful
- [ ] External integrations working
- [ ] Critical user flows tested
- [ ] Performance metrics normal

---

## Post-Deployment Checklist

### Immediate (0-15 minutes)

- [ ] Verify deployment completed successfully
- [ ] Check application health checks
- [ ] Monitor error rates
- [ ] Monitor response times
- [ ] Check application logs for errors
- [ ] Verify database queries executing normally
- [ ] Test critical user paths
- [ ] Verify external integrations working

### Short-term (15-60 minutes)

- [ ] Monitor CPU and memory usage
- [ ] Monitor database performance
- [ ] Check for increased error rates
- [ ] Verify background jobs processing
- [ ] Check queue depths
- [ ] Monitor cache hit rates
- [ ] Review user feedback/support tickets

### Medium-term (1-24 hours)

- [ ] Review application metrics
- [ ] Analyze performance trends
- [ ] Check for memory leaks
- [ ] Review error tracking (Sentry, etc.)
- [ ] Verify scheduled jobs executed
- [ ] Check data consistency
- [ ] Review security logs

### Communication

- [ ] Notify stakeholders of successful deployment
- [ ] Update status page
- [ ] Close maintenance window
- [ ] Update documentation with actual deployment time
- [ ] Document any issues encountered

---

## Rollback Checklist

### Decision Criteria

Rollback if:
- [ ] Critical functionality broken
- [ ] Security vulnerability introduced
- [ ] Data corruption detected
- [ ] Performance degradation > 50%
- [ ] Error rate > 5%
- [ ] Unable to fix forward within 30 minutes

### Rollback Execution

- [ ] Notify stakeholders of rollback decision
- [ ] Trigger rollback pipeline or manual rollback
- [ ] Rollback database migrations (if applicable)
- [ ] Verify previous version deployed
- [ ] Run health checks
- [ ] Verify critical functionality
- [ ] Monitor for stability

### Post-Rollback

- [ ] Document rollback reason
- [ ] Create incident report
- [ ] Schedule post-mortem
- [ ] Update status page
- [ ] Notify stakeholders
- [ ] Plan fix and re-deployment

---

## Environment-Specific Notes

### Staging Deployment

- Lower risk, can be more aggressive
- Good for final validation
- Test rollback procedures

### Production Deployment

- Higher risk, be conservative
- Deploy during low-traffic hours
- Have rollback plan ready
- Monitor closely

---

## Deployment Windows

### Recommended Deployment Times

- **Best**: Tuesday-Thursday, 10 AM - 2 PM (local time)
- **Avoid**: Fridays, weekends, holidays, end of month
- **Never**: During peak traffic hours, during critical business periods

---

## Monitoring Dashboards

Ensure these dashboards are open during deployment:

- [ ] Application performance dashboard
- [ ] Infrastructure metrics dashboard
- [ ] Error tracking dashboard
- [ ] Database performance dashboard
- [ ] User analytics dashboard

---

## Emergency Contacts

Keep these contacts readily available:

- On-call engineer: [Phone/Slack]
- Database admin: [Phone/Slack]
- Infrastructure team: [Phone/Slack]
- Product owner: [Phone/Slack]
- Security team: [Phone/Slack]

---

## Post-Deployment Review

Within 48 hours of deployment:

- [ ] Review deployment metrics
- [ ] Document lessons learned
- [ ] Update runbook with any new procedures
- [ ] Update this checklist if needed
- [ ] Share deployment report with team
