# Twitter-like Microblogging Platform

A scalable microblogging platform implementation using Python (FastAPI), Redis, and PostgreSQL.

## System Architecture

The system uses a **Hybrid Fan-out Architecture**:
-   **Fan-out on Write**: For normal users, tweets are pushed to followers' timelines (Redis).
-   **Fan-out on Read**: For celebrities, tweets are pulled and merged at read time.

## Directory Structure

```
.
├── app/                    # Application Source Code
│   ├── models/             # Database Models
│   ├── routers/            # API Endpoints
│   ├── schemas/            # Pydantic Schemas
│   ├── services/           # Business Logic
│   └── workers/            # Background Workers (Celery)
├── infra/                  # Infrastructure Configuration
│   ├── k8s/                # Kubernetes Manifests
│   └── docker-compose.yml  # Local Development
└── tests/                  # Unit & Integration Tests
```

## Getting Started

### Prerequisites
-   Docker & Docker Compose

### Running Locally
```bash
docker-compose up --build
```
Access the API documentation at `http://localhost:8000/docs`.

### Running Tests
```bash
pip install -r requirements.txt
pip install pytest httpx
pytest tests/
```
