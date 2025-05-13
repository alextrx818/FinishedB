#!/bin/bash
# run_pipeline.sh - Wrapper script for orchestrate_complete.py with flock locking
# 
# This script ensures only one instance runs at a time using flock
# and handles logging to the orchestrator.log file

# Change to script directory
cd "$(dirname "$0")"

# Path to lock file
LOCK_FILE="/tmp/sports_bot_orchestrator.lock"

# Path to log file
LOG_FILE="./orchestrator.log"

# Temporary file for collecting current run output
TEMP_LOG_FILE="/tmp/orchestrator_current_run.log"

# Function to format timestamp in MM/DD/YYYY hh:MM:SS AM/PM EDT format
formatted_timestamp() {
    # Use TZ environment variable to ensure Eastern time
    TZ="America/New_York" date "+%m/%d/%Y %I:%M:%S %p %Z"
}

# Function to prepend content to log file
prepend_to_log() {
    local content="$1"
    local log_file="$2"
    local header="\n===== $(formatted_timestamp) =====\n"
    
    # Add header to the content
    content="${header}${content}\n\n"
    
    if [ -f "$log_file" ]; then
        # Read existing content
        local old_content=$(cat "$log_file")
        # Write new content followed by old content
        echo -e "${content}${old_content}" > "$log_file"
    else
        # Create file with just the new content
        echo -e "$content" > "$log_file"
    fi
}

# Use flock to ensure only one instance runs
(
    # Try to acquire lock, fail immediately if not available
    flock -n 200 || { echo "$(formatted_timestamp) [ERROR] Another instance is running; exiting" >> "$LOG_FILE"; exit 1; }
    
    # Clean any existing temp log
    > "$TEMP_LOG_FILE"
    
    # Run the Python script, capturing all output to temp file
    ./sports_venv/bin/python ./orchestrate_complete.py >> "$TEMP_LOG_FILE" 2>&1
    
    # Now prepend the entire temp file to the main log file
    prepend_to_log "$(cat $TEMP_LOG_FILE)" "$LOG_FILE"
    
    # Clean up temp file
    rm -f "$TEMP_LOG_FILE"
    
) 200>"$LOCK_FILE"
