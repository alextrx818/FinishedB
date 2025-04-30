#!/bin/bash
# Script to stop the daily log fetcher process

echo "Stopping Daily Log Fetcher..."

# Check if the PID file exists
if [ -f football/logs/logger_pid.txt ]; then
    # Read the PID from the file
    LOGGER_PID=$(cat football/logs/logger_pid.txt)
    
    # Check if the process is still running
    if ps -p $LOGGER_PID > /dev/null; then
        echo "Stopping logger process with PID: $LOGGER_PID"
        kill $LOGGER_PID
        echo "Logger stopped."
    else
        echo "Logger process with PID $LOGGER_PID is not running."
    fi
    
    # Clean up the PID file
    rm football/logs/logger_pid.txt
else
    echo "PID file not found. Looking for any daily_log_fetcher.py processes..."
    
    # Try to find the process by name
    FETCHER_PIDS=$(pgrep -f "python3.*daily_log_fetcher.py")
    
    if [ -n "$FETCHER_PIDS" ]; then
        echo "Found logger processes with PIDs: $FETCHER_PIDS"
        kill $FETCHER_PIDS
        echo "Logger processes stopped."
    else
        echo "No running logger processes found."
    fi
fi

echo "Done."
