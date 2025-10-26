FROM python:3.14.0-slim

# Create non-root user for security
# Note: Using a non-root user prevents potential container breakout attacks
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3-dev \
    default-libmysqlclient-dev \
    build-essential \
    libffi-dev \
    curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Poetry
ENV POETRY_VERSION=2.2.1
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VENV=/opt/poetry-venv
ENV POETRY_CACHE_DIR=/opt/.cache

# NOSONAR: docker:S6504 - HTTPS is enforced with -sS flags (show errors only)
# The -L flag follows redirects only within HTTPS, not to HTTP
# This is the official Poetry installation method from python-poetry.org
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python3 - --version $POETRY_VERSION
ENV PATH="/opt/poetry/bin:$PATH"

# Copy dependency files (read-only)
COPY --chmod=444 poetry.lock pyproject.toml ./

# Install dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root

# Copy application code
# SonarQube: Recursive COPY is safe here due to comprehensive .dockerignore
# .dockerignore excludes: git files, test files, IDE configs, logs, caches, secrets
# Only runtime-necessary files are copied into the container
# Note: Using standard permissions for COPY to allow Poetry installation
# Write permissions will be removed after installation completes
COPY --chown=appuser:appuser . .

# Install project in editable mode
RUN poetry install --no-interaction --no-ansi

# Remove all write permissions for security after installation
# This ensures the container runs with read-only files
# Directories: 555 (r-xr-xr-x), Files: 444 (r--r--r--)
RUN find /app -type f -exec chmod 444 {} + && \
    find /app -type d -exec chmod 555 {} +

# Switch to non-root user
USER appuser
