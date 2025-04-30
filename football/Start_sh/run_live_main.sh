#!/bin/bash
# Script to run live.py with visible output in the terminal and logging to Main_Log.log

# Set the path to the project
PROJECT_DIR="/root/CascadeProjects/sports bot"
LOG_FILE="$PROJECT_DIR/football/logs/Main_Log.log"

# Ensure the log file exists but don't overwrite it
touch "$LOG_FILE"

# Add a separator to the log file to indicate a new session, but preserve previous content
echo "" >> "$LOG_FILE"
echo "=== Football Live Monitor Started at $(date) ===" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Ensure we're in the right directory
cd "$PROJECT_DIR" || exit 1

# Kill any existing live.py processes
pkill -f "live.py" 2>/dev/null || true

# Clear the screen for better visibility
clear

echo "Starting Football Live Monitor..."
echo "Output will be displayed below and logged to $LOG_FILE"
echo "==============================================="

# Set up a trap to log when the process is stopped
trap 'echo "" >> "$LOG_FILE"; echo "=== Football Live Monitor Stopped at $(date) ===" >> "$LOG_FILE"; echo "" >> "$LOG_FILE"' EXIT

# Run live.py with output going directly to screen and to log file
# without adding timestamps to each line
python3 football/live.py --continuous | tee -a "$LOG_FILE"
