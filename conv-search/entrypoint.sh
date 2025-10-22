#!/bin/sh
exec uv run gunicorn \
  --bind "0.0.0.0:9201" \
  --timeout 600 \
  --chdir ./src/flask \
  backend:app