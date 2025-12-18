# Capacity Planning for Linux Infrastructure

**Level:** Expert / Infrastructure Architect
**Focus:** Proactive resource planning and cost optimization.

---

## 1. Data Collection Framework

### 1.1 Utilization Metrics
*   **CPU**: Average, peak, p95 over time.
*   **Memory**: Used, cached, swap activity.
*   **Disk**: Space used, IOPS, throughput.
*   **Network**: Bandwidth in/out, packet rates.

### 1.2 Performance Metrics
*   **Response Time**: p50, p95, p99 latency.
*   **Throughput**: Requests per second.
*   **Error Rates**: 4xx, 5xx errors.

### 1.3 Business Metrics
*   **User Growth**: Monthly active users (MAU).
*   **Transaction Volume**: Orders, API calls.
*   **Data Growth**: Database size, log volume.

### 1.4 Cost Metrics
*   **Infrastructure**: Server, cloud, network costs.
*   **Licensing**: Database, monitoring tools.
*   **Support**: Vendor contracts.

---

## 2. Analysis Techniques

### 2.1 Trend Analysis
*   **Linear Regression**: Fit line to historical data.
*   **Example**: CPU usage growing 5% per month.
*   **Projection**: In 6 months, will hit 100% capacity.

### 2.2 Seasonality Detection
*   **Weekly**: Higher load on weekdays.
*   **Monthly**: End-of-month batch jobs.
*   **Yearly**: Black Friday, tax season.

### 2.3 Event Correlation
*   **Marketing Campaigns**: Traffic spike after email blast.
*   **Product Launches**: New feature drives usage.

---

## 3. Capacity Models

### 3.1 Linear Scaling
*   **Assumption**: Resources scale proportionally.
*   **Example**: 1000 users = 1 server. 2000 users = 2 servers.

### 3.2 Step Function
*   **Reality**: Can't buy 0.5 servers.
*   **Example**: At 1500 users, must buy 2nd server (50% idle initially).

### 3.3 Non-linear
*   **Database**: Performance degrades exponentially with size.
*   **Example**: 1GB DB = 10ms query. 10GB DB = 100ms query (not 100ms).

### 3.4 Constraint-based
*   **Identify Bottleneck**: Is it CPU, memory, disk, or network?
*   **Example**: Adding CPU won't help if disk is the bottleneck.

---

## 4. Forecasting Methods

### 4.1 Business-driven
*   **Input**: Company expects 50% user growth next year.
*   **Output**: Need 50% more infrastructure.

### 4.2 Usage-driven
*   **Input**: Historical trend shows 5% monthly growth.
*   **Output**: Extrapolate forward.

### 4.3 Event-driven
*   **Input**: Launching in new country next quarter.
*   **Output**: Estimate impact based on similar past events.

### 4.4 Hybrid
*   Combine all three methods. Use highest estimate for safety.

---

## 5. Recommendation Types

### 5.1 Immediate (0-1 Month)
*   **Trigger**: Utilization >80%.
*   **Action**: Add capacity NOW.

### 5.2 Short-term (3-6 Months)
*   **Trigger**: Trend shows 80% in 3 months.
*   **Action**: Budget and procure.

### 5.3 Long-term (1-3 Years)
*   **Strategic**: Plan for 3x growth.
*   **Action**: Architecture changes, vendor negotiations.

---

## 6. Presentation to Stakeholders

### 6.1 Executive Summary
*   **Current State**: 70% CPU utilization.
*   **Forecast**: Will hit 100% in 4 months.
*   **Recommendation**: Add 2 servers ($10k).
*   **Risk of Inaction**: Service outages, lost revenue.

### 6.2 Technical Details (Appendix)
*   Graphs, formulas, assumptions.

---

## 7. Industry-Specific Patterns

### 7.1 E-commerce
*   **Seasonality**: Black Friday = 10x normal traffic.
*   **Strategy**: Auto-scaling, pre-provision for known events.

### 7.2 SaaS
*   **Growth**: Exponential user growth in early stages.
*   **Strategy**: Cloud-native, horizontal scaling.

### 7.3 Data Analytics
*   **Pattern**: Data grows faster than compute needs.
*   **Strategy**: Tiered storage (hot/cold), data lifecycle policies.
