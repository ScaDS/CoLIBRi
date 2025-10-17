#!/bin/sh
exec gunicorn \
  --bind "0.0.0.0:6201" \
  --timeout 600 \
  --chdir ./src/flask \
  backend:app