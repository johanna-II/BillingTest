FROM python:3.12-slim

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

RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python3 - --version $POETRY_VERSION
ENV PATH="/opt/poetry/bin:$PATH"

# Copy dependency files
COPY poetry.lock pyproject.toml ./

# Install dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root

# Copy application code
# Note: .dockerignore file ensures sensitive data is not copied
# This includes git files, test files, IDE configs, and other non-runtime files
COPY --chown=appuser:appuser . .

# Install project in editable mode
RUN poetry install --no-interaction --no-ansi

# Switch to non-root user
USER appuser
