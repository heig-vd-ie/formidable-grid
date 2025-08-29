#!/usr/bin/env bash
set -euo pipefail

# Load environment variables from .envrc
if [ -f ".envrc" ]; then
  if command -v direnv >/dev/null 2>&1; then
    eval "$(direnv export bash)"
  else
    # fallback if .envrc just has `export VAR=...`
    # shellcheck disable=SC1091
    source .envrc
  fi
fi

SERVICE="$1"
CMD=""
PORT=""

# Define service -> port mapping (from your docker-compose or env vars)
case "$SERVICE" in
  backend-arras-api)
    PORT="${BACKEND_ARRAS_PORT:-4600}"   # default if not set
    CMD="poetry run uvicorn ${SERVICE}.main:app --host 0.0.0.0 --port ${PORT} --reload"
    ;;
  *)
    echo "❌ Unknown service: $SERVICE"
    exit 1
    ;;
esac

# Stop Docker container for this service (if running)
echo "🛑 Stopping docker service $SERVICE..."
docker compose stop "$SERVICE" >/dev/null 2>&1 || true

# Kill anything running on that port natively
make kill-port PORT=$PORT

# Run service natively
echo "🚀 Starting $SERVICE on port $PORT..."
exec $CMD
