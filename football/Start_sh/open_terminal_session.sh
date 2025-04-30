#!/bin/bash
# This script creates a new terminal session using tmux or screen
# that can be attached to at any time to view the live output

# Get the absolute path to the project directory
PROJECT_DIR="/root/CascadeProjects/sports bot"

# First try to stop any existing sessions
if command -v tmux &> /dev/null; then
    tmux kill-session -t football_monitor 2>/dev/null || true
elif command -v screen &> /dev/null; then
    screen -X -S football_monitor quit 2>/dev/null || true
fi

# Create a new session depending on what's available
if command -v tmux &> /dev/null; then
    echo "Creating a new tmux session for football monitor..."
    tmux new-session -d -s football_monitor "cd \"$PROJECT_DIR\" && bash football/run_live_monitor.sh"
    echo "
Session created!
To view the live output:
    tmux attach -t football_monitor

To detach from the session (leave it running):
    Press Ctrl+B then D
"
elif command -v screen &> /dev/null; then
    echo "Creating a new screen session for football monitor..."
    screen -dmS football_monitor bash -c "cd \"$PROJECT_DIR\" && bash football/run_live_monitor.sh"
    echo "
Session created!
To view the live output:
    screen -r football_monitor

To detach from the session (leave it running):
    Press Ctrl+A then D
"
else
    echo "Neither tmux nor screen are available. Please install one of them to use this feature."
    exit 1
fi
