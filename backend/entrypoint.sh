#!/bin/bash
set -euo pipefail

# ─────────────────────────────────────────────
# Dormtel App - Entrypoint Script
# Runs Alembic migrations then starts uvicorn
# ─────────────────────────────────────────────

cd /app

# Wait for database to be resolvable and ready
MAX_RETRIES=30
RETRY_DELAY=2

for i in $(seq 1 $MAX_RETRIES); do
  if python -c "import socket; socket.gethostbyname('db')" >/dev/null 2>&1; then
    echo "Database host 'db' is resolvable."
    break
  fi
  echo "Waiting for database host 'db' to be resolvable... ($i/$MAX_RETRIES)"
  sleep $RETRY_DELAY
done

echo "Running database migrations..."
python -m alembic upgrade head

echo "Starting Dormtel API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
