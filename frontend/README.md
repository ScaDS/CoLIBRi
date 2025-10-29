# CoLIBRi Frontend

This directory contains the containerized code for the _CoLIBRi_ frontend. In order to operate properly, this service
needs all other microservices running (Preprocessor, Conv-Search, and Database).

## Project Tools

The following tools are used:
* [Python 3.11](https://www.python.org/downloads/release/python-3110/)
* [Dash](https://dash.plotly.com/)
* [OpenCV](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)
* [Scikit-Learn](https://scikit-learn.org/stable/)
* [pdf2image](https://pypi.org/project/pdf2image/)
* [gunicorn](https://gunicorn.org/)

## Application Setup

* `Dockerfile`: Dockerfile to build the Docker image for the Frontend
* `entrypoint.sh`: Starts gunicorn server and frontend app in the Docker Image
* `pyproject.toml`: Python configuration file for used dependencies and tools

## Application Structure

The frontend itself is defined in `src/app/main.py`.  
Page contents are included in `src/app/pages/analyze.py`.  
Helper code is provided in `src/app/search_engine.py`, `src/app/technical_drawing.py`, and `src/app/utils.py`.

* `main.py`:
  * Defines pages, stylesheets (in `/assets/`) and URL prefixes
  * Runs the frontend

* `analyze.py`:
  * Defines page layout with HTML and dash components
  * Defines callbacks for user interaction, and data storage

* `search_engine.py`:
  * Defines BallTree index and custom _CoLIBRi_ distance metric
  * Query function for retrieving the k nearest neighbors of a vector from the BallTree index

* `technical_drawing.py`
  * Internal representation and helper methods for a technical drawing
  * Representations for `Surface`, `GeneralTolerance`, `GDT`, and `Dimensioning`

## Run the Application

For the frontend to work in the intended way, all other services (Preprocessor, Conv-Search, and Database) need to be up and running.  
To make sure, best start the whole docker compose stack like described in the project's [`README`](../README.md#docker-compose-setup).

You can change the `FRONTEND_PATH` variable in the project's `.env` to suit your needs.
This defines the URL path prefix under which Dash runs the application, e.g. `http://host.de/colibri`

### Run microservice via Docker Compose as stand-alone

**Switch to the parent directory where the file `docker-compose.yml` is located.**

To build and run the frontend only:
* Build the service
  * `docker compose build frontend-app`
* Start the frontend without other dependent services
  * `docker compose up -d --no-deps frontend-app`
* Inspect the running containers
  * `docker compose ps -a`
* See the logs for any errors
  * `docker compose logs -f frontend-app`
* Stop all running containers, remove the images and volumes:
  * `docker compose down --rmi "all" -v`
