# CoLIBRi Frontend

This directory contains the containerized code for the CoLIBRI frontend. In order to run properly, this service
assumes that all other micro-services are running (Conv-Search, Database, and Preprocessor).

## Project Tools

The following tools are used:
* [Python 3.11](https://www.python.org/downloads/release/python-3110/)
* [Dash](https://dash.plotly.com/)
* [OpenCV](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)
* [Scikit-Learn](https://scikit-learn.org/stable/)
* [pdf2image](https://pypi.org/project/pdf2image/)
* [gunicorn](https://gunicorn.org/)

## Repository Setup

* `Dockerfile`: Dockerfile to build the Docker image for the Frontend
* `entrypoint.sh`: Run on entry in the Docker Image
* `pyproject.toml`: Python configuration file for the Frontend
  * Defines Python version 
  * Defines environment
  * Settings for ruff and bandit

## Application Structure

The frontend itself is defined in `src/app/main.py`. Page contents are included in `src/app/pages/analyze.py`.
Helper code is included in `src/app/search_engine.py` and `src/app/technical_drawing.py`.

* `main.py`:
  * Defines pages, stylesheets (in `/assets/`) and URL prefixes
  * Runs the frontend

* `analyze.py`:
  * Defines site layout using HTML and dash components
  * Defines callbacks for user interaction
  * Defines data storage

* `search_engine.py`:
  * class `SeachEngine` contains:
    * custom CoLIBRi metric
      * splits incoming vectors into blocks
      * each block gets assigned a distance function
      * computes weighted sum of resulting distances
    * `__init__` builds a BallTree from a set of vectors
    * query function that uses a query vector to get the k nearest neighbors in the BallTree
  * Helper functions for splitting vectors and distance functions for individual blocks

* `technical_drawing.py`
  *  class `TechnicalDrawing` contains:
    * our internal representation for a technical drawing
    * helper methods for getting certain characteristics such as the smallest tolerance or the smallest GD&T
  * classes for `Surface`, `GeneralTolerance`, `GDT` and `Dimensioning` representations

## Build the Application

For the frontend to work in the intended way, all backend services (Conv-Search, Database, and Preprocessor) need to be running as well.
Make sure they are running or run the whole docker compose stack.

You may change the `FRONTEND_PATH` variable in `.env.sample` to fit to your needs. This defines the URL path prefix that Dash runs the application on.

### Python Environment

* Make sure you have [uv](https://docs.astral.sh/uv/guides/install-python/) installed!
* Generate a virtual environment using uv:
```
uv lock && uv sync --frozen --no-dev
```
* uv will use the defined packages in `pyproject.toml` to solve the environment and install necessary packages

### Running the service

After building the python environment using uv, you may use `uv run` to run any script in the virtual environment. Thus, run either
```
uv run ./src/app/main.py
```
for a development server, or
```
uv run gunicorn --bind "0.0.0.0:5201" --timeout 600 --chdir ./src/app main:server --log-level debug
```
for a production server. You may change the port in the --bind section to fit your needs.

### Build Service via Docker Compose as stand-alone
**Switch to the parent directory where the file `docker-compose.yml` is located.**

To build and run only the database and Spring application:
* `docker compose build frontend-app`, to build the service
* `docker compose up -d frontend-app` to start the frontend

To inspect the running containers:
* `docker compose ps -a`

To stop all running containers, remove the images and volumes:
* `docker compose down --rmi "all" -v`

### Build all Services via Docker Compose
`docker compose up -d` will run all microservices at once. This is the recommended way to run the frontend.