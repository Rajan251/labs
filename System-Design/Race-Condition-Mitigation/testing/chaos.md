# Advanced Testing Strategies

## 1. Chaos Testing (Network Partitions)
To ensure the distributed locking and circuit breakers work under failure, we simulate network issues.

### Tools: Chaos Mesh / Pumba

### Scenarios
1.  **Redis Partition**: Cut network between Service and Redis.
    - *Expected Behavior*: Services should fail fast (Circuit Breaker) or retry (if configured). Locks should eventually expire to prevent deadlocks.
2.  **Database Latency**: Introduce 5s latency to DB.
    - *Expected Behavior*: Optimistic locking might see more retries. Pessimistic locking will hold connections longer (connection pool exhaustion risk).

### Implementation (Chaos Mesh YAML)
```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: redis-delay
spec:
  action: delay
  mode: one
  selector:
    namespaces:
      - default
    labelSelectors:
      "app": "redis"
  delay:
    latency: "500ms"
    jitter: "100ms"
```

## 2. Property-Based Testing (Hypothesis)
Instead of fixed examples, we generate random data to find edge cases.

### Python Example (Hypothesis)
```python
from hypothesis import given, strategies as st
from payment.models import Wallet

@given(st.integers(min_value=1, max_value=100), st.integers(min_value=1, max_value=100))
def test_transfer_invariant(amount1, amount2):
    # Invariant: Total system balance remains constant
    initial_total = wallet1.balance + wallet2.balance
    transfer(wallet1, wallet2, 10)
    final_total = wallet1.balance + wallet2.balance
    assert initial_total == final_total
```
