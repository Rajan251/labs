# Real-World Deployment Use Cases

## 1. FinTech / Banking
- **Strategy**: **Blue-Green Deployment**
- **Why**: Zero downtime is critical. Instant rollback is mandatory for compliance.
- **Example**: A core banking ledger update. Deploy v2 to Green, run extensive compliance tests, then switch traffic. If any error occurs, switch back to Blue immediately.

## 2. E-Commerce (Black Friday)
- **Strategy**: **Canary Deployment**
- **Why**: High risk of load-related issues.
- **Example**: Rolling out a new checkout flow. Route 1% of traffic to v2. Monitor conversion rates and errors. If stable, increase to 10%, then 50%, then 100%.

## 3. SaaS Startup
- **Strategy**: **CI/CD + Rolling Update**
- **Why**: High velocity, frequent small changes.
- **Example**: A team pushing 10+ updates a day. GitHub Actions builds the image, pushes to registry, and updates Kubernetes Deployment. K8s handles the rolling update automatically.

## 4. AI/ML Model Serving
- **Strategy**: **Shadow Deployment**
- **Why**: Need to verify model accuracy on real data without affecting users.
- **Example**: Deploying a new recommendation engine. Mirror user requests to the new model. Compare its recommendations with the current model. Promote only if accuracy improves.

## 5. Enterprise Legacy App
- **Strategy**: **Recreate Deployment**
- **Why**: Application is not cloud-native and cannot handle multiple versions accessing the database simultaneously.
- **Example**: Updating an old ERP system. Schedule a maintenance window. Stop the old version. Run DB migrations. Start the new version.
