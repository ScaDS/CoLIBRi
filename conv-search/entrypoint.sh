#!/bin/sh
exec conda run --no-capture-output -n cpt_ms-conv-search-env gunicorn \
  --bind "0.0.0.0:${CS_PORT}" \
  --timeout 600 \
  --chdir ./src/flask \
  backend:app