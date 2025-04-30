#!/bin/bash
# Script to start the daily log fetcher in the background

echo "Starting Daily Log Fetcher in the background..."
echo "Press Ctrl+C to stop"
echo "Started at: $(date)"
echo "========================================"

# Change to the project directory
cd "/root/CascadeProjects/sports bot"

# Create logs directory if it doesn't exist
mkdir -p football/logs

# Run the daily log fetcher in the background
nohup python3 football/daily_log_fetcher.py --interval 30 > football/logs/fetcher_process.log 2>&1 &
LOGGER_PID=$!

echo "Daily Log Fetcher started with PID: $LOGGER_PID"
echo "Process logs: football/logs/fetcher_process.log"
echo "Fetch logs directory: football/logs/"

# Save the PID to a file for easy reference later
echo "$LOGGER_PID" > football/logs/logger_pid.txt
echo "PID saved to football/logs/logger_pid.txt"

echo ""
echo "To stop the logger:"
echo "  kill $LOGGER_PID"
echo ""
echo "To view today's logs:"
echo "  cat football/logs/football_fetches_$(date +%Y-%m-%d).log"
echo ""
echo "For end-of-day review, use the log viewer tool:"
echo "  python3 football/view_daily_logs.py"
