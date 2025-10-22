# Stage 1: Build debian-based image with python and uv as base
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS base

# Install local dependencies do cleanup
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Stage 2: Build runtime image
FROM base AS runtime

ENV PYTHONUNBUFFERED=1
ARG CS_PORT
WORKDIR /app/

# Copy dependency files
COPY pyproject.toml ./
COPY entrypoint.sh ./
COPY .env ./
RUN chmod +x ./entrypoint.sh

# Generate uv lock file and install dependencies
RUN uv lock && uv sync --frozen --no-dev

# Copy application code
COPY src ./src

# Expose port
EXPOSE ${CS_PORT}

# Make CS_PORT available at runtime
ENV CS_PORT=${CS_PORT}

# run the gunicorn server at entry
ENTRYPOINT ["/app/entrypoint.sh"]