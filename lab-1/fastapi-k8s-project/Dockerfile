# =============================================================================
# MULTI-STAGE DOCKERFILE FOR FASTAPI APPLICATION
# =============================================================================
# This Dockerfile uses multi-stage builds to create a minimal production image
# 
# Stage 1 (builder): Install dependencies and compile Python packages
# Stage 2 (runtime): Copy only necessary files for a smaller final image
#
# Benefits:
# - Smaller image size (only runtime dependencies)
# - Better security (fewer tools in production)
# - Faster deployment (smaller images transfer faster)
# =============================================================================

# -----------------------------------------------------------------------------
# STAGE 1: Builder
# -----------------------------------------------------------------------------
# This stage installs all dependencies including build tools
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies required for building Python packages
# - gcc, g++: Compilers for C extensions
# - libpq-dev: PostgreSQL client library
# - curl: For health checks during build
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
# --no-cache-dir: Don't cache packages (reduces image size)
# --user: Install to user directory (easier to copy to next stage)
RUN pip install --no-cache-dir --user -r requirements.txt

# -----------------------------------------------------------------------------
# STAGE 2: Runtime
# -----------------------------------------------------------------------------
# This stage creates the final minimal image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install only runtime system dependencies
# - libpq5: PostgreSQL client library (runtime only, not dev)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder stage
# This copies only the installed packages, not the build tools
COPY --from=builder /root/.local /root/.local

# Update PATH to include user-installed packages
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY ./app /app/app

# Create non-root user for security
# Running as non-root is a security best practice
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port 8000
# This is the port uvicorn will listen on
EXPOSE 8000

# Health check
# Kubernetes will use this to determine if the container is healthy
# --interval: How often to check (30s)
# --timeout: How long to wait for response (10s)
# --start-period: Grace period before starting checks (40s)
# --retries: How many failures before marking unhealthy (3)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run the application
# Using uvicorn with the following settings:
# - host 0.0.0.0: Listen on all network interfaces
# - port 8000: Application port
# - workers: Number of worker processes (set via environment variable)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
