package kubernetes.admission

deny[msg] {
  input.request.kind.kind == "Pod"
  input.request.operation == "CREATE"
  container := input.request.object.spec.containers[_]
  not container.securityContext.runAsNonRoot
  msg := sprintf("Container '%v' must set securityContext.runAsNonRoot to true", [container.name])
}
