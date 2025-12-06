FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Create a non-root user for security
RUN useradd -m celeryuser
USER celeryuser

# Command will be overridden by docker-compose
CMD ["celery", "-A", "app.celery_app", "worker", "--loglevel=info"]
