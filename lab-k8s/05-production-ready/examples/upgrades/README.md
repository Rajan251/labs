# Upgrade Strategies

## Blue/Green Deployment
1. Deploy version v2 (Green) alongside v1 (Blue).
2. Run tests on Green.
3. Switch Service selector to Green.
4. Delete Blue.

## Canary Deployment
1. Deploy a small percentage of v2 pods.
2. Monitor metrics (errors, latency).
3. Gradually increase v2 percentage.
