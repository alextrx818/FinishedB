#!/bin/bash
# Script to stop the log alerts scanner process

echo "Stopping Log Alerts Scanner..."

# Check if the PID file exists
if [ -f football/logs/log_alerts_pid.txt ]; then
    # Read the PID from the file
    LOGGER_PID=$(cat football/logs/log_alerts_pid.txt)
    
    # Check if the process is still running
    if ps -p $LOGGER_PID > /dev/null; then
        echo "Stopping log alerts process with PID: $LOGGER_PID"
        kill $LOGGER_PID
        echo "Log alerts scanner stopped."
    else
        echo "Log alerts process with PID $LOGGER_PID is not running."
    fi
    
    # Clean up the PID file
    rm football/logs/log_alerts_pid.txt
else
    echo "PID file not found. Looking for any log_alerts processes..."
    
    # Try to find the process by name
    FETCHER_PIDS=$(pgrep -f "python3.*run_log_alerts.py")
    
    if [ -n "$FETCHER_PIDS" ]; then
        echo "Found log alerts processes with PIDs: $FETCHER_PIDS"
        kill $FETCHER_PIDS
        echo "Log alerts processes stopped."
    else
        echo "No running log alerts processes found."
    fi
fi

echo "Done."
