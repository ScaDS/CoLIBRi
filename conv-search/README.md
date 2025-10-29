# CoLIBRi Conversational Search Microservice

This directory contains the containerized code for the _CoLIBRi_ conversational search microservice. 
Make sure to set the configuration values and credentials in the `.env` file (see below).

## Project Tools

The following tools are used:
* [Python 3.11](https://www.python.org/downloads/release/python-3110/)
* [gunicorn](https://gunicorn.org/)
* [Flask](https://flask.palletsprojects.com/en/stable/)
* [langchain](https://python.langchain.com/docs/introduction/)
* [llama-index](https://developers.llamaindex.ai/python/framework/)
* [ollama](https://github.com/ollama/ollama-python)

## Note on LLM inference and environment file

We assume that you have access to an LLM endpoint with OpenAI-compatible API to run this microservice, 
although some parts of the service may also work with a locally hosted Ollama instance.

Create a new `.env` file from `.env.sample`. Set your credentials for the LLM endpoint API and other values accordingly:
* `RETRIEVAL_METHOD`= { _REMOTE_, _LOCAL_ }: whether to run an embedding model locally (Huggingface on cpu) or send a request to the API
* `LOCAL_EMBED_MODEL`= { _huggingface_model_id_ }: get embedding of a query with this local model. We tried BAAI/bge-m3, but results were subpar
* `LLM_TYPE`= { _OLLAMA_, _REMOTE_ }: type of LLM to use.
  * _OLLAMA_: local LLM served via Ollama
  * _REMOTE_: LLM hosted at a remote endpoint
* if `LLM_TYPE`=_OLLAMA_
  * `OLLAMA_URL`= { ollama_host_url }
  * `OLLAMA_MODEL`= { ollama_model }
* if `LLM_TYPE`=_REMOTE_
  * `REMOTE_URL`= { remote_api_url }
  * `REMOTE_MODEL`= { remote_model }
  * `REMOTE_EMBED_MODEL`= { remote_embedding_model }
  * `REMOTE_API_KEY`= { remote_api_key }

## Application Setup

* `Dockerfile`: Dockerfile to build the Docker image for the conv-search
* `entrypoint.sh`: Starts gunicorn server and conv-search app in the Docker Image
* `pyproject.toml`: Python configuration file for used dependencies and tools
* `.env.sample`: copy, change name to `.env`, and change settings to run conv-search

## Application Structure

The endpoints for the Flask application are defined in `src/flask/backend.py`.  
All logic is handled by `src/flask/chatbot_logic.py`, which imports functions from `src/flask/search_engine.py`.

* `chatbot_logic.py` tools for generating tool_calls and executing them
* `search_engine.py` different search engines, one for local embeddings and one for remote embeddings
* Endpoints in `backend.py`:
  * `/retrieve`
    * uses `data["query"]`: query embedding to query the search engine
    * this is only for debugging and not really used during production
  * `/chatbot`: create a message describing the current retrieval results and the user message, send that to the LLM
    * uses `data["messages"]`: history of messages, OpenAI style
    * uses `data["technical_drawing_ids"]`: list of technical drawing ids currently displayed in the frontend (retrieval results)
    * when called
      * for the drawing ids, text is created describing an according technical drawing with its features
      * a tool_call is generated and executed using pydantic and llama_index, which is either
        * search_parts: user performs a new query with specific keywords
        * answer_question_about_previous_results: user asks a question in natural language about the current retrieval results
      * chatbot responds with a new message history and potentially new drawing ids

## Run the Application

For the conv-search to work in the intended way, the database service need to be up and running.  
To make sure, best start the whole docker compose stack like described in the project's [`README`](../README.md#docker-compose-setup).

### Run microservice via Docker Compose as stand-alone

**Switch to the parent directory where the file `docker-compose.yml` is located.**

To build and run the conv-search only:
* Build the service
  * `docker compose build convsearch-app`
* Start the conv-search without other dependent services
  * `docker compose up -d --no-deps convsearch-app`
* Inspect the running containers
  * `docker compose ps -a`
* See the logs for any errors
  * `docker compose logs -f convsearch-app`
* Stop all running containers, remove the images and volumes:
  * `docker compose down --rmi "all" -v`
