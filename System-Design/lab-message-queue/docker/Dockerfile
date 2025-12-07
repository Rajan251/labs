FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir pyyaml

# Copy application code
COPY broker/ ./broker/
COPY client/ ./client/
COPY coordinator/ ./coordinator/
COPY protocol/ ./protocol/
COPY examples/ ./examples/
COPY config/ ./config/

# Create data directory
RUN mkdir -p /data

# Expose broker port
EXPOSE 9092

# Default command (can be overridden)
CMD ["python", "-m", "broker.broker", "1", "9092"]
