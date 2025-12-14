# CI/CD Pipelines

## Overview
We support both **Jenkins** (traditional) and **Tekton** (cloud-native) for CI/CD.

## Jenkins Pipeline
- **Type**: Scripted/Declarative Groovy pipelines.
- **Use Case**: Legacy applications, complex logic, extensive plugin ecosystem.
- **Execution**: Runs on Jenkins agents (pods) in the cluster.

## Tekton Pipeline
- **Type**: Kubernetes Custom Resources (Task, Pipeline, PipelineRun).
- **Use Case**: Cloud-native, lightweight, serverless execution.
- **Components**:
  - **Task**: A sequence of steps (containers) to execute.
  - **Pipeline**: A graph of Tasks.
  - **PipelineRun**: An execution of a Pipeline.
