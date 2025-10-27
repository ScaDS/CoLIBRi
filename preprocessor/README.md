# CoLIBRi Preprocessor

## GPU and CUDA

An NVIDIA GPU is required to run this preprocessing service. The GPU should support at least CUDA 6.0 compute capabilities (see https://developer.nvidia.com/cuda-legacy-gpus). We recommend at least 10GB VRAM.

Ensure that the appropriate **NVIDIA GPU driver** and **NVIDIA Container Toolkit** are installed on your system, like desribed [here](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).

Select the appropriate Dockerfile for your available NVIDIA GPU, which needs to be specified in the project's [docker-compose.yml](https://github.com/ScaDS/CoLIBRi/blob/main/docker-compose.yml#L58) via the global environment file `.env`.

### Dockerfile.cu118
* For CUDA 11.8 with cuDNN 8.9
* Built based on [paddlepaddle Docker image](https://hub.docker.com/r/paddlepaddle/paddle) tagged "3.2.0-gpu-cuda11.8-cudnn8.9"
* Covers GPU architectures according to CUDA compute capabilities:
  * 6.0, 6.1, 7.0 - see https://developer.nvidia.com/cuda-legacy-gpus
  * 7.5, 8.0, 8.6 - see https://developer.nvidia.com/cuda-gpus

### Dockerfile.cu129
* For CUDA 12.9 with cuDNN 9.9
* Built based on [paddlepaddle Docker image](https://hub.docker.com/r/paddlepaddle/paddle) tagged "3.2.0-gpu-cuda12.9-cudnn9.9"
* Covers GPU architectures according to CUDA compute capabilities:
  * 12.0 - see https://developer.nvidia.com/cuda-gpus
