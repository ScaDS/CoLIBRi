# CoLIBRi

> This prototype is work in progress and provided “as is,” without warranty of any kind.
The authors accept no responsibility for any issues, errors, or consequences resulting from its use.

We present CoLIBRi (Conversational Image-Based Retrieval), an end-to-end system for multi-modal retrieval and conversational search on image-based manufacturing drawings. The system combines fine-tuned optical character recognition for textual attributes (e.g., dimensions, tolerances, materials), deep-learning–based segmentation for part geometries, pre-trained visual embeddings for geometric representation, and a vision–language model to extract structured metadata such as part names from title blocks. Engineers can either upload a drawing to trigger multi-modal retrieval or use a conversational interface powered by a large language model to issue natural-language queries and explore retrieved parts. By linking retrieved manufacturing drawings with enterprise resource planning data on machine usage and production times, CoLIBRi enables faster quotation preparation while reducing dependence on individual expertise. Developed in close collaboration with a medium-sized manufacturing company, the system demonstrates how multi-modal AI and conversational interfaces can provide practically relevant support for industrial engineering workflows. To foster reproducibility and future research, we release the CoLIBRi model weights and source code under an open license.

## Overview

This repository provides the application code for _CoLIBRi_ as well as sample data and other tools,
e.g., for reproducing benchmarks.  

_CoLIBRi_ is based on a containerized microservice architecture with the following components:

* **Frontend Service**
  * Dash App, providing an interface to interact with the application.
  * Please see the according [README](frontend/README.md) for more details.

* **Preprocessor Service**
  * Microservice for generating search vectors from input mechanical drawings using OCR, shape segmentation and CLIP embedding.
  * Please see the according [README](preprocessor/README.md) for more details.

* **Conversational Search**
  * Microservice for LLM / VLM backend calls, used for search engine and the conversational interface.
  * Please see the according [README](conv-search/README.md) for more details.

* **Database Service**
  * Microservice to persist and access the preprocessed data for the technical drawings.
  * Please see the according [README](database/README.md) for more details.

For reproducing benchmarks and plots, we provide:

* **Tools**
  * Tools to reproduce benchmarks, tables and visualizations from our paper.
  * Please see the according [README](tools/README.md) for more details.

* **Example Data**
  * We publish 9 drawings of 4 unique machining parts created by our industrie partner [CPT Präzisionstechnik GMBH](https://cptcnc.de).
  * Please see the according [README](example_data/README.md) for more details.

## Application Setup

The application and its microservices are managed within a [Docker Compose](https://docs.docker.com/compose/) stack,
defined by the file [docker-compose.yml](docker-compose.yml).

### Basic System Requirements

* The application was built on and tested for linux/amd64 (x86-64) architectures
* Docker with Docker Compose available
* NVIDIA GPU which supports at least CUDA 11.8, with at least 10GB of VRAM
* Recent installation of NVIDIA GPU driver and NVIDIA Container Toolkit
* The services use the following ports: 5201, 6201, 7201, 7211, 9201

### Docker Compose Setup

#### For configuration, two environment files are used:

* `.env`
  * Global configuration of _CoLIBRi_
  * See [`.env.sample`](.env.sample) for details
* `conv-search/.env`
  * Configuration of models and LLM backend for conversational search
  * See [`conv-search/.env.sample`](conv-search/.env.sample) for details

#### To set up the application with Docker Compose:

* Create the two environment files `.env` and `conv-search/.env` (see above)
* Build the services via 
  * `docker compose build`
* Start the services via 
  * `docker compose up -d`
* Inspect the running containers via 
  * `docker compose ps -a`
* Inspect the logs of a specific service via 
  * `docker compose logs -f frontend-app`
* The frontend service is available at `http://localhost:5201`
* Stop all running containers, fully remove according images and volumes via 
  * `docker compose down --rmi "all" -v`
