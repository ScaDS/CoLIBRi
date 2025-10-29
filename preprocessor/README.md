# CoLIBRi Preprocessor

This directory contains the containerized code for the _CoLIBRi_ preprocessor microservice.

## Project Tools

The following tools are used:
* [Python 3.10](https://www.python.org/downloads/release/python-3100/)
* [OpenCV](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)
* [Scikit-Learn](https://scikit-learn.org/stable/)
* [Scikit-Image](https://scikit-image.org/)
* [Rapidfuzz](https://github.com/rapidfuzz/RapidFuzz)
* [Flask](https://flask.palletsprojects.com/en/stable/)
* [PaddleOCR](https://www.paddleocr.ai/main/en/quick_start.html)
* [pdf2image](https://pypi.org/project/pdf2image/)
* [Tesseract](https://pypi.org/project/pytesseract/)
* [nnunetv2](https://pypi.org/project/nnunetv2/)
* [clip](https://github.com/openai/CLIP.git)
* [gunicorn](https://gunicorn.org/)

## Application Setup

* `Dockerfile.cu[verion]`: Dockerfile(s) to build the Docker image for the Preprocessor with specified CUDA version (see below)
* `entrypoint.sh`: Starts gunicorn server and preprocessor app in the Docker Image
* `pyproject.toml`: Python configuration file for used dependencies and tools

## GPU and CUDA

An NVIDIA GPU is required to run this preprocessing service.  
The GPU should support at least CUDA 6.0 compute capabilities (see https://developer.nvidia.com/cuda-legacy-gpus). 
We recommend at least 10GB VRAM.

Ensure that the appropriate **NVIDIA GPU driver** and **NVIDIA Container Toolkit** are installed on your system, like desribed [here](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).

Select the appropriate Dockerfile for your NVIDIA GPU, which needs to be specified in the project's `.env` file.

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

## Application Structure

![application architecture](resources/architecture_overview.png)

The endpoints for the Flask application are defined in `src/flask/backend.py`.  
All logic is handled by `src/flask/preprocess.py`, which imports functions from 
* `src/flask/converter/`: contains the standardization, table extraction and part segmentation steps
  * `consts.py`: important constants that work for our dataset.  
     If you want to try this tool on you own dataset, changing some of these might be important (especially LINE_WIDTH).
  * `image_rotation.py`: tools for checking if image is rotated and correcting it
  * `image_std.py`: tools for converting bytestrings to cv2 images, deskewing, resizing / padding images to 2048x2048
  * `shape_extract.py`: tools for removing dimensioning, arrows and lines as well as applying the UNet segmentation
  * `table_extract.py`: fire propagation algorithm for table detection
  * `thumb_gen.py`: deprecated, but can be used to generate a thumbnail for a drawing using either a representative view or a 3d render if it exists
* `src/flask/ocr/`: contains the OCR and information extraction steps
  * `paddle_ocr_engine.py`: initialize and apply OCR model to a drawing
  * `context_merger.py`: from the OCR results, merge text within a cell, or close to each other using DBSCAN
  * `extraction.py`: from the resulting text clusters, extract text features such as material, norms, surfaces etc.
  * `vectorizer.py`: convert those extracted features to a searchable vector representation
* `src/flask/shapes/`: contains the embedding generation step
  * `vectorizer.py`: applies CLIP embedding to all views, selects the most representative one
* Title extraction through the VLM is handled in conv-search microservice

## Run the Application

For the preprocessor to work in the intended way, the database service need to be up and running.  
To make sure, best start the whole docker compose stack like described in the project's [`README`](../README.md#docker-compose-setup).

### Run microservice via Docker Compose as stand-alone

**Switch to the parent directory where the file `docker-compose.yml` is located.**

To build and run the frontend only:
* Build the service
  * `docker compose build preprocessor-app`
* Start the frontend without other dependent services
  * `docker compose up -d --no-deps preprocessor-app`
* Inspect the running containers
  * `docker compose ps -a`
* See the logs for any errors
  * `docker compose logs -f preprocessor-app`
* Stop all running containers, remove the images and volumes:
  * `docker compose down --rmi "all" -v`
