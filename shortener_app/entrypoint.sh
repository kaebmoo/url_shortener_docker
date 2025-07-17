#!/bin/sh
set -e

echo "SHORTENER_APP: Applying database migrations..."
alembic upgrade head

echo "SHORTENER_APP: Starting Gunicorn server..."
exec gunicorn -k uvicorn.workers.UvicornWorker --bind "0.0.0.0:${PORT:-8000}" main:app