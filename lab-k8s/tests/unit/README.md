# Unit Tests

This directory contains unit tests for Kubernetes policies using [Open Policy Agent (OPA)](https://www.openpolicyagent.org/).

## Policy Test

The `policy.rego` file defines a policy that denies Pods running as root. The `policy_test.rego` file contains unit tests for this policy.

### Prerequisites
- [OPA](https://www.openpolicyagent.org/docs/latest/#running-opa) installed

### Usage

Run the tests using the `opa test` command:

```bash
opa test . -v
```

### What it tests
- **Deny**: Ensures that a Pod with `runAsNonRoot: false` (or missing) is denied.
- **Allow**: Ensures that a Pod with `runAsNonRoot: true` is allowed.
