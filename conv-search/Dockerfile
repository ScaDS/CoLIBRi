# Stage 1: Build debian-based image with python and uv as runtime
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS runtime

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