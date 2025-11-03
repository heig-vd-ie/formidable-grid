#!/bin/bash

SESSION_NAME=${1:-"formidable-dev"}
PROJECT_DIR=$(pwd)

tmux kill-session -t "$SESSION_NAME" 2>/dev/null

tmux new-session -d -s "$SESSION_NAME" -c "$PROJECT_DIR"

# Split window into 2 horizontal panes
tmux split-window -h -t "$SESSION_NAME:0"

tmux select-layout -t "$SESSION_NAME:0" even-vertical

# Pane 0: 
tmux send-keys -t "$SESSION_NAME:0.0" "source .envrc && make build _start logs" C-m

# Focus on the which pane
tmux select-pane -t "$SESSION_NAME:0.1"

# Set titles
titles=(
  "Servers"
  "Terminal"
)

# Loop through titles and assign each to a pane
for i in "${!titles[@]}"; do
    tmux select-pane -t "${SESSION_NAME}:0.${i}" -T "${titles[$i]}"
done

# Attach to the session
tmux attach-session -t "$SESSION_NAME"
