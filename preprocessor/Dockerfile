# Stage 1: Build miniconda image as base
FROM continuumio/miniconda3:latest AS base

# Install local dependencies for cv2, do cleanup
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg libsm6 libxext6 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Stage 2: Build runtime image
FROM base AS runtime

ARG PP_PORT
ARG GPU_ID
WORKDIR /app/

# Copy files
COPY preprocessor-conda-env.yml requirements.txt entrypoint.sh ./
RUN chmod +x ./entrypoint.sh
COPY src ./src

# Create the environment with conda
# TODO: RUN conda config --prepend envs_dirs "/opt/conda-envs"

# Expose PP_PORT to access from outside
EXPOSE ${PP_PORT}

# Make PP_PORT available at runtime
ENV PP_PORT=${PP_PORT}

# Set env vars for paddleocr
ENV CUDA_VISIBLE_DEVICES=${GPU_ID}
ENV LD_LIBRARY_PATH=/opt/conda-envs/preprocessor-env/lib/

# Run the gunicorn server at entry
ENTRYPOINT ["/app/entrypoint.sh"]
