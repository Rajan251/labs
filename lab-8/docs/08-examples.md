# 17. Examples & Sample Outputs

## Normalized Billing Record
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "cloud": "aws",
  "account_id": "123456789012",
  "service": "AmazonEC2",
  "resource_id": "i-0abcdef1234567890",
  "usage_start": "2023-10-27T10:00:00Z",
  "usage_end": "2023-10-27T11:00:00Z",
  "cost": 0.096,
  "currency": "USD",
  "tags": {
    "Owner": "team-data",
    "Environment": "prod"
  }
}
```

## Rightsizing Recommendation
```json
{
  "resource_id": "i-0abcdef1234567890",
  "current_type": "m5.2xlarge",
  "recommended_type": "m5.large",
  "reason": "CPU utilization < 10% for 30 days",
  "savings_monthly": 145.20,
  "confidence": "HIGH",
  "action": "Resize"
}
```

## Reservation Recommendation Table
| Region | Family | Term | Type | Recommended Qty | Upfront Cost | Monthly Savings |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| us-east-1 | m5 | 1yr | All Upfront | 12 | $15,000 | $1,200 |
| eu-west-1 | r5 | 3yr | No Upfront | 5 | $0 | $450 |

## Alert Payload
```json
{
  "alert": "Spend Spike Detected",
  "service": "AmazonS3",
  "account": "prod-assets",
  "increase_pct": 250,
  "previous_day_cost": 45.00,
  "current_day_cost": 157.50,
  "link": "https://dashboard.internal/alerts/999"
}
```
