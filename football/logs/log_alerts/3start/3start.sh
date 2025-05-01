#!/bin/bash
#
# 3start.sh - Control script for the 3start line monitor
#
# This script provides commands to start, stop, restart, and check the status
# of the 3start line monitor that watches for betting lines with values of 3.0+.

# Define paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
START3_SCRIPT="$SCRIPT_DIR/3start_monitor.py"
MATCHES_LOG="$SCRIPT_DIR/3start_matches.log"
STATUS_LOG="$SCRIPT_DIR/3start_status.log"
OUTPUT_LOG="$SCRIPT_DIR/3start_output.log"
PID_FILE="$SCRIPT_DIR/3start_pid.txt"

# Ensure the script has executable permissions
chmod +x "$START3_SCRIPT" 2>/dev/null

# Check if the monitor script exists
if [ ! -f "$START3_SCRIPT" ]; then
    echo "Error: 3start_monitor.py not found at $START3_SCRIPT"
    exit 1
fi

# Function to start the monitor
start_monitor() {
    echo "Starting 3start monitor..."
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "3start monitor is already running with PID: $PID"
            return
        else
            echo "Removing stale PID file..."
            rm -f "$PID_FILE"
        fi
    fi
    
    # Start the monitor in the background and redirect all output
    python3 "$START3_SCRIPT" > "$OUTPUT_LOG" 2>&1 &
    PID=$!
    
    # Save the PID
    echo $PID > "$PID_FILE"
    echo "3start monitor started with PID: $PID"
    
    # Create empty log files if they don't exist
    touch "$MATCHES_LOG" "$STATUS_LOG"
    
    echo "Monitor is running in the background."
    echo "- Use '$0 status' to check its status"
    echo "- Use '$0 view-matches' to see detected matches"
    echo "- Use '$0 view-log' to see the monitor's output"
}

# Function to stop the monitor
stop_monitor() {
    echo "Stopping 3start monitor..."
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            kill "$PID"
            sleep 1
            if ps -p "$PID" > /dev/null 2>&1; then
                echo "Monitor did not stop gracefully, forcing..."
                kill -9 "$PID" 2>/dev/null
            fi
            rm -f "$PID_FILE"
            echo "3start monitor stopped."
        else
            echo "No active monitor process found."
            rm -f "$PID_FILE"
        fi
    else
        echo "No PID file found. Monitor may not be running."
    fi
}

# Function to check the status
check_status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "3start monitor is RUNNING with PID: $PID"
            echo "-----------------------------------------"
            echo "Recent status log entries:"
            tail -n 5 "$STATUS_LOG" 2>/dev/null || echo "No status log entries yet."
            echo "-----------------------------------------"
            echo "Recent matches detected:"
            tail -n 10 "$MATCHES_LOG" 2>/dev/null || echo "No matches detected yet."
            echo "-----------------------------------------"
            echo "Use '$0 view-matches' for full match log"
            echo "Use '$0 view-log' for full monitor output"
        else
            echo "3start monitor is NOT RUNNING (stale PID file)"
        fi
    else
        echo "3start monitor is NOT RUNNING"
    fi
}

# View matches log
view_matches() {
    if [ -f "$MATCHES_LOG" ]; then
        echo "=== 3START MATCHES LOG ==="
        cat "$MATCHES_LOG"
    else
        echo "Matches log not found: $MATCHES_LOG"
    fi
}

# View status/output log
view_log() {
    if [ -f "$OUTPUT_LOG" ]; then
        echo "=== 3START OUTPUT LOG ==="
        cat "$OUTPUT_LOG"
    else
        echo "Output log not found: $OUTPUT_LOG"
    fi
}

# Force a full rescan
force_rescan() {
    echo "Forcing a full rescan (deleting offset file)..."
    OFFSET_FILE="$SCRIPT_DIR/3start_offset.txt"
    
    # First stop the monitor if it's running
    stop_monitor
    
    # Remove the offset file
    if [ -f "$OFFSET_FILE" ]; then
        rm -f "$OFFSET_FILE"
        echo "Offset file removed. Will rescan from the beginning of Main_Log.log."
    else
        echo "No offset file found. Will rescan from the beginning of Main_Log.log."
    fi
    
    # Restart the monitor
    start_monitor
    
    echo "Full rescan initiated."
}

# Main script logic
case "$1" in
    start)
        start_monitor
        ;;
    stop)
        stop_monitor
        ;;
    restart)
        stop_monitor
        sleep 1
        start_monitor
        ;;
    status)
        check_status
        ;;
    view-matches)
        view_matches
        ;;
    view-log)
        view_log
        ;;
    force-rescan)
        force_rescan
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|view-matches|view-log|force-rescan}"
        echo ""
        echo "Commands:"
        echo "  start        - Start the 3start monitor"
        echo "  stop         - Stop the 3start monitor"
        echo "  restart      - Restart the 3start monitor"
        echo "  status       - Check the status of the 3start monitor"
        echo "  view-matches - View detected matches with 3+ line values"
        echo "  view-log     - View the monitor's output log"
        echo "  force-rescan - Force a complete rescan of Main_Log.log"
        exit 1
        ;;
esac

exit 0
