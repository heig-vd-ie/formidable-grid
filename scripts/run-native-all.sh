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

# Services
NATIVE_SERVICES="${NATIVE_SERVICES:-backend-arras-api}"
ALL_SERVICES="$(docker compose config --services)"
ONLY_DOCKER_SERVICES="$(comm -23 <(echo "$ALL_SERVICES" | sort) <(echo "$NATIVE_SERVICES" | tr ' ' '\n' | sort))"

SESSION="dev_session"

# Kill existing tmux session if present
if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "🛑 Killing existing tmux session: $SESSION"
    tmux kill-session -t "$SESSION"
fi

echo "🟢 Starting tmux session: $SESSION"

# Create new tmux session detached
tmux new-session -d -s "$SESSION" -n "services"

# Get the full path to the Poetry virtualenv Python
VENV_PYTHON="$(poetry env info --path)/bin/python"
if [ ! -x "$VENV_PYTHON" ]; then
    echo "❌ Could not find Poetry virtualenv Python at $VENV_PYTHON"
    exit 1
fi

# Debug: check python-multipart inside the virtualenv
"$VENV_PYTHON" -m pip show python-multipart || echo "⚠️ python-multipart not found in Poetry env"

# Launch native services in panes
first_service=1
for svc in $NATIVE_SERVICES; do
    # Ensure we're in the right directory and use the correct Poetry environment
    CMD="bash -l -c 'cd $(pwd) && export VIRTUAL_ENV=\"$(poetry env info --path)\" && export PATH=\"\$VIRTUAL_ENV/bin:\$PATH\" && ./scripts/run-native.sh $svc'"
    if [ "$first_service" -eq 1 ]; then
        # First pane uses initial pane
        tmux send-keys -t "$SESSION":services "$CMD" C-m
        first_service=0
    else
        # Split new pane for subsequent services
        tmux split-window -t "$SESSION":services -v "$CMD"
        tmux select-layout -t "$SESSION":services tiled
    fi
done

# Launch Docker services in additional panes
for svc in $ONLY_DOCKER_SERVICES; do
    CMD="bash -l -c 'docker compose up $svc'"
    tmux split-window -t "$SESSION":services -v "$CMD"
    tmux select-layout -t "$SESSION":services tiled
done

echo "✅ All services started in tmux panes."
echo "   Attach with: tmux attach -t $SESSION"
