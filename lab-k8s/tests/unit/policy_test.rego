package kubernetes.admission

test_deny_root_container {
    deny["Container 'nginx' must set securityContext.runAsNonRoot to true"] with input as {
        "request": {
            "kind": {"kind": "Pod"},
            "operation": "CREATE",
            "object": {
                "spec": {
                    "containers": [
                        {
                            "name": "nginx",
                            "image": "nginx",
                            "securityContext": {
                                "runAsNonRoot": false
                            }
                        }
                    ]
                }
            }
        }
    }
}

test_allow_non_root_container {
    count(deny) == 0 with input as {
        "request": {
            "kind": {"kind": "Pod"},
            "operation": "CREATE",
            "object": {
                "spec": {
                    "containers": [
                        {
                            "name": "nginx",
                            "image": "nginx",
                            "securityContext": {
                                "runAsNonRoot": true
                            }
                        }
                    ]
                }
            }
        }
    }
}
