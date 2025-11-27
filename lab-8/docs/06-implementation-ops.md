# 16. Implementation Plan & Milestones

## Phased Rollout Strategy

### Phase 1: Foundation (Weeks 1-2)
*   **Goal**: Visibility.
*   **Tasks**:
    *   Enable CUR/Billing Exports in all clouds.
    *   Deploy Data Warehouse and Ingestion Pipelines.
    *   Build "Executive View" Dashboard.

### Phase 2: Enrichment & Attribution (Weeks 3-4)
*   **Goal**: Accountability.
*   **Tasks**:
    *   Implement Tagging Policies.
    *   Connect CMDB/Org Hierarchy.
    *   Build "Team View" Dashboards.

### Phase 3: Recommendations (Weeks 5-6)
*   **Goal**: Identification of Waste.
*   **Tasks**:
    *   Deploy Rightsizing Engine (Read-Only).
    *   Tune thresholds to reduce false positives.
    *   Generate first round of "Potential Savings" reports.

### Phase 4: Automation Pilot (Weeks 7-8)
*   **Goal**: Action.
*   **Tasks**:
    *   Enable "Safe Mode" automation on Non-Prod environments.
    *   Implement Slack/Jira integration for manual approvals.

### Phase 5: Optimization & Scale (Week 9+)
*   **Goal**: Continuous Improvement.
*   **Tasks**:
    *   Enable Reservation/SP Optimizer.
    *   Expand automation to Production (with strict approvals).
    *   Quarterly FinOps reviews.

---

# 18. CI / IaC / Dev Workflow Integration

## Terraform Annotation
We use a standard module wrapper to enforce tagging.
```hcl
module "standard_ec2" {
  source = "./modules/ec2"
  
  # Required Metadata
  owner       = "team-checkout"
  environment = "prod"
  cost_center = "cc-123"
  
  # Resource Specs
  instance_type = "m5.large"
}
```

## CI Cost Checks (Infracost)
Integrate tools like Infracost into GitHub Actions / GitLab CI.
*   **Pull Request**: Developer opens PR to change instance from `t3.micro` to `m5.4xlarge`.
*   **Bot Comment**: "⚠️ **Cost Warning**: This change increases monthly spend by **$1,200**. Budget impact: High."
*   **Gate**: Require Manager approval if delta > $500.

---

# 19. Observability, Metrics & Testing

## Platform Metrics
We monitor the platform itself:
*   **Ingestion Latency**: Time from Cloud Provider publication to Dashboard availability.
*   **Coverage**: % of resources with valid tags.
*   **Savings Realized**: Cumulative $ value of accepted recommendations.
*   **Error Rate**: % of remediation actions that failed.

## Testing Strategy
*   **Unit Tests**: Validate parsing logic for CUR files and Rightsizing rules.
*   **Integration Tests**: Spin up a "Test" VPC, launch a known idle instance, verify the platform recommends rightsizing.
*   **Canary**: Run automation on a "Canary" tag first before broad rollout.

---

# 20. Troubleshooting & Common Problems

| Issue | Probable Cause | Fix |
| :--- | :--- | :--- |
| **Missing Data in Dashboard** | CUR export failed or permissions revoked. | Check CloudProvider billing console and IAM roles. |
| **Currency Mismatch** | Azure export in EUR, AWS in USD. | Verify Normalization Layer exchange rate API connectivity. |
| **False Positive Rightsizing** | "Idle" instance is actually a Hot Standby. | Add `CostOpt:Exclude` tag or adjust "Idle" definition. |
| **Automation Failed** | API Rate Limiting or Insufficient Permissions. | Check Platform Logs and implement exponential backoff. |

---

# 21. Security & Operational Runbooks

## Playbook: Investigating Spend Spike
1.  **Alert Received**: "Account A spend up 200%".
2.  **Triage**: Open "Anomaly Dashboard". Identify Service (e.g., S3) and Resource (e.g., Bucket X).
3.  **Root Cause**: Check CloudTrail for `CreateBucket` or `PutObject` events in that timeframe.
4.  **Action**: Contact `Owner` tag. If unresponsive and critical, apply "Quarantine Policy" (Restrict access) or suspend resource if policy allows.

## Playbook: Emergency Rollback
1.  **Trigger**: Automation mistakenly stopped critical production instances.
2.  **Action**:
    *   **Stop Scheduler**: Pause Airflow DAGs.
    *   **Revert**: Run `revert_actions.py --window 1h` to restart instances stopped in the last hour.
    *   **Post-Mortem**: Analyze why the safety check failed.
