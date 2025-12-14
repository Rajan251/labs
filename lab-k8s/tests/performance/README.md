# Performance Tests

This directory contains performance tests using [k6](https://k6.io/).

## Load Test

The `load-test.js` script simulates a load test scenario with ramping up and down of virtual users.

### Prerequisites
- [k6](https://k6.io/docs/getting-started/installation/) installed
- A running service to test (update the URL in the script)

### Usage

1. Update the URL in `load-test.js` to point to your target service (e.g., a NodePort or Ingress URL).
2. Run the test:

```bash
k6 run load-test.js
```

### Configuration
- **Stages**: Configured to ramp up to 20 users over 30s, hold for 1m, and ramp down.
- **Thresholds**: Fails if 95% of requests take longer than 500ms.
