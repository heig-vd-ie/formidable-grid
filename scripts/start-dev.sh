#!/bin/bash

SESSION_NAME=${1:-"formidable-dev"}
PROJECT_DIR="/home/myi/projects/formidable-grid"

tmux kill-session -t "$SESSION_NAME" 2>/dev/null

tmux new-session -d -s "$SESSION_NAME" -c "$PROJECT_DIR"

# Split window into 3 horizontal panes
tmux split-window -h -t "$SESSION_NAME:0"
tmux split-window -h -t "$SESSION_NAME:0.1"

tmux select-layout -t "$SESSION_NAME:0" even-vertical

# Pane 0: 
tmux send-keys -t "$SESSION_NAME:0.0" "source .envrc && make start && docker exec -it gridlabd sh" C-m

# Pane 1:
tmux send-keys -t "$SESSION_NAME:0.1" "source .envrc && cd frontend && npm run dev" C-m

# Pane 2:
tmux send-keys -t "$SESSION_NAME:0.2" "source .envrc &&cd frontend && npm run api" C-m

# Focus on the which pane
tmux select-pane -t "$SESSION_NAME:0.0"

# Attach to the session
tmux attach-session -t "$SESSION_NAME"
