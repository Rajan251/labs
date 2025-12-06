# High-Scale Video Streaming Platform

A production-grade video streaming platform (MVP) built with modern DevOps practices.

## 🚀 Tech Stack

-   **Frontend**: React, Vite, HLS.js
-   **Backend**: Node.js, Express, TypeScript
-   **Worker**: Python, FFmpeg
-   **Database**: PostgreSQL, Redis
-   **Storage**: MinIO (S3 Compatible)
-   **Messaging**: RabbitMQ
-   **Infrastructure**: Docker, Kubernetes, Helm, Terraform
-   **Monitoring**: Prometheus, Grafana
-   **CI/CD**: GitHub Actions

## 📂 Project Structure

```text
.
├── api/                 # Video Metadata & Upload API
├── worker/              # Transcoding Worker (FFmpeg)
├── web/                 # React Frontend Client
├── k8s/                 # Kubernetes Manifests & Helm Charts
│   ├── charts/          # Application Helm Chart
│   ├── monitoring/      # Prometheus/Grafana Configs
│   ├── security/        # Network Policies
│   └── cost/            # Resource Quotas
├── terraform/           # AWS Infrastructure as Code
├── scripts/             # Automation Scripts
├── .github/workflows/   # CI/CD Pipelines
├── docker-compose.yml   # Local Dev Stack
├── Makefile             # Automation Shortcuts
└── README.md            # This file
```

## ⚡ Quick Start

1.  **Prerequisites**: Docker, Node.js, Make.
2.  **Setup**:
    ```bash
    make setup
    ```
3.  **Start Local Environment**:
    ```bash
    make up
    ```
4.  **Access Services**:
    -   **Web UI**: http://localhost:5173 (or via Nginx on port 80)
    -   **API**: http://localhost:3000
    -   **MinIO**: http://localhost:9001 (User/Pass: minioadmin)

## 🔄 System Flow

1.  **Upload**: User selects video -> API generates Presigned URL -> Browser uploads to MinIO.
2.  **Notify**: Browser notifies API "Upload Complete" -> API pushes job to RabbitMQ.
3.  **Process**: Worker consumes job -> Downloads video -> Transcodes to HLS -> Uploads segments to MinIO.
4.  **Stream**: User plays video -> Player requests `.m3u8` -> MinIO serves segments.

## 🛠 DevOps Features

-   **CI/CD**: Automated builds and security scans on push.
-   **Monitoring**: Metrics for API latency and Worker throughput.
-   **Security**: Network policies restrict pod-to-pod communication.
-   **Cost**: Resource limits prevent runaway costs.
