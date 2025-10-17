# Stage 1: Build NVIDIA CUDA on Ubuntu with Python and uv as base image
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS base

# Install local dependencies, do cleanup
RUN apt-get update && apt-get install -y \
    git curl \
    ffmpeg libsm6 libxext6  \
    tesseract-ocr poppler-utils \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Stage 2: Build runtime image
FROM base AS runtime

ARG PP_PORT
ARG GPU_ID
WORKDIR /app/

# Copy dependency files
COPY pyproject.toml ./
COPY entrypoint.sh ./
RUN chmod +x ./entrypoint.sh
# Copy application code
COPY src ./src

# Install dependencies
RUN uv lock && uv sync --frozen --no-dev

# Expose PP_PORT to access from outside
EXPOSE ${PP_PORT}

# Make PP_PORT available at runtime
ENV PP_PORT=${PP_PORT}

# Env vars for CUDA
ENV CUDA_VISIBLE_DEVICES=${GPU_ID}
ENV LD_LIBRARY_PATH=/app/.venv/lib/python3.11/site-packages/nvidia/cudnn/lib

# Run the gunicorn server at entry
ENTRYPOINT ["/app/entrypoint.sh"]
