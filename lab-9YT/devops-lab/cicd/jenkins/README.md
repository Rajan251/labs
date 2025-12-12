# Jenkins Lab

## 1. Introduction
**Jenkins** is the leading open source automation server.

## 2. Lab Setup

In this lab, we will install Jenkins on Kubernetes and run a simple pipeline.

### Prerequisites
*   Kubernetes cluster.
*   Helm.

### Step 1: Install Jenkins
```bash
helm repo add jenkins https://charts.jenkins.io
helm repo update
helm install jenkins jenkins/jenkins --namespace jenkins --create-namespace
```

### Step 2: Access Jenkins
1.  Get password:
    ```bash
    kubectl exec --namespace jenkins -it svc/jenkins -c jenkins -- /bin/cat /run/secrets/additional/chart-admin-password && echo
    ```
2.  Port forward:
    ```bash
    kubectl port-forward -n jenkins svc/jenkins 8080:8080
    ```
3.  Login at `http://localhost:8080` (User: `admin`).

### Step 3: Create a Pipeline
1.  Click **New Item** -> **Pipeline** -> Name it "Demo".
2.  Scroll to **Pipeline** section.
3.  Paste the content of `Jenkinsfile` (below).
4.  Click **Save**.
5.  Click **Build Now**.

## 3. Sample Jenkinsfile
See `Jenkinsfile` in this directory.
