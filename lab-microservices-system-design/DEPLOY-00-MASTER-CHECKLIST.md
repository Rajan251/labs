# Production Deployment Master Checklist

Complete step-by-step guide for deploying the microservices system to a production Ubuntu server.

## 📋 Overview

This master checklist links to detailed guides for each component. Follow in order.

---

## ✅ Pre-Deployment Checklist

### Server Requirements
- [ ] Ubuntu Server 20.04 LTS or 22.04 LTS
- [ ] Minimum 4GB RAM (8GB recommended)
- [ ] Minimum 2 CPU cores (4 cores recommended)
- [ ] Minimum 50GB disk space (100GB recommended)
- [ ] Root or sudo access
- [ ] Static IP address or domain name
- [ ] Firewall access (ports 80, 443, 22)

### Network Requirements
- [ ] Server accessible via SSH
- [ ] Ports 80 (HTTP) and 443 (HTTPS) open
- [ ] Port 22 (SSH) open for management
- [ ] Optional: Port 15672 for RabbitMQ management (restrict to admin IPs)
- [ ] Optional: Port 27017 for MongoDB (restrict to localhost or VPN)

### Security Requirements
- [ ] SSH key-based authentication configured
- [ ] Password authentication disabled
- [ ] Firewall (UFW) ready to configure
- [ ] SSL/TLS certificate ready (Let's Encrypt or commercial)
- [ ] Backup strategy planned

---

## 📚 Deployment Guides (Follow in Order)

### 1. Server Setup
**Document:** `DEPLOY-01-SERVER-SETUP.md`
- [ ] Initial Ubuntu server configuration
- [ ] User setup and SSH hardening
- [ ] Firewall configuration
- [ ] System updates and security

**Estimated Time:** 30 minutes

---

### 2. Docker Installation
**Document:** `DEPLOY-02-DOCKER-INSTALL.md`
- [ ] Install Docker Engine
- [ ] Install Docker Compose
- [ ] Configure Docker daemon
- [ ] User permissions setup

**Estimated Time:** 15 minutes

---

### 3. MongoDB Setup
**Document:** `DEPLOY-03-MONGODB-SETUP.md`
- [ ] MongoDB container deployment
- [ ] Authentication configuration
- [ ] Database initialization
- [ ] Backup configuration
- [ ] Performance tuning

**Estimated Time:** 20 minutes

---

### 4. Redis Setup
**Document:** `DEPLOY-04-REDIS-SETUP.md`
- [ ] Redis container deployment
- [ ] Password authentication
- [ ] Persistence configuration
- [ ] Memory limits
- [ ] Performance tuning

**Estimated Time:** 15 minutes

---

### 5. RabbitMQ Setup
**Document:** `DEPLOY-05-RABBITMQ-SETUP.md`
- [ ] RabbitMQ container deployment
- [ ] User and vhost configuration
- [ ] Queue setup
- [ ] Management UI security
- [ ] Performance tuning

**Estimated Time:** 20 minutes

---

### 6. Nginx Setup
**Document:** `DEPLOY-06-NGINX-SETUP.md`
- [ ] Nginx container deployment
- [ ] SSL/TLS certificate installation
- [ ] HTTPS configuration
- [ ] Rate limiting tuning
- [ ] Security headers

**Estimated Time:** 30 minutes

---

### 7. FastAPI Application Deployment
**Document:** `DEPLOY-07-FASTAPI-DEPLOY.md`
- [ ] Application code deployment
- [ ] Environment configuration
- [ ] Container build and deployment
- [ ] Health check verification
- [ ] Scaling configuration

**Estimated Time:** 25 minutes

---

### 8. Celery Workers Deployment
**Document:** `DEPLOY-08-CELERY-DEPLOY.md`
- [ ] Worker container deployment
- [ ] Concurrency configuration
- [ ] Beat scheduler setup
- [ ] Queue monitoring
- [ ] Auto-scaling setup

**Estimated Time:** 20 minutes

---

### 9. Monitoring & Logging Setup
**Document:** `DEPLOY-09-MONITORING-SETUP.md`
- [ ] Log aggregation setup
- [ ] Container monitoring
- [ ] Alert configuration
- [ ] Dashboard setup
- [ ] Health check automation

**Estimated Time:** 40 minutes

---

### 10. Security Hardening
**Document:** `DEPLOY-10-SECURITY-HARDENING.md`
- [ ] SSL/TLS enforcement
- [ ] Secrets management
- [ ] Network isolation
- [ ] Access control
- [ ] Security scanning

**Estimated Time:** 30 minutes

---

### 11. Backup & Recovery
**Document:** `DEPLOY-11-BACKUP-RECOVERY.md`
- [ ] Database backup automation
- [ ] Volume backup strategy
- [ ] Recovery procedures
- [ ] Disaster recovery plan
- [ ] Backup testing

**Estimated Time:** 30 minutes

---

### 12. Final Verification
**Document:** `DEPLOY-12-FINAL-VERIFICATION.md`
- [ ] End-to-end testing
- [ ] Load testing
- [ ] Failover testing
- [ ] Performance verification
- [ ] Documentation review

**Estimated Time:** 45 minutes

---

## 📊 Deployment Progress Tracker

| Phase | Document | Status | Time | Completed |
|-------|----------|--------|------|-----------|
| 1 | Server Setup | ⬜ Not Started | 30 min | ☐ |
| 2 | Docker Install | ⬜ Not Started | 15 min | ☐ |
| 3 | MongoDB Setup | ⬜ Not Started | 20 min | ☐ |
| 4 | Redis Setup | ⬜ Not Started | 15 min | ☐ |
| 5 | RabbitMQ Setup | ⬜ Not Started | 20 min | ☐ |
| 6 | Nginx Setup | ⬜ Not Started | 30 min | ☐ |
| 7 | FastAPI Deploy | ⬜ Not Started | 25 min | ☐ |
| 8 | Celery Deploy | ⬜ Not Started | 20 min | ☐ |
| 9 | Monitoring | ⬜ Not Started | 40 min | ☐ |
| 10 | Security | ⬜ Not Started | 30 min | ☐ |
| 11 | Backup | ⬜ Not Started | 30 min | ☐ |
| 12 | Verification | ⬜ Not Started | 45 min | ☐ |
| **TOTAL** | | | **5 hours** | |

---

## 🚨 Critical Notes

### Before You Start
1. **Backup existing data** if upgrading
2. **Plan maintenance window** (recommended: 6 hours)
3. **Notify users** of scheduled downtime
4. **Have rollback plan** ready
5. **Test in staging** environment first

### During Deployment
1. **Follow documents in order** - dependencies matter
2. **Complete each checklist** before moving to next
3. **Document any deviations** from standard procedure
4. **Save all configuration files** in version control
5. **Test after each major step**

### After Deployment
1. **Monitor for 24 hours** closely
2. **Check logs** for errors or warnings
3. **Verify backups** are running
4. **Test failover** procedures
5. **Update documentation** with any changes

---

## 📞 Emergency Contacts

**Before deployment, fill in:**

| Role | Name | Contact | Availability |
|------|------|---------|--------------|
| DevOps Lead | __________ | __________ | __________ |
| Database Admin | __________ | __________ | __________ |
| Security Team | __________ | __________ | __________ |
| On-Call Engineer | __________ | __________ | __________ |

---

## 🔄 Rollback Plan

If deployment fails:

1. **Stop all containers:**
   ```bash
   docker compose down
   ```

2. **Restore from backup:**
   ```bash
   # Restore MongoDB
   docker run --rm -v mongodb_backup:/backup -v mongodb_data:/data \
     ubuntu tar xzf /backup/mongodb_backup.tar.gz -C /data
   ```

3. **Revert to previous version:**
   ```bash
   git checkout <previous-commit>
   docker compose up -d
   ```

4. **Verify rollback:**
   ```bash
   curl http://localhost/health
   ```

---

## 📝 Post-Deployment Checklist

- [ ] All services running and healthy
- [ ] SSL/TLS certificates valid
- [ ] Monitoring and alerts active
- [ ] Backups configured and tested
- [ ] Documentation updated
- [ ] Team trained on new system
- [ ] Runbooks created for common tasks
- [ ] Incident response plan documented
- [ ] Performance baseline established
- [ ] Capacity planning completed

---

## 🎯 Success Criteria

Deployment is successful when:

- ✅ All health checks pass
- ✅ API responds within SLA (<100ms p95)
- ✅ No errors in logs for 1 hour
- ✅ Load test passes (1000+ concurrent users)
- ✅ Failover test successful
- ✅ Backups verified and restorable
- ✅ Monitoring dashboards showing green
- ✅ Security scan passes
- ✅ Documentation complete and reviewed
- ✅ Team sign-off received

---

## 📚 Quick Reference

### Essential Commands
```bash
# Check all services
docker compose ps

# View logs
docker compose logs -f

# Restart service
docker compose restart <service>

# Check resource usage
docker stats

# Backup database
docker compose exec mongodb mongodump --out /backup

# Check SSL certificate
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com
```

### Important Files
- `/home/rk/Documents/labs/lab-microservices-system-design/docker-compose.yml`
- `/home/rk/Documents/labs/lab-microservices-system-design/.env`
- `/home/rk/Documents/labs/lab-microservices-system-design/nginx/nginx.conf`

### Important URLs
- API Documentation: `https://yourdomain.com/docs`
- RabbitMQ Management: `https://yourdomain.com:15672`
- Health Check: `https://yourdomain.com/health`

---

**Total Estimated Deployment Time:** 5-6 hours
**Recommended Team Size:** 2-3 people
**Recommended Time:** Off-peak hours (e.g., Saturday 2 AM - 8 AM)

---

**Next Step:** Start with [DEPLOY-01-SERVER-SETUP.md](DEPLOY-01-SERVER-SETUP.md)
