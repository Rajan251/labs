# Branching Strategies & CI/CD

## Overview
A robust CI/CD pipeline mirrors the branching strategy used by the development team.

## Strategies

### 1. GitFlow
- **Branches**: `main`, `develop`, `feature/*`, `release/*`, `hotfix/*`.
- **CI/CD Mapping**:
    - `feature/*`: Run tests and linting. No deployment.
    - `develop`: Deploy to **Dev** environment.
    - `release/*`: Deploy to **Staging** environment.
    - `main`: Deploy to **Production** environment (often with manual approval).

### 2. Trunk-Based Development
- **Branches**: `main` (trunk), short-lived feature branches.
- **CI/CD Mapping**:
    - `feature`: Run tests.
    - `main`: Deploy to **Dev** -> **Staging** -> **Production** in a single pipeline execution, promoting artifacts if tests pass.

## Multibranch Pipelines
Tools like Jenkins and Tekton support "Multibranch" pipelines which automatically discover branches and create pipelines for them.
- **Jenkins**: Uses `Jenkinsfile` in each branch.
- **Tekton**: Uses Triggers to detect push events and filter by branch name.
