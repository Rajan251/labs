# 12. Reporting, Dashboards & UX

## Required Dashboards
We separate views by persona:
1.  **Executive View (FinOps/CTO)**:
    *   Total Spend vs Budget (MoM, YoY).
    *   Forecasted End-of-Month Spend.
    *   Top 5 Spenders (Teams/Services).
    *   Savings Realized (ROI of this platform).
2.  **Engineering View (Team Leads)**:
    *   Daily Spend by Service.
    *   Active Rightsizing Recommendations.
    *   Anomalies detected in last 24h.
    *   Unit Cost (e.g., Cost per API Request).
3.  **Optimization View**:
    *   RI/SP Coverage & Utilization.
    *   Waste Tracker (Idle resources, Unattached volumes).

## Example Dashboard Layout (Grafana)
*   **Row 1**: [Stat] Current Month Cost | [Stat] Forecast | [Stat] Savings Potential
*   **Row 2**: [Time Series] Daily Cost by Account (Stacked Bar)
*   **Row 3**: [Table] Top 10 Most Expensive Resources
*   **Row 4**: [Table] Active Rightsizing Recommendations (Actionable)

## Export & API
*   **Scheduled Reports**: PDF/CSV emailed weekly to Budget Owners.
*   **API**: `GET /api/v1/costs/summary?team=checkout` for integration into internal developer portals (Backstage).

---

# 13. Governance, Policy & FinOps Practices

## Policy Enforcement
We use a "Guardrails, not Gates" approach where possible, but strict blocks for egregious violations.
*   **Tagging Policy**:
    *   *Rule*: All resources must have `Owner` and `CostCenter`.
    *   *Enforcement*: SCP (AWS) / Azure Policy to deny creation if tags missing.
*   **Budget Alerts**:
    *   *Rule*: Alert Team Channel when 80% of monthly budget consumed.
    *   *Enforcement*: AWS Budgets / GCP Budget Alerts.
*   **Zombie Resource Policy**:
    *   *Rule*: Any EBS volume unattached for > 14 days is snapshotted and deleted.

## Governance Workflows
*   **Monthly Cost Review**: A 30-min meeting where Engineering Leads review their spend vs budget with FinOps.
*   **Exemption Process**: Teams can request exemption from rightsizing (e.g., "This instance needs high memory for cache warming") via a Jira ticket, which applies a `CostOpt:Exclude` tag.

---

# 15. Security, Privacy & Compliance

## Secure Storage
*   **Encryption**: All billing data in S3/GCS/Blob Storage is encrypted at rest (SSE-KMS) and in transit (TLS 1.2+).
*   **Access Control**: Only the Platform Service Account has write access. Humans have Read-Only access via assumed roles.
*   **Secrets**: API keys and database credentials stored in AWS Secrets Manager / HashiCorp Vault.

## Audit Trails
*   **Immutable Logs**: Every action taken by the platform (e.g., "Stopped instance i-123") is logged to a dedicated, locked-down S3 bucket with Object Lock enabled (WORM compliance).
*   **Traceability**: Logs include `Timestamp`, `Action`, `ResourceID`, `Trigger` (Auto/Manual), and `User` (if manual).

## Data Retention
*   **Billing Data**: Retained for 3 years for historical trend analysis.
*   **Detailed Metrics**: Retained for 90 days (high resolution), then downsampled.
*   **PII Handling**: If billing tags contain email addresses, a transformation layer hashes them (`sha256(email)`) before storage in the Data Warehouse.
