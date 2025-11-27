# 8. Automated Remediation & Safe Execution

## Remediation Actions
The platform supports a library of atomic actions:
*   **Compute**: `StopInstance`, `StartInstance`, `TerminateInstance`, `ResizeInstance`.
*   **Storage**: `DeleteSnapshot`, `DeleteVolume`, `LifecycleMoveToArchive`.
*   **Kubernetes**: `PatchDeployment` (update requests/limits), `CordonNode`.
*   **Databases**: `StopRDS` (for non-prod nights/weekends).

## Safety Measures
Automation is powerful but risky. We implement "Safe Mode" by default.
1.  **Dry-Run**: All actions first run in a mode that logs what *would* happen without making changes.
2.  **Approval Workflows**:
    *   **Manual**: Send a Slack message with "Approve" / "Reject" buttons.
    *   **Auto-Approve**: For low-risk environments (Dev/Sandbox) and high-confidence recommendations (e.g., Delete unattached volume > 30 days old).
3.  **Exclusion Tags**: Resources tagged `CostOpt:Exclude` or `Env:Prod` (configurable) are skipped by automation.
4.  **Change Windows**: Actions only execute during specified windows (e.g., M-F, 9am-5pm) to ensure engineers are available if issues arise.

## Example Playbook (AWS CLI)
**Stop Idle Instance:**
```bash
# Check for exclusion tag
TAG_CHECK=$(aws ec2 describe-tags --filters "Name=resource-id,Values=$INSTANCE_ID" "Name=key,Values=CostOpt:Exclude")
if [ -z "$TAG_CHECK" ]; then
  # Stop the instance
  aws ec2 stop-instances --instance-ids $INSTANCE_ID
  # Tag as stopped by automation
  aws ec2 create-tags --resources $INSTANCE_ID --tags Key=CostOpt:Action,Value=AutoStopped
fi
```

---

# 11. Anomaly Detection & Alerting

## Detection Strategies
1.  **Static Thresholds**: "Alert if S3 spend > $100/day". Simple but prone to noise.
2.  **Trend-Based**: "Alert if daily spend increases by > 20% vs. 7-day moving average".
3.  **Machine Learning**: Use Isolation Forests to detect outliers in multi-dimensional data (Service, Region, Account).

## Alert Routing
*   **Critical**: (e.g., > 50% spike) -> PagerDuty (On-Call Engineer).
*   **Warning**: (e.g., New expensive resource) -> Slack Channel (#finops-alerts).
*   **Info**: (e.g., Weekly summary) -> Email.

## Example Alert Payload
```json
{
  "alert_type": "COST_ANOMALY",
  "severity": "CRITICAL",
  "service": "AmazonRDS",
  "account": "Prod-Data-1",
  "detected_at": "2023-10-27T14:30:00Z",
  "details": "Spend spiked to $500/hr (Normal: $50/hr).",
  "root_cause": "New db.r5.24xlarge instance launched by user: jdoe.",
  "action_link": "https://platform.internal/anomalies/123"
}
```

---

# 14. Integrations & Automation

## Integrations
*   **Slack/Teams**: ChatOps for notifications and interactive approvals.
*   **Jira/ServiceNow**: Create tickets for rightsizing tasks that require manual engineering effort (e.g., architectural refactoring).
*   **CI/CD (GitHub/GitLab)**:
    *   **Pull Request Commenter**: "This PR adds 2 x m5.large instances. Est. Cost Impact: +$200/mo."
    *   **Policy Check**: Block builds that violate cost policies (e.g., "No gp2 volumes allowed, use gp3").

## Example Automation Flow
1.  **Trigger**: Rightsizing Engine identifies an idle RDS instance.
2.  **Notification**: Slack bot messages the `#team-backend` channel with the finding.
3.  **Interaction**: Engineer clicks "Snooze 1 Week" or "Approve Stop".
4.  **Execution**:
    *   If "Approve": Lambda function stops the RDS instance.
    *   If "Snooze": Recommendation is suppressed for 7 days.
5.  **Feedback**: Jira ticket created if "Refactor Needed" is selected.
