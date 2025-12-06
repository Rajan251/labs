FROM rabbitmq:3.12-management-alpine

# Enable default user and password (optional, can be overridden by env vars)
ENV RABBITMQ_DEFAULT_USER=guest
ENV RABBITMQ_DEFAULT_PASS=guest

# Enable management plugin (already enabled in this image tag, but good practice to be explicit if using base image)
# RUN rabbitmq-plugins enable rabbitmq_management
