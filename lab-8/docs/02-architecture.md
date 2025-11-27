# 3. High-level Architecture & Components

The platform follows a modern data engineering and event-driven architecture. It separates data ingestion (Billing/Metrics) from the decision engine (Rightsizing/Anomalies) and the action layer (Remediation).

## Architecture Diagram

```ascii
                                  +---------------------+
                                  |   Orchestration     |
                                  |  (Apache Airflow)   |
                                  +----------+----------+
                                             |
       [Ingestion Layer]                     v                     [Analytics & Action Layer]
+-----------------------------+    +-------------------+    +--------------------------------+
|  AWS CUR / Cost Explorer    +--->+                   +--->+  Rightsizing Engine (Rules)    |
|                             |    |  Data Warehouse   |    |                                |
|  Azure Cost Management      +--->+  (BigQuery /      +--->+  Anomaly Detection (ML)        |
|                             |    |   Snowflake)      |    |                                |
|  GCP Billing Export         +--->+                   +--->+  Reservation Optimizer         |
+-----------------------------+    +---------+---------+    +---------------+----------------+
                                             ^                              |
                                             |                              v
+-----------------------------+    +---------+---------+    +--------------------------------+
|  Real-time Metrics          |    |  Normalization    |    |  Action Layer (Remediation)    |
|  (Prometheus / CloudWatch)  +--->+  & Enrichment     |    |                                |
|                             |    |  (ETL Process)    |    |  - Stop/Resize Instances       |
|  Resource Metadata          +--->+                   +--->+  - Update K8s Requests/Limits  |
|  (Tags, CMDB, Git)          |    |                   |    |  - Send Slack/Email Alerts     |
+-----------------------------+    +-------------------+    +--------------------------------+
                                                                            |
                                                                            v
                                                            +--------------------------------+
                                                            |  UI & Reporting                |
                                                            |  (Grafana / Looker)            |
                                                            +--------------------------------+
```

## Core Components

1.  **Ingestion Layer**:
    *   **Billing Connectors**: Scheduled jobs to fetch daily billing files (AWS CUR, Azure CSVs) and stream them to the Data Warehouse.
    *   **Metric Collectors**: Agents or API scrapers that pull CPU, Memory, Disk, and Network utilization metrics into a Time-Series DB (Prometheus).

2.  **Streaming/ETL**:
    *   **Normalization**: A unified schema (Canonical Resource Model) to map provider-specific fields (e.g., `AmazonEC2` vs `Microsoft.Compute`) to a common format.
    *   **Enrichment**: Decorating billing records with business context (Team, App, Owner) from a CMDB or Tagging logic.

3.  **Data Warehouse / Time-Series DB**:
    *   **Columnar Store**: Stores petabytes of historical billing data for fast aggregation (SQL-based).
    *   **TSDB**: Stores high-resolution utilization metrics (e.g., 5-minute intervals) for accurate rightsizing analysis.

4.  **Analytics & ML**:
    *   **Rightsizing Engine**: Compares "Paid" (Billing) vs "Used" (Metrics) to identify waste.
    *   **Anomaly Detection**: Statistical models (e.g., Z-Score, Prophet) to flag spending spikes.

5.  **Orchestration & Automation**:
    *   **Workflow Engine**: Manages dependencies (e.g., "Don't run rightsizing until billing data is ingested").
    *   **Bots**: Stateless functions (Lambda/Cloud Functions) that execute approved remediation actions.

6.  **Action Layer**:
    *   **Remediation**: APIs to interact with cloud providers to modify resources.
    *   **Notification**: Integration with Slack/Teams/PagerDuty for approvals and alerts.

7.  **Security & Audit**:
    *   **IAM**: Least-privilege roles for all components.
    *   **Audit**: Centralized logging of every recommendation generated and action taken.

---

# 4. Data Ingestion & Normalization

## Ingestion Methods

### AWS
*   **Primary**: **Cost & Usage Report (CUR)**. Configure CUR to deliver Parquet files to an S3 bucket hourly/daily. Use AWS Glue to catalog and Athena/Redshift Spectrum to query, or ingest directly into the Data Warehouse.
*   **Secondary**: **Cost Explorer API** for quick, high-level daily aggregates (expensive for granular data).
*   **Metrics**: CloudWatch API (GetMetricData) or CloudWatch Streams to Kinesis -> Firehose -> S3.

### Azure
*   **Primary**: **Cost Management Export**. Schedule daily exports of usage details to an Azure Storage Blob container.
*   **Secondary**: **Cost Details API** for programmatic retrieval.
*   **Inventory**: Azure Resource Graph API for fast, queryable inventory snapshots.

### GCP
*   **Primary**: **Cloud Billing Export**. Native export to BigQuery. This is the gold standard and requires minimal setup.
*   **Metrics**: Cloud Monitoring (Stackdriver) API.

## Normalization Schema
To analyze costs across clouds, we map all data to a **Canonical Resource Model**.

**Example Normalized Record:**
```json
{
  "id": "uuid-550e8400-e29b",
  "cloud_provider": "aws",
  "account_id": "123456789012",
  "resource_id": "i-0abcdef1234567890",
  "service_name": "AmazonEC2",
  "region": "us-east-1",
  "usage_start_time": "2023-10-27T00:00:00Z",
  "usage_end_time": "2023-10-27T01:00:00Z",
  "usage_quantity": 1.0,
  "usage_unit": "Hrs",
  "cost_unblended": 0.096,
  "currency": "USD",
  "tags": {
    "Environment": "Production",
    "Team": "DataScience",
    "Owner": "jane.doe"
  },
  "metadata": {
    "instance_type": "m5.large",
    "os": "Linux"
  }
}
```

## Handling Complexities
*   **Currency Conversion**: All costs are converted to a base currency (e.g., USD) using daily exchange rates at the time of usage.
*   **Cost Allocation**:
    *   **Shared Resources**: Costs for shared K8s clusters or databases are split based on custom logic (e.g., namespace CPU usage).
    *   **Unallocated**: Tagging policies enforce "Unknown" or "Unallocated" buckets for untagged resources to drive accountability.
*   **Credits & Refunds**: These are tracked as separate line items with negative values to allow for "Gross Cost" vs "Net Cost" reporting.
*   **Amortized Costs**: For RIs and Savings Plans, we calculate the *effective* hourly rate (Upfront Fee / Total Hours + Hourly Fee) to show true consumption cost rather than spikes on purchase days.
