# Stage 1: Build debian-based image with python and uv as base
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS base

# Install local dependencies for cv2, do cleanup
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg libsm6 libxext6 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Stage 2: Build runtime image
FROM base AS runtime

ARG APP_PORT
WORKDIR /app/

# Copy dependency files
COPY pyproject.toml ./
COPY entrypoint.sh ./
RUN chmod +x ./entrypoint.sh

# Generate uv lock file and install dependencies
RUN uv lock && uv sync --frozen --no-dev

# Copy application code
COPY src ./src

# Expose port
EXPOSE ${APP_PORT}

# Make APP_PORT available at runtime
ENV APP_PORT=${APP_PORT}

ENTRYPOINT ["/app/entrypoint.sh"]