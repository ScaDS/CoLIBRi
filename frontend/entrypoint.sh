#!/bin/sh
exec conda run --no-capture-output -n frontend-env gunicorn \
  --bind "0.0.0.0:${APP_PORT}" \
  --timeout 600 \
  --chdir ./src/app \
  app:server \
  --log-level debug