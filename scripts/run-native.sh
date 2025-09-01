#!/usr/bin/env bash
set -euo pipefail

# Load environment variables from .envrc
if [ -f ".envrc" ]; then
  if command -v direnv >/dev/null 2>&1; then
    eval "$(direnv export bash)"
  else
    source .envrc
  fi
fi

SERVICE="$1"
PORT=""

case "$SERVICE" in
  backend-arras-api)
    PORT="${BACKEND_ARRAS_PORT:-4600}"  # default port
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

# Run service natively using Poetry
echo "🚀 Starting $SERVICE on port $PORT..."
uvicorn backend-arras-api.main:app --reload --port "$PORT"
