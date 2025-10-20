# CoLIBRi Preprocessor

## GPU and CUDA

An NVIDIA GPU is required to run this preprocessing service.

Ensure that the appropriate **NVIDIA GPU driver** and **NVIDIA Container Toolkit** are installed on your system, like desribed [here](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).

Select the appropriate Dockerfile for your available NVIDIA GPU, which needs to be specified in the project's [docker-compose.yml](https://github.com/ScaDS/CoLIBRi/blob/main/docker-compose.yml#L59).

### Dockerfile.cu118
* Built with CUDA 11.8 and cuDNN 8.9
* Covers GPU architectures according to CUDA compute capabilities:
  * 6.0, 6.1, 7.0 - see https://developer.nvidia.com/cuda-legacy-gpus
  * 7.5, 8.0, 8.6 - see https://developer.nvidia.com/cuda-gpus

### Dockerfile.cu129
* Built with CUDA 12.9 and cuDNN 9.9
* Covers GPU architectures according to CUDA compute capabilities:
  * 12.0 - see https://developer.nvidia.com/cuda-gpus
