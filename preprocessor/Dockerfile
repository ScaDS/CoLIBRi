# Stage 1: Build NVIDIA CUDA on Ubuntu with Python and uv as base image
FROM nvidia/cuda:12.9.0-cudnn-runtime-ubuntu22.04 AS base

# Install local dependencies, do cleanup
RUN apt-get update && apt-get install -y \
    python3.11 python3.11-dev python3-pip \
    git curl \
    ffmpeg libsm6 libxext6  \
    tesseract-ocr poppler-utils \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set Python 3.11 as default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
# Make uv install packages into the systems default Python 3.11
ENV UV_SYSTEM_PYTHON=1

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
RUN uv pip install --system -e ".[dev]"

# Expose PP_PORT to access from outside
EXPOSE ${PP_PORT}

# Make PP_PORT available at runtime
ENV PP_PORT=${PP_PORT}

# Set env vars for paddleocr
ENV CUDA_VISIBLE_DEVICES=${GPU_ID}

# Run the gunicorn server at entry
ENTRYPOINT ["/app/entrypoint.sh"]
