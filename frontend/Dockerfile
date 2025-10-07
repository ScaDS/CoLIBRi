# Stage 1: Build miniconda image as base
FROM continuumio/miniconda3:latest AS base

# Install local dependencies for cv2, do cleanup
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg libsm6 libxext6 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Stage 2: Build runtime image
FROM base AS runtime

ARG APP_PORT
WORKDIR /app/

# Copy files
COPY frontend-conda-env.yml entrypoint.sh ./
RUN chmod +x ./entrypoint.sh
COPY src ./src

# Create or update the conda environment
RUN conda env create -f /app/frontend-conda-env.yml

# expose port 5001 to access it from outside of the container
EXPOSE ${APP_PORT}

# Make APP_PORT available at runtime
ENV APP_PORT=${APP_PORT}

# run with conda environment
ENTRYPOINT ["/app/entrypoint.sh"]