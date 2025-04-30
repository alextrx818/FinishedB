#!/bin/bash
# Script to display live monitor output and log it to the main logger file

# Get the absolute path to the project directory
PROJECT_DIR="/root/CascadeProjects/sports bot"
LOG_FILE="$PROJECT_DIR/football/main_logger.log"

# Create or clear the log file
echo "=== Football Live Monitor Started at $(date) ===" > "$LOG_FILE"

# Timestamp function for logging
add_timestamp() {
  while IFS= read -r line; do
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $line"
  done
}

# Check if we're running in background mode
if [[ "$1" == "--background" ]]; then
  # In background mode, just log to the file silently
  cd "$PROJECT_DIR"
  python3 football/live_monitor_wrapper.py 6128359776 30 | add_timestamp >> "$LOG_FILE" 2>&1
else
  # In foreground mode, display to stdout and log
  cd "$PROJECT_DIR"
  # Use tee to display output and log simultaneously
  python3 football/live_monitor_wrapper.py 6128359776 30 | add_timestamp | tee -a "$LOG_FILE"
fi
