# Unit Tests
# Test individual components (e.g., OPA policies)

package kubernetes.admission

test_deny_privileged_pods {
    deny["Privileged pods are not allowed"] with input.request.object.spec.containers as [{"securityContext": {"privileged": true}}]
}
