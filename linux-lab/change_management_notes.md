# Change Management Process for Production Systems

**Level:** Expert / Change Manager / SRE
**Focus:** ITIL-aligned change control and risk management.

---

## 1. Change Classification

### 1.1 Standard Changes
*   **Definition**: Pre-approved, low-risk, documented procedures.
*   **Examples**: Password resets, certificate renewals, routine patching.
*   **Approval**: Pre-authorized. No CAB review needed.
*   **Documentation**: Follow runbook exactly.

### 1.2 Normal Changes
*   **Definition**: Medium risk, requires review and approval.
*   **Examples**: Application deployments, infrastructure changes.
*   **Approval**: CAB review required.
*   **Lead Time**: Minimum 5 business days notice.

### 1.3 Emergency Changes
*   **Definition**: Immediate action required, high risk.
*   **Examples**: Security patch for active exploit, production outage fix.
*   **Approval**: Emergency CAB (e-CAB) or designated authority.
*   **Documentation**: Retrospective within 24 hours.

---

## 2. Change Request Components

### 2.1 Business Justification
*   Why is this change needed?
*   What is the business impact of NOT doing it?

### 2.2 Technical Implementation
*   Step-by-step procedure.
*   Systems affected.
*   Dependencies.

### 2.3 Risk Assessment
| Risk | Likelihood | Impact | Mitigation |
| :--- | :--- | :--- | :--- |
| Database corruption | Low | High | Take backup before change |
| Service downtime | Medium | Medium | Schedule during low-traffic window |

### 2.4 Rollback Plan
*   **Trigger**: When to rollback (e.g., error rate >5%).
*   **Steps**: Exact commands to revert.
*   **Time**: How long rollback takes.

### 2.5 Testing Plan
*   **Pre-Production**: Test in staging first.
*   **Validation**: How to verify success (smoke tests, health checks).

### 2.6 Communication Plan
*   **Stakeholders**: Who needs to know?
*   **Timing**: When to notify (before, during, after)?
*   **Channels**: Email, Slack, status page.

---

## 3. Change Advisory Board (CAB)

### 3.1 Composition
*   **Technical Lead**: Infrastructure/Application experts.
*   **Business Representative**: Product/Business owner.
*   **Security**: InfoSec representative.
*   **Change Manager**: Facilitates meeting.

### 3.2 Meeting Frequency
*   **Weekly**: Review upcoming normal changes.
*   **Emergency**: Ad-hoc for emergency changes.

### 3.3 Decision Criteria
*   **Approve**: Low risk, well-documented, tested.
*   **Defer**: Needs more information or testing.
*   **Reject**: Risk too high, insufficient justification.

---

## 4. Implementation Procedures

### 4.1 Change Window Scheduling
*   **Production**: Tuesday/Thursday 2-4 AM (low traffic).
*   **Blackout Periods**: No changes during Black Friday, tax season, etc.

### 4.2 Pre-Implementation Checklist
- [ ] Backup taken and verified
- [ ] Rollback plan tested
- [ ] Stakeholders notified
- [ ] Monitoring alerts configured
- [ ] On-call engineer available

### 4.3 Implementation Steps
1.  **Start**: Announce in Slack: "Change #12345 starting".
2.  **Execute**: Follow runbook step-by-step.
3.  **Verify**: Run smoke tests after each major step.
4.  **Complete**: Announce: "Change #12345 complete. All systems green."

### 4.4 Post-Implementation Validation
*   **Immediate**: Health checks pass.
*   **24 Hours**: Monitor error rates, performance metrics.
*   **7 Days**: No related incidents.

---

## 5. Emergency Change Process

### 5.1 Authorization
*   **Threshold**: Production down or security breach.
*   **Decision Maker**: On-call manager or CTO.

### 5.2 Documentation (Retrospective)
*   **Within 24 Hours**: Create change ticket with full details.
*   **Within 48 Hours**: Post-mortem with lessons learned.

### 5.3 Communication
*   **Immediate**: Status page update: "Investigating issue".
*   **Every 30 Min**: Progress updates.
*   **Post-Fix**: Root cause and resolution summary.

---

## 6. Metrics and Improvement

### 6.1 Change Success Rate
*   **Target**: >95% of changes succeed without rollback.
*   **Tracking**: `(Successful Changes / Total Changes) * 100`.

### 6.2 Rollback Frequency
*   **Target**: <5% rollback rate.
*   **Analysis**: Why did rollback occur? Improve testing.

### 6.3 Change Duration
*   **Estimate vs Actual**: Are we estimating accurately?
*   **Goal**: Reduce variance to <20%.

### 6.4 Incident Correlation
*   **Question**: Did a recent change cause this incident?
*   **Tool**: Correlate incident timestamps with change deployments.

---

## 7. Tooling Integration

### 7.1 Ticketing System (Jira, ServiceNow)
*   **Workflow**: Draft -> CAB Review -> Approved -> Scheduled -> Implemented -> Closed.
*   **Automation**: Auto-notify stakeholders on status change.

### 7.2 Configuration Management
*   **Ansible/Puppet**: Track what changed on which servers.
*   **Git**: All infrastructure code changes tracked.

### 7.3 Monitoring Correlation
*   **Datadog/Prometheus**: Tag deployments with change ID.
*   **Alerts**: "Error rate spiked after Change #12345".
