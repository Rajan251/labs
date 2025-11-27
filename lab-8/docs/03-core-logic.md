# 5. Inventory & Metadata Enrichment

## Collection Methods
To make cost data actionable, we must know *what* the resource is and *who* owns it.
*   **Cloud APIs**: Periodic scans (e.g., every 6 hours) of `ec2:DescribeInstances`, `rds:DescribeDBInstances`, etc., to capture current state, tags, and configuration.
*   **Terraform State**: Parsing `.tfstate` files to map resources back to their IaC definitions and git repositories.
*   **Kubernetes**: `kube-state-metrics` to map Pods/PVCs to Namespaces, Deployments, and Labels.

## Enrichment Techniques
*   **CMDB Integration**: Join resource IDs with an internal CMDB (e.g., ServiceNow) to fetch Business Unit, Cost Center, and Application Owner.
*   **Git Metadata**: Tag resources with the `git_commit_sha` and `repo_url` of the code that deployed them.
*   **Autoscaling Context**: Identify if an instance is part of an ASG/VMSS. If so, rightsizing must target the Group configuration, not the individual instance.

## Tagging Strategy & Enforcement
*   **Mandatory Tags**: `Owner`, `Environment`, `CostCenter`, `Service`, `Application`.
*   **Enforcement**:
    *   **Soft**: Daily reports of untagged resources sent to engineering leads.
    *   **Hard**: CI/CD pipeline failure (via OPA/Checkov) if tags are missing in Terraform.
    *   **Auto-Tagging**: Lambda functions that listen to `RunInstances` events and automatically apply the creator's IAM username as the `Owner` tag.

---

# 6. Cost Modeling & Allocation

## Allocation Models
1.  **Direct Allocation**: 100% of cost assigned to the resource's `CostCenter` tag.
2.  **Shared Services**:
    *   **Proportional**: Split costs of shared resources (e.g., K8s Cluster, Transit Gateway) based on consumption metrics (CPU/Network) of the tenant services.
    *   **Fixed**: Split costs evenly across all consuming teams (e.g., Development Environment Base Infrastructure).
3.  **Unallocated**: Any cost not covered by the above is flagged as `Unallocated` and reviewed weekly.

## Amortization
*   **Reservations (RI/SP)**: We use **Amortized Cost** for all internal reporting. This spreads the one-time upfront payments across the reservation term, preventing "spiky" budgets.
*   **Spot Instances**: Treated as standard pay-as-you-go but highlighted for volatility risk.

## Example: Shared Load Balancer
A shared ALB costs $50/month.
*   Service A processes 10GB (20%)
*   Service B processes 40GB (80%)
*   **Allocation**: Service A is charged $10, Service B is charged $40.

---

# 7. Rightsizing Engine & Recommendation Logic

## Rules-Based Logic
We use configurable thresholds to identify inefficiencies.

| Category | Rule Logic | Thresholds (Example) |
| :--- | :--- | :--- |
| **Idle** | CPU < X% AND Net < Y MB | CPU < 1% (Max), Network < 1MB (Sum) over 7 days |
| **Underutilized** | CPU < X% AND Mem < Y% | CPU < 20% (Max), Mem < 30% (Max) over 14 days |
| **Overprovisioned** | CPU > X% consistently | CPU > 80% (Avg) for 4+ hours daily |
| **Modernize** | Older Gen Family | e.g., `m4.large` -> `m5.large` (Better price/perf) |

## ML/Statistical Approaches
*   **Seasonality**: Use Holt-Winters or Prophet to detect if "low usage" is just a weekend dip vs. true waste.
*   **Clustering**: Group similar workloads (e.g., "Web Servers") and recommend a standard size for the cluster based on the 95th percentile of the group's usage.

## Output Format
```json
{
  "resource_id": "i-0123456789abcdef0",
  "current_type": "m5.2xlarge",
  "recommended_type": "m5.large",
  "estimated_monthly_savings": 145.20,
  "risk_score": "LOW",
  "confidence": 0.95,
  "justification": "Max CPU 12% over last 30 days; Memory 25%. Downsizing safe.",
  "metrics": {
    "p95_cpu": 11.5,
    "p95_mem": 24.0
  }
}
```

---

# 9. Reservation & Commitment Optimizer

## Analysis Logic
1.  **Historical Usage**: Analyze hourly usage over the last 60-90 days.
2.  **Watermark Analysis**: Determine the "Min", "Avg", and "Max" usage for each instance family/region.
3.  **Break-Even**: Calculate if the RI/SP discount outweighs the risk of lock-in.
4.  **Recommendation**: Suggest purchasing RIs/SPs to cover the **Min** (Base) load, leaving the variable load for On-Demand or Spot.

## Recommendation Table
| Family | Region | Term | Payment | Qty | Est. Savings |
| :--- | :--- | :--- | :--- | :--- | :--- |
| m5 | us-east-1 | 1yr | All Upfront | 10 | $450/mo |
| r5 | us-west-2 | 3yr | Partial | 5 | $800/mo |

## Risk Mitigation
*   **Convertible RIs**: Prioritize Convertible RIs or Compute Savings Plans for volatile environments to allow changing families/regions.
*   **Coverage Target**: Aim for 70-80% coverage, not 100%, to maintain flexibility for architectural changes.

---

# 10. Kubernetes-specific Rightsizing

## Metrics Integration
*   **Source**: Prometheus (via `kube-state-metrics` and `cadvisor`).
*   **Key Metrics**: `container_cpu_usage_seconds_total`, `container_memory_working_set_bytes`.

## Logic
*   **Requests vs. Usage**: Compare the configured `requests` against actual usage.
    *   If Usage << Requests: **Slack** (Wasted reservation). Recommend lowering Requests.
    *   If Usage ~= Limits: **Throttling Risk**. Recommend increasing Limits.
*   **HPA/VPA**:
    *   If HPA is active, rightsizing must tune the HPA `targetUtilization` rather than static replicas.
    *   Use VPA in "Recommendation Mode" to generate suggested values without auto-applying them initially.

## Ephemeral Workloads
*   **Jobs/CronJobs**: Exclude from standard long-running analysis. Optimize based on "Cost per Run" efficiency.
*   **Spot Nodes**: Aggressively schedule batch/stateless pods on Spot Node Pools.
