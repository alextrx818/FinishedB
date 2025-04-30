#!/bin/bash
# Script to run the live monitor wrapper in continuous mode

echo "Starting Football Live Monitor with Telegram notifications..."
echo "Press Ctrl+C to stop"
echo "Started at: $(date)"
echo "========================================"

# Run the wrapper script which will send Telegram notifications and then run live.py
cd "/root/CascadeProjects/sports bot"

# Use the terminal display wrapper instead of running directly
# Pass --background flag when being called from start_24_7_monitoring.sh
if [[ "$1" == "--background" ]]; then
  bash football/terminal_display_wrapper.sh --background
else
  bash football/terminal_display_wrapper.sh
fi
