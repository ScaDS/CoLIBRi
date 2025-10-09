FROM continuumio/miniconda3:latest

ARG CS_PORT

WORKDIR /app/
COPY env_conv_search.yml ./
COPY entrypoint.sh ./
COPY .env ./
RUN chmod +x /app/entrypoint.sh
COPY ./src ./src

# expose port CS_PORT to access it from outside of the container
EXPOSE ${CS_PORT}
# Make PP_PORT available at runtime
ENV CS_PORT=${CS_PORT}
ENV PYTHONPATH=/app/

# Create the environment with conda
RUN conda env create -f /app/env_conv_search.yml

# There is a bug in the LlamaIndex Ollama library, which is whywe have to replace this file with the fixed version
# We should remove this once we upgrade to a newer version of Ollama
COPY fixed_ollama_base.py /opt/conda/envs/conv-search-env/cpt_ms-cpt_ms-conv-search-env-env/lib/python3.1/site-packages/llama_index/multi_modal_llms/ollama/base.py

ENV LD_LIBRARY_PATH=/opt/conda/envs/conv-search-env/cpt_ms-cpt_ms-conv-search-env-env/lib/
ENV PYTHONUNBUFFERED=1

# run the gunicorn server at entry
ENTRYPOINT ["/app/entrypoint.sh"]