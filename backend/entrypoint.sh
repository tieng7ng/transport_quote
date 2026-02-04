#!/bin/bash
set -e

echo "=== Transport Quote Backend ==="

echo "Running database migrations..."
alembic upgrade head

echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 3000
