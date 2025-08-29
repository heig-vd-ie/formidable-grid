#!/usr/bin/env bash
set -euo pipefail

# Load environment variables
if [ -f ".envrc" ]; then
  if command -v direnv >/dev/null 2>&1; then
    eval "$(direnv export bash)"
  else
    # Fallback if .envrc just has simple exports
    source .envrc
  fi
fi

# Services
NATIVE_SERVICES="${NATIVE_SERVICES:-backend-arras-api}"
ALL_SERVICES="$(docker compose config --services)"
ONLY_DOCKER_SERVICES="$(comm -23 <(echo "$ALL_SERVICES" | sort) <(echo "$NATIVE_SERVICES" | tr ' ' '\n' | sort))"

SESSION="dev_session"
if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "🛑 Killing existing tmux session: $SESSION"
    tmux kill-session -t "$SESSION"
fi

echo "🟢 Starting tmux session: $SESSION"

# Create new tmux session detached
tmux new-session -d -s "$SESSION" -n "native"

# Launch each native service in its own tmux window
for svc in $NATIVE_SERVICES; do
  echo "🚀 Launching native service: $svc"
  tmux new-window -t "$SESSION" -n "$svc" "./scripts/run-native.sh $svc"
done

# Build Docker images
echo "🔨 Building Docker images..."
docker compose build

# Launch Docker services in a separate tmux window
tmux new-window -t "$SESSION" -n "docker" bash -c "for svc in $ONLY_DOCKER_SERVICES; do \
    echo 'Starting Docker service: '$svc; \
    docker compose up -d \$svc; \
done; echo 'All docker services started';docker compose logs -f; exec bash"

echo "✅ All services are started. Attach with:"
echo "   tmux attach -t $SESSION"
