#!/bin/bash
# Script to start the log alerts scanner in the background

echo "Starting Log Alerts Scanner in the background..."
echo "Press Ctrl+C to stop"
echo "Started at: $(date)"
echo "========================================"

# Change to the project directory
cd "/root/CascadeProjects/sports bot"

# Create logs directory if it doesn't exist
mkdir -p football/logs

# Run the log alerts scanner in the background
nohup python3 football/run_log_alerts.py --continuous --interval 60 > football/logs/log_alerts_process.log 2>&1 &
LOGGER_PID=$!

echo "Log Alerts Scanner started with PID: $LOGGER_PID"
echo "Process logs: football/logs/log_alerts_process.log"

# Save the PID to a file for easy reference later
echo "$LOGGER_PID" > football/logs/log_alerts_pid.txt
echo "PID saved to football/logs/log_alerts_pid.txt"

echo ""
echo "To stop the log alerts scanner:"
echo "  kill $LOGGER_PID"
echo ""
echo "To check for alerts:"
echo "  cat football/logs/log_alerts.log"
