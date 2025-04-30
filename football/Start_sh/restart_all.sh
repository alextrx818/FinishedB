#!/bin/bash
# Simple restart script for the football monitoring system

echo "Restarting Football Monitoring System..."

# Change to the project directory
cd "/root/CascadeProjects/sports bot"

# Stop any existing processes
echo "Stopping any existing processes..."
if [ -f football/running_pids.txt ]; then
  cat football/running_pids.txt | xargs kill 2>/dev/null || true
  echo "Existing processes stopped."
else
  echo "No PID file found. Checking for running processes..."
  pkill -f "football/live_monitor_wrapper.py" 2>/dev/null || true
  pkill -f "football/football_alerts.py" 2>/dev/null || true
fi

# Stop log fetcher and scanner if running
echo "Stopping log services..."
bash football/stop_daily_logging.sh 2>/dev/null || true
bash football/stop_log_alerts.sh 2>/dev/null || true

# Make sure processes are fully stopped before restarting
sleep 2

# Start everything again using the existing script
echo "Starting main monitoring services..."
bash football/start_24_7_monitoring.sh

# Start log fetcher and log scanner
echo "Starting log services..."
bash football/start_daily_logging.sh
bash football/start_log_alerts.sh

echo "
=============================================
All services restarted successfully!
 - Main monitoring (live.py)
 - Football alerts (Telegram)
 - Daily log fetcher
 - Log scanner alerts
=============================================
"
