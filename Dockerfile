# Use high performance, lightweight Python 3.13 image
FROM python:3.13-slim-bookworm

# Metadata
LABEL maintainer="AutoPR Lab Team"
LABEL version="1.0"
LABEL description="AutoPR Lab Decision Engine"

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml requirements.txt ./

# Install the package and its dependencies
RUN pip install --upgrade pip && \
    pip install .

# Copy the rest of the application
COPY . .

# Ensure scripts directory is in PATH
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Define the default entrypoint
ENTRYPOINT ["python", "scripts/decision_engine.py"]
