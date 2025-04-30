#!/bin/bash
# Script to run live.py with visible output in the terminal and logging

# Set the path to the project
PROJECT_DIR="/root/CascadeProjects/sports bot"
LOG_FILE="$PROJECT_DIR/football/main_logger.log"

# Clear old log and start new one
echo "=== Football Live Monitor Started at $(date) ===" > "$LOG_FILE"

# Ensure we're in the right directory
cd "$PROJECT_DIR" || exit 1

# Timestamp function for logging only
add_timestamp() {
  while IFS= read -r line; do
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $line"
  done
}

# Kill any existing live.py processes
pkill -f "live.py" 2>/dev/null || true

# Clear the screen for better visibility
clear

echo "Starting Football Live Monitor..."
echo "Output will be displayed below and logged to $LOG_FILE"
echo "==============================================="

# Run live.py with the output going to two places:
# 1. Directly to the screen (without timestamps)
# 2. To the log file (with timestamps)
python3 football/live.py --continuous | tee >(add_timestamp > "$LOG_FILE")
