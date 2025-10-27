# CoLIBRi

Supporting quotation through multi-modal retrieval and conversational search on technical drawings. 

> This prototype is work in progress and provided “as is,” without warranty of any kind.
The authors accept no responsibility for any issues, errors, or consequences resulting from its use.

## Overview

This repository provides the application code for _CoLIBRi_ as well as sample data and other tools,
e.g., for reproducing benchmarks.  

_CoLIBRi_ is based on a containerized microservice architecture with the following components:

### Frontend Service

**ToDo**

Please see the according [README](https://github.com/ScaDS/CoLIBRi/blob/main/frontend/README.md) for more details.

### Preprocessor Service

**ToDo**

Please see the according [README](https://github.com/ScaDS/CoLIBRi/blob/main/preprocessor/README.md) for more details.

### Conversational Search

**ToDo**

Please see the according [README](https://github.com/ScaDS/CoLIBRi/blob/main/conv-search/README.md) for more details.

### Database Service

Microservice to persist and access the preprocessed data for the technical drawings.
It operates an application based on the Spring Boot Framework for REST resources, and a PostgreSQL database.

Please see the according [README](https://github.com/ScaDS/CoLIBRi/blob/main/database/README.md) for more details.

### Tools

**ToDo**

Please see the according [README](https://github.com/ScaDS/CoLIBRi/blob/main/tools/README.md) for more details.

### Example Data

**ToDo**

Please see the according [README](https://github.com/ScaDS/CoLIBRi/blob/main/example_data/README.md) for more details.

## Application Setup

The application and its microservices are managed within a [Docker Compose](https://docs.docker.com/compose/) stack,
defined by the file [docker-compose.yml](https://github.com/ScaDS/CoLIBRi/blob/main/docker-compose.yml).

### Basic System Requirements

* The application was built on and tested for linux/amd64 (x86-64) architectures
* Docker with Docker Compose available
* NVIDIA GPU which supports at least CUDA 11.8, with at least 10GB of VRAM
* The services use the following ports: 5201, 6201, 7201, 7211, 9201

### Docker Compose Setup

#### For configuration, two environment files are used:
* `.env`
  * Global configuration of CoLIBRi
  * See [`.env.sample`](https://github.com/ScaDS/CoLIBRi/blob/main/.env.sample) for details
* `conv-search/.env`
  * Configuration of models and LLM backend for conversational search
  * See [`conv-search/.env.sample`](https://github.com/ScaDS/CoLIBRi/blob/main/conv-search/.env.sample) for details

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