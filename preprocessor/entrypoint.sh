#!/bin/sh
exec conda run --no-capture-output -n preprocessor-env gunicorn \
  --bind "0.0.0.0:${PP_PORT}" \
  --timeout 600 \
  --chdir ./src/flask \
  backend:app