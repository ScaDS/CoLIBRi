#!/bin/sh
exec uv run gunicorn \
  --bind "0.0.0.0:5201" \
  --timeout 600 \
  --chdir ./src/app \
  main:server \
  --log-level debug